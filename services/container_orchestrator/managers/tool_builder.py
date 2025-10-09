"""
==============================================================================
TOOL BUILDER - Auto-generate Docker images from tool manifests
==============================================================================
Generates Dockerfiles and builds images from tool manifest specifications.
==============================================================================
"""

import docker
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ToolBuilder:
    """Auto-generates and builds Docker images from tool manifests."""
    
    # Base image mapping for runtimes
    RUNTIME_IMAGES = {
        "python3": "python:3.11-slim",
        "python": "python:3.11-slim",
        "node": "node:20-slim",
        "nodejs": "node:20-slim",
        "go": "golang:1.21-alpine",
        "bash": "bash:5.2-alpine",
        "shell": "bash:5.2-alpine",
    }
    
    def __init__(self):
        self.client = docker.from_env()
        logger.info("🔨 Tool builder initialized")
    
    def generate_dockerfile(
        self,
        runtime: str,
        entrypoint: str,
        build_config: Dict[str, Any],
        health_check: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate Dockerfile content from manifest specs."""
        
        base_image = self.RUNTIME_IMAGES.get(runtime.lower(), runtime)
        
        dockerfile_lines = [
            f"FROM {base_image}",
            "",
            "WORKDIR /tool",
            ""
        ]
        
        # Handle build engine (pip, npm, go mod, etc.)
        build_engine = build_config.get("engine", "").lower()
        requirements_file = build_config.get("requirements_file", "")
        
        if build_engine == "pip" and requirements_file:
            dockerfile_lines.extend([
                f"COPY {requirements_file} .",
                "RUN pip install --no-cache-dir -r requirements.txt",
                ""
            ])
        elif build_engine == "npm" and requirements_file:
            dockerfile_lines.extend([
                "COPY package.json package-lock.json* ./",
                "RUN npm ci --only=production",
                ""
            ])
        elif build_engine == "go":
            dockerfile_lines.extend([
                "COPY go.mod go.sum* ./",
                "RUN go mod download",
                ""
            ])
        
        # Copy tool files
        # Extract directory from entrypoint
        entrypoint_dir = str(Path(entrypoint).parent)
        if entrypoint_dir and entrypoint_dir != '.':
            dockerfile_lines.append(f"COPY {entrypoint_dir}/ ./{entrypoint_dir}/")
        else:
            dockerfile_lines.append("COPY . .")
        
        dockerfile_lines.append("")
        
        # Make entrypoint executable
        dockerfile_lines.extend([
            f"RUN chmod +x {entrypoint}",
            ""
        ])
        
        # Add health check if specified
        if health_check and health_check.get("type") == "script":
            cmd = health_check.get("command", "")
            dockerfile_lines.extend([
                f'HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \\',
                f'  CMD {cmd} || exit 1',
                ""
            ])
        
        # Set entrypoint based on runtime
        if runtime.lower() in ["python3", "python"]:
            dockerfile_lines.append(f'ENTRYPOINT ["python3", "{entrypoint}"]')
        elif runtime.lower() in ["node", "nodejs"]:
            dockerfile_lines.append(f'ENTRYPOINT ["node", "{entrypoint}"]')
        elif runtime.lower() in ["bash", "shell"]:
            dockerfile_lines.append(f'ENTRYPOINT ["bash", "{entrypoint}"]')
        elif runtime.lower() == "go":
            # For Go, build and run the binary
            dockerfile_lines[-1] = "RUN go build -o /tool/app ."
            dockerfile_lines.append('ENTRYPOINT ["/tool/app"]')
        else:
            dockerfile_lines.append(f'ENTRYPOINT ["{entrypoint}"]')
        
        return "\n".join(dockerfile_lines)
    
    def build_tool_image(
        self,
        tool_name: str,
        tool_path: Path,
        manifest: Dict[str, Any],
        force_rebuild: bool = False
    ) -> str:
        """Build Docker image for a tool from its manifest."""
        
        image_tag = f"cortex/tool-{tool_name}:latest"
        
        # Check if image already exists
        if not force_rebuild:
            try:
                self.client.images.get(image_tag)
                logger.info(f"✅ Image already exists: {image_tag}")
                return image_tag
            except docker.errors.ImageNotFound:
                pass
        
        implementation = manifest.get("implementation", {})
        runtime = implementation.get("runtime", "python3")
        entrypoint = implementation.get("entrypoint", "./main.py")
        build_config = implementation.get("build", {})
        health_check = manifest.get("health_check")
        
        # Generate Dockerfile
        dockerfile_content = self.generate_dockerfile(
            runtime=runtime,
            entrypoint=entrypoint,
            build_config=build_config,
            health_check=health_check
        )
        
        logger.debug(f"Generated Dockerfile for {tool_name}:\n{dockerfile_content}")
        
        # Create temporary build context
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Write Dockerfile
            dockerfile_path = tmppath / "Dockerfile"
            dockerfile_path.write_text(dockerfile_content)
            
            # Copy tool files to build context
            # Copy everything from tool directory except Dockerfile if it exists
            for item in tool_path.iterdir():
                if item.name == "Dockerfile":
                    continue
                if item.is_file():
                    shutil.copy2(item, tmppath / item.name)
                elif item.is_dir():
                    shutil.copytree(item, tmppath / item.name, dirs_exist_ok=True)
            
            # Build image
            logger.info(f"🔨 Building image: {image_tag}")
            
            try:
                image, build_logs = self.client.images.build(
                    path=str(tmppath),
                    tag=image_tag,
                    rm=True,
                    forcerm=True
                )
                
                # Log build output
                for log in build_logs:
                    if 'stream' in log:
                        msg = log['stream'].strip()
                        if msg:
                            logger.debug(f"  {msg}")
                    elif 'error' in log:
                        logger.error(f"Build error: {log['error']}")
                
                logger.info(f"✅ Built image: {image_tag}")
                return image_tag
                
            except docker.errors.BuildError as e:
                logger.error(f"Failed to build image {image_tag}: {e}")
                raise
    
    def ensure_tool_image(
        self,
        tool_name: str,
        manifest_registry
    ) -> str:
        """Ensure tool image exists, building if necessary."""
        
        image_tag = f"cortex/tool-{tool_name}:latest"
        
        # Try to get existing image
        try:
            self.client.images.get(image_tag)
            return image_tag
        except docker.errors.ImageNotFound:
            pass
        
        # Need to build - fetch manifest and tool path
        logger.info(f"Image not found, building: {image_tag}")
        
        # This would integrate with manifest_ingestion service
        # For now, we'll look in standard locations
        from pathlib import Path
        
        tool_base = Path("/app/manifests/tools")
        tool_path = tool_base / tool_name
        
        if not tool_path.exists():
            # Try alternative location
            tool_path = Path(f"/home/mlamkadm/repos/Cortex-Prime-MK1/manifests/tools/{tool_name}")
        
        if not tool_path.exists():
            raise ValueError(f"Tool path not found: {tool_name}")
        
        # Load manifest
        manifest_file = tool_path / "tool.yml"
        if not manifest_file.exists():
            raise ValueError(f"Tool manifest not found: {manifest_file}")
        
        import yaml
        manifest = yaml.safe_load(manifest_file.read_text())
        
        return self.build_tool_image(tool_name, tool_path, manifest)
