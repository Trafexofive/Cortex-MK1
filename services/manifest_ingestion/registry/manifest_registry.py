"""
==============================================================================
MANIFEST REGISTRY SERVICE v1.0
==============================================================================
Central registry for managing all Cortex-Prime manifests.
Provides dependency resolution, validation, and lifecycle management.
==============================================================================
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from loguru import logger

from models.manifest_models import (
    ManifestRegistry, 
    ManifestValidationResponse,
    ManifestKind,
    ManifestUnion,
    AgentManifest,
    ToolManifest,
    RelicManifest,
    WorkflowManifest,
    create_manifest_from_dict
)
from parsers.manifest_parser import ManifestParser, ManifestParsingError


class ManifestRegistryService:
    """
    Central service for manifest registration, validation, and dependency management.
    
    Philosophy:
    - Sovereignty: Each manifest is a complete, autonomous specification
    - Dependency Resolution: Automatic validation of inter-manifest dependencies  
    - Lifecycle Management: Track manifest state and evolution
    - Performance: In-memory registry with optional persistence
    """
    
    def __init__(self, manifests_root: Optional[Path] = None):
        self.registry = ManifestRegistry()
        self.parser = ManifestParser()
        
        # Default to project manifests directory
        if manifests_root is None:
            manifests_root = Path(__file__).parent.parent.parent.parent / "manifests"
        
        self.manifests_root = Path(manifests_root)
        logger.info(f"Manifest registry initialized with root: {self.manifests_root}")
    
    # ========================================================================
    # CORE REGISTRY OPERATIONS
    # ========================================================================
    
    async def register_manifest(self, data: Dict[str, Any]) -> ManifestValidationResponse:
        """
        Register a new manifest in the registry.
        
        Args:
            data: Parsed manifest dictionary
            
        Returns:
            Validation response with registration status
        """
        try:
            # Validate structure
            is_valid, structure_errors = await self.parser.validate_manifest_structure(data)
            
            if not is_valid:
                return ManifestValidationResponse(
                    valid=False,
                    errors=structure_errors
                )
            
            # Create typed manifest
            typed_manifest = await self.parser.create_typed_manifest(data)
            
            # Validate dependencies
            deps_valid, missing_deps = await self._validate_dependencies_internal(data)
            
            # Store in appropriate registry section
            kind = typed_manifest.kind
            name = typed_manifest.name
            
            if kind == ManifestKind.AGENT:
                self.registry.agents[name] = typed_manifest
            elif kind == ManifestKind.TOOL:
                self.registry.tools[name] = typed_manifest
            elif kind == ManifestKind.RELIC:
                self.registry.relics[name] = typed_manifest
            elif kind == ManifestKind.WORKFLOW:
                self.registry.workflows[name] = typed_manifest
            
            # Update registry stats
            self.registry.update_stats()
            
            logger.info(f"Successfully registered {kind} manifest: {name}")
            
            return ManifestValidationResponse(
                valid=True,
                dependencies_satisfied=deps_valid,
                missing_dependencies=missing_deps
            )
            
        except Exception as e:
            logger.error(f"Failed to register manifest: {str(e)}")
            return ManifestValidationResponse(
                valid=False,
                errors=[str(e)]
            )
    
    async def get_manifest(self, kind: str, name: str) -> Optional[ManifestUnion]:
        """Get a specific manifest by kind and name"""
        kind_enum = ManifestKind(kind) if isinstance(kind, str) else kind
        
        registry_map = {
            ManifestKind.AGENT: self.registry.agents,
            ManifestKind.TOOL: self.registry.tools,
            ManifestKind.RELIC: self.registry.relics,
            ManifestKind.WORKFLOW: self.registry.workflows
        }
        
        return registry_map.get(kind_enum, {}).get(name)
    
    async def list_manifests(self, kind: Optional[str] = None) -> Dict[str, List[str]]:
        """List all manifests, optionally filtered by kind"""
        if kind:
            kind_enum = ManifestKind(kind)
            registry_map = {
                ManifestKind.AGENT: self.registry.agents,
                ManifestKind.TOOL: self.registry.tools,
                ManifestKind.RELIC: self.registry.relics,
                ManifestKind.WORKFLOW: self.registry.workflows
            }
            
            return {kind: list(registry_map[kind_enum].keys())}
        
        return {
            "agents": list(self.registry.agents.keys()),
            "tools": list(self.registry.tools.keys()),
            "relics": list(self.registry.relics.keys()),
            "workflows": list(self.registry.workflows.keys())
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get registry status and statistics"""
        return {
            "total_manifests": self.registry.total_manifests,
            "by_type": {
                "agents": len(self.registry.agents),
                "tools": len(self.registry.tools),
                "relics": len(self.registry.relics),
                "workflows": len(self.registry.workflows)
            },
            "last_updated": self.registry.last_updated.isoformat(),
            "manifests_root": str(self.manifests_root)
        }
    
    # ========================================================================
    # DEPENDENCY MANAGEMENT
    # ========================================================================
    
    async def resolve_dependencies(self, kind: str, name: str) -> Dict[str, List[str]]:
        """
        Get all dependencies for a specific manifest.
        
        Returns:
            Dictionary mapping dependency types to lists of names
        """
        manifest = await self.get_manifest(kind, name)
        if not manifest:
            return {}
        
        dependencies = {
            "agents": [],
            "tools": [],
            "relics": [],
            "workflows": [],
            "monuments": [],
            "amulets": []
        }
        
        # Extract dependencies based on manifest type
        if hasattr(manifest, 'import_') and manifest.import_:
            import_config = manifest.import_
            dependencies["agents"] = import_config.agents
            dependencies["tools"] = import_config.tools  
            dependencies["relics"] = import_config.relics
            dependencies["workflows"] = import_config.workflows
            dependencies["monuments"] = import_config.monuments
            dependencies["amulets"] = import_config.amulets
        
        # Additional dependencies from other fields
        if hasattr(manifest, 'dependencies'):
            dependencies["other"] = getattr(manifest, 'dependencies', [])
        
        return dependencies
    
    async def validate_dependencies(self, kind: str, name: str) -> ManifestValidationResponse:
        """Validate that all dependencies for a manifest are satisfied"""
        manifest = await self.get_manifest(kind, name)
        if not manifest:
            return ManifestValidationResponse(
                valid=False,
                errors=[f"Manifest {kind}/{name} not found"]
            )
        
        dependencies = await self.resolve_dependencies(kind, name)
        missing = []
        
        # Check each dependency type
        for dep_type, dep_names in dependencies.items():
            if dep_type in ["agents", "tools", "relics", "workflows"]:
                for dep_name in dep_names:
                    if not await self.get_manifest(dep_type[:-1], dep_name):  # Remove 's' from plural
                        missing.append(f"{dep_type[:-1]}/{dep_name}")
        
        return ManifestValidationResponse(
            valid=len(missing) == 0,
            dependencies_satisfied=len(missing) == 0,
            missing_dependencies=missing
        )
    
    async def _validate_dependencies_internal(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Internal dependency validation for raw manifest data"""
        missing = []
        
        if 'import' in data:
            import_section = data['import']
            
            # Check agents
            for agent_name in import_section.get('agents', []):
                if agent_name not in self.registry.agents:
                    missing.append(f"agent/{agent_name}")
            
            # Check tools
            for tool_name in import_section.get('tools', []):
                if tool_name not in self.registry.tools:
                    missing.append(f"tool/{tool_name}")
            
            # Check relics
            for relic_name in import_section.get('relics', []):
                if relic_name not in self.registry.relics:
                    missing.append(f"relic/{relic_name}")
            
            # Check workflows
            for workflow_name in import_section.get('workflows', []):
                if workflow_name not in self.registry.workflows:
                    missing.append(f"workflow/{workflow_name}")
        
        return len(missing) == 0, missing
    
    async def get_dependency_graph(self) -> Dict[str, Dict[str, List[str]]]:
        """Build complete dependency graph for visualization"""
        graph = {}
        
        all_manifests = {
            **{f"agent/{name}": manifest for name, manifest in self.registry.agents.items()},
            **{f"tool/{name}": manifest for name, manifest in self.registry.tools.items()},
            **{f"relic/{name}": manifest for name, manifest in self.registry.relics.items()},
            **{f"workflow/{name}": manifest for name, manifest in self.registry.workflows.items()}
        }
        
        for manifest_id, manifest in all_manifests.items():
            kind, name = manifest_id.split('/', 1)
            dependencies = await self.resolve_dependencies(kind, name)
            
            # Flatten dependencies
            flat_deps = []
            for dep_type, dep_names in dependencies.items():
                if dep_type in ["agents", "tools", "relics", "workflows"]:
                    for dep_name in dep_names:
                        flat_deps.append(f"{dep_type[:-1]}/{dep_name}")
            
            graph[manifest_id] = {
                "dependencies": flat_deps,
                "dependents": []  # Will be filled in second pass
            }
        
        # Second pass: fill in dependents
        for manifest_id, info in graph.items():
            for dep_id in info["dependencies"]:
                if dep_id in graph:
                    graph[dep_id]["dependents"].append(manifest_id)
        
        return graph
    
    # ========================================================================
    # FILESYSTEM SYNCHRONIZATION
    # ========================================================================
    
    async def load_manifests_from_filesystem(self) -> Dict[str, int]:
        """
        Load all manifests from the filesystem into the registry.
        
        Returns:
            Dictionary with counts of loaded manifests by type
        """
        counts = {"agents": 0, "tools": 0, "relics": 0, "workflows": 0, "errors": 0}
        
        if not self.manifests_root.exists():
            logger.warning(f"Manifests root directory does not exist: {self.manifests_root}")
            return counts
        
        # Define manifest directories
        manifest_dirs = {
            "agents": self.manifests_root / "agents",
            "tools": self.manifests_root / "tools", 
            "relics": self.manifests_root / "relics",
            "workflows": self.manifests_root / "workflows"
        }
        
        for kind, dir_path in manifest_dirs.items():
            if not dir_path.exists():
                logger.info(f"Directory does not exist, skipping: {dir_path}")
                continue
            
            await self._load_manifests_from_directory(dir_path, kind, counts)
        
        # Update registry stats
        self.registry.update_stats()
        
        logger.info(f"Loaded manifests - {counts}")
        return counts
    
    async def _load_manifests_from_directory(
        self, 
        directory: Path, 
        expected_kind: str, 
        counts: Dict[str, int]
    ):
        """Load manifests from a specific directory"""
        try:
            # Look for manifest files recursively
            manifest_files = []
            
            # Common manifest file patterns
            patterns = ["*.yml", "*.yaml", "manifest.yml", "manifest.yaml", "agent.yml", "tool.yml", "relic.yml"]
            
            for pattern in patterns:
                manifest_files.extend(directory.rglob(pattern))
            
            for file_path in manifest_files:
                try:
                    logger.debug(f"Loading manifest: {file_path}")
                    
                    # Parse manifest
                    manifest_data = await self.parser.parse_manifest_file(file_path)
                    
                    # Resolve relative paths
                    manifest_data = await self.parser.resolve_relative_paths(
                        manifest_data, 
                        file_path.parent
                    )
                    
                    # Register manifest
                    result = await self.register_manifest(manifest_data)
                    
                    if result.valid:
                        manifest_kind = manifest_data.get('kind', '').lower()
                        if manifest_kind + 's' in counts:  # Convert to plural
                            counts[manifest_kind + 's'] += 1
                        logger.debug(f"Successfully loaded: {file_path}")
                    else:
                        logger.error(f"Failed to validate manifest {file_path}: {result.errors}")
                        counts["errors"] += 1
                        
                except Exception as e:
                    logger.error(f"Error loading manifest {file_path}: {str(e)}")
                    counts["errors"] += 1
                    
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {str(e)}")
    
    # ========================================================================
    # REGISTRY PERSISTENCE
    # ========================================================================
    
    async def export_registry(self) -> Dict[str, Any]:
        """Export the entire registry as JSON-serializable data"""
        return {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_manifests": self.registry.total_manifests,
                "manifests_root": str(self.manifests_root)
            },
            "agents": {name: manifest.dict() for name, manifest in self.registry.agents.items()},
            "tools": {name: manifest.dict() for name, manifest in self.registry.tools.items()},
            "relics": {name: manifest.dict() for name, manifest in self.registry.relics.items()},
            "workflows": {name: manifest.dict() for name, manifest in self.registry.workflows.items()}
        }
    
    async def save_registry_to_file(self, file_path: Path):
        """Save registry to a JSON file"""
        export_data = await self.export_registry()
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Registry exported to: {file_path}")
    
    async def validate_manifest(self, data: Dict[str, Any]) -> ManifestValidationResponse:
        """Validate a manifest without registering it"""
        try:
            # Validate structure
            is_valid, structure_errors = await self.parser.validate_manifest_structure(data)
            
            if not is_valid:
                return ManifestValidationResponse(
                    valid=False,
                    errors=structure_errors
                )
            
            # Create typed manifest to validate Pydantic model
            typed_manifest = await self.parser.create_typed_manifest(data)
            
            # Validate dependencies
            deps_valid, missing_deps = await self._validate_dependencies_internal(data)
            
            warnings = []
            if not deps_valid:
                warnings.append(f"Missing dependencies: {', '.join(missing_deps)}")
            
            return ManifestValidationResponse(
                valid=True,
                warnings=warnings,
                dependencies_satisfied=deps_valid,
                missing_dependencies=missing_deps
            )
            
        except Exception as e:
            return ManifestValidationResponse(
                valid=False,
                errors=[str(e)]
            )
    
    # ========================================================================
    # HOT-RELOAD SUPPORT
    # ========================================================================
    
    async def reload_manifest_file(self, file_path: Path):
        """
        Reload a specific manifest file (triggered by filesystem watcher).
        
        Args:
            file_path: Path to the manifest file that changed
        """
        try:
            logger.info(f"♻️  Reloading manifest: {file_path}")
            
            # Parse the manifest file
            manifest_data = await self.parser.parse_manifest_file(file_path)
            
            # Register/update in registry
            result = await self.register_manifest(manifest_data)
            
            if result.valid:
                logger.success(f"✅ Successfully reloaded: {manifest_data.get('kind')}/{manifest_data.get('name')}")
            else:
                logger.error(f"❌ Failed to reload {file_path}: {result.errors}")
            
            return result
            
        except ManifestParsingError as e:
            logger.error(f"❌ Parsing error reloading {file_path}: {e}")
            return ManifestValidationResponse(valid=False, errors=[str(e)])
        except Exception as e:
            logger.error(f"❌ Unexpected error reloading {file_path}: {e}")
            return ManifestValidationResponse(valid=False, errors=[str(e)])
    
    async def remove_manifest_by_path(self, file_path: Path):
        """
        Remove a manifest from the registry (triggered when file is deleted).
        
        Args:
            file_path: Path to the deleted manifest file
        """
        try:
            # Try to parse the file path to determine manifest type and name
            # This is a best-effort approach since the file no longer exists
            
            # Search through registry to find matching manifest
            file_path_str = str(file_path)
            removed = False
            
            for kind_name, registry_dict in [
                ("Agent", self.registry.agents),
                ("Tool", self.registry.tools),
                ("Relic", self.registry.relics),
                ("Workflow", self.registry.workflows)
            ]:
                # Find manifest by matching file path in metadata
                for name, manifest in list(registry_dict.items()):
                    # Check if this manifest corresponds to the deleted file
                    # (This requires manifests to store their source path)
                    if self._manifest_matches_path(manifest, file_path):
                        del registry_dict[name]
                        self.registry.update_stats()
                        logger.info(f"🗑️  Removed {kind_name} manifest: {name}")
                        removed = True
                        break
            
            if not removed:
                logger.warning(f"⚠️  Could not find manifest for deleted file: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error removing manifest for {file_path}: {e}")
    
    def _manifest_matches_path(self, manifest: Any, file_path: Path) -> bool:
        """
        Check if a manifest corresponds to a given file path.
        Currently uses heuristic matching; could be improved with metadata.
        """
        # If manifest has _source_path metadata, use it
        if hasattr(manifest, '_source_path'):
            return Path(manifest._source_path) == file_path
        
        # Fallback: match by name in path
        if hasattr(manifest, 'name'):
            return manifest.name in str(file_path)
        
        return False
            )