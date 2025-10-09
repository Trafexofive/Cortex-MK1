"""
==============================================================================
DOCKER MANAGER - Container Lifecycle Management
==============================================================================
Manages Docker container creation, execution, and cleanup.
==============================================================================
"""

import docker
import asyncio
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
from pathlib import Path

from models.container_models import (
    ToolExecutionRequest,
    ToolExecutionResult,
    RelicStartRequest,
    RelicInfo,
    ContainerStatus,
    ContainerStats,
    ExecutionStatus
)


class DockerManager:
    """Manages Docker container operations."""
    
    def __init__(self):
        self.client = docker.from_env()
        self.executions: Dict[str, ToolExecutionResult] = {}
        self.relics: Dict[str, RelicInfo] = {}
        logger.info("🐳 Docker manager initialized")
    
    # ========================================================================
    # TOOL EXECUTION
    # ========================================================================
    
    async def execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """Execute a tool in an ephemeral container."""
        
        result = ToolExecutionResult(
            tool_name=request.tool_name,
            session_id=request.session_id,
            status=ExecutionStatus.PENDING
        )
        
        self.executions[result.execution_id] = result
        
        try:
            # Get or build image
            image = await self._get_or_build_image(
                request.image,
                request.dockerfile,
                request.build_context,
                request.tool_name
            )
            
            # Prepare container config
            container_config = {
                "image": image,
                "name": f"tool_{request.tool_name}_{request.session_id}_{result.execution_id[:8]}",
                "detach": True,
                "remove": False,  # We'll remove manually after reading logs
                "environment": {
                    **request.environment,
                    "TOOL_NAME": request.tool_name,
                    "SESSION_ID": request.session_id,
                    "PARAMETERS": json.dumps(request.parameters)
                },
                "network_mode": request.network_mode,
                "mem_limit": f"{request.resource_limits.memory_mb}m",
                "cpu_quota": int(request.resource_limits.cpu_limit * 100000),
                "cpu_period": 100000,
            }
            
            # Add volumes if specified
            if request.volumes:
                container_config["volumes"] = request.volumes
            
            logger.info(f"🔧 Executing tool: {request.tool_name} (session: {request.session_id})")
            
            # Create and start container
            result.status = ExecutionStatus.RUNNING
            result.started_at = datetime.utcnow()
            
            container = self.client.containers.run(**container_config)
            result.container_id = container.id
            
            logger.debug(f"Container started: {container.short_id}")
            
            # Wait for completion with timeout
            timeout = request.resource_limits.timeout_seconds
            start_time = time.time()
            
            exit_code = await self._wait_for_container(container, timeout)
            
            execution_time = time.time() - start_time
            result.execution_time_seconds = execution_time
            result.completed_at = datetime.utcnow()
            
            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            result.stdout = stdout
            result.stderr = stderr
            result.exit_code = exit_code
            
            # Parse result from stdout (assuming JSON output)
            try:
                if stdout.strip():
                    result.result = json.loads(stdout)
            except json.JSONDecodeError:
                # If not JSON, just keep stdout as is
                pass
            
            # Get resource stats
            stats = container.stats(stream=False)
            if stats:
                memory_used = stats.get('memory_stats', {}).get('usage', 0)
                result.memory_used_mb = memory_used / (1024 * 1024)
            
            # Determine final status
            if exit_code == 0:
                result.status = ExecutionStatus.SUCCESS
                logger.info(f"✅ Tool execution completed: {request.tool_name} ({execution_time:.2f}s)")
            elif exit_code == 124:  # Timeout signal
                result.status = ExecutionStatus.TIMEOUT
                result.error = f"Execution timed out after {timeout}s"
                logger.warning(f"⏱️  Tool execution timeout: {request.tool_name}")
            else:
                result.status = ExecutionStatus.FAILED
                result.error = f"Exit code: {exit_code}"
                logger.error(f"❌ Tool execution failed: {request.tool_name} (exit {exit_code})")
            
            # Cleanup container
            if request.cleanup:
                try:
                    container.remove(force=True)
                    logger.debug(f"Container removed: {container.short_id}")
                except Exception as e:
                    logger.warning(f"Failed to remove container {container.short_id}: {e}")
            
        except docker.errors.ImageNotFound as e:
            result.status = ExecutionStatus.FAILED
            result.error = f"Image not found: {str(e)}"
            result.completed_at = datetime.utcnow()
            logger.error(f"Image not found for tool {request.tool_name}: {e}")
            
        except docker.errors.APIError as e:
            result.status = ExecutionStatus.FAILED
            result.error = f"Docker API error: {str(e)}"
            result.completed_at = datetime.utcnow()
            logger.error(f"Docker API error executing tool {request.tool_name}: {e}")
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            logger.error(f"Unexpected error executing tool {request.tool_name}: {e}")
        
        return result
    
    async def _wait_for_container(self, container, timeout: int) -> int:
        """Wait for container to complete with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            container.reload()
            
            if container.status in ['exited', 'dead']:
                return container.attrs['State']['ExitCode']
            
            await asyncio.sleep(0.5)
        
        # Timeout - kill container
        try:
            container.kill()
        except Exception as e:
            logger.warning(f"Failed to kill timed out container: {e}")
        
        return 124  # Timeout exit code
    
    async def _get_or_build_image(
        self,
        image: Optional[str],
        dockerfile: Optional[str],
        build_context: Optional[str],
        name: str
    ) -> str:
        """Get existing image or build from Dockerfile."""
        
        # If image specified, use it
        if image:
            try:
                self.client.images.get(image)
                return image
            except docker.errors.ImageNotFound:
                logger.info(f"Pulling image: {image}")
                self.client.images.pull(image)
                return image
        
        # Build from Dockerfile
        if dockerfile and build_context:
            tag = f"cortex/tool-{name}:latest"
            
            logger.info(f"Building image: {tag} from {dockerfile}")
            
            build_context_path = Path(build_context).resolve()
            dockerfile_path = Path(dockerfile).resolve()
            
            # Build image
            image_obj, build_logs = self.client.images.build(
                path=str(build_context_path),
                dockerfile=str(dockerfile_path.relative_to(build_context_path)),
                tag=tag,
                rm=True,
                forcerm=True
            )
            
            # Log build output
            for log in build_logs:
                if 'stream' in log:
                    logger.debug(log['stream'].strip())
            
            return tag
        
        raise ValueError(f"Must provide either 'image' or both 'dockerfile' and 'build_context'")
    
    def get_execution(self, execution_id: str) -> Optional[ToolExecutionResult]:
        """Get execution result by ID."""
        return self.executions.get(execution_id)
    
    def get_execution_logs(self, execution_id: str) -> Dict[str, str]:
        """Get logs for an execution."""
        result = self.executions.get(execution_id)
        if not result:
            raise ValueError(f"Execution not found: {execution_id}")
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        result = self.executions.get(execution_id)
        if not result:
            return False
        
        if result.status != ExecutionStatus.RUNNING:
            return False
        
        try:
            if result.container_id:
                container = self.client.containers.get(result.container_id)
                container.kill()
                result.status = ExecutionStatus.CANCELLED
                result.completed_at = datetime.utcnow()
                logger.info(f"Cancelled execution: {execution_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_id}: {e}")
            return False
        
        return False
    
    # ========================================================================
    # RELIC MANAGEMENT
    # ========================================================================
    
    async def start_relic(self, request: RelicStartRequest, network_id: Optional[str] = None) -> RelicInfo:
        """Start a relic container."""
        
        relic_info = RelicInfo(
            relic_name=request.relic_name,
            session_id=request.session_id,
            status=ContainerStatus.CREATED,
            container_id="",
            container_name=""
        )
        
        try:
            # Get or build image
            image = await self._get_or_build_image(
                request.image,
                request.dockerfile,
                request.build_context,
                request.relic_name
            )
            
            # Container name
            container_name = f"relic_{request.relic_name}_{request.session_id}_{relic_info.relic_id[:8]}"
            relic_info.container_name = container_name
            
            # Prepare container config
            container_config = {
                "image": image,
                "name": container_name,
                "detach": True,
                "environment": {
                    **request.environment,
                    "RELIC_NAME": request.relic_name,
                    "SESSION_ID": request.session_id
                },
                "mem_limit": f"{request.resource_limits.memory_mb}m",
                "cpu_quota": int(request.resource_limits.cpu_limit * 100000),
                "cpu_period": 100000,
            }
            
            # Add volumes
            if request.volumes:
                container_config["volumes"] = request.volumes
            
            # Add port mappings
            if request.ports:
                container_config["ports"] = request.ports
            
            # Add to network if provided
            if network_id:
                container_config["network"] = network_id
                relic_info.network_id = network_id
            
            logger.info(f"🔮 Starting relic: {request.relic_name} (session: {request.session_id})")
            
            # Create and start container
            container = self.client.containers.run(**container_config)
            relic_info.container_id = container.id
            relic_info.status = ContainerStatus.RUNNING
            relic_info.started_at = datetime.utcnow()
            
            # Set internal URL
            if network_id:
                relic_info.internal_url = f"http://{container_name}:8000"
            
            logger.info(f"✅ Relic started: {request.relic_name} ({container.short_id})")
            
            # Store relic info
            self.relics[relic_info.relic_id] = relic_info
            
            # Wait for health check
            if request.health_check_endpoint:
                await self._wait_for_health(
                    relic_info,
                    request.health_check_endpoint,
                    request.health_check_timeout_seconds
                )
            
        except Exception as e:
            logger.error(f"Failed to start relic {request.relic_name}: {e}")
            relic_info.status = ContainerStatus.DEAD
            raise
        
        return relic_info
    
    async def _wait_for_health(self, relic_info: RelicInfo, endpoint: str, timeout: int):
        """Wait for relic to become healthy."""
        import httpx
        
        if not relic_info.internal_url:
            return
        
        url = f"{relic_info.internal_url}{endpoint}"
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < timeout:
                try:
                    response = await client.get(url, timeout=2.0)
                    if response.status_code == 200:
                        relic_info.healthy = True
                        relic_info.last_health_check = datetime.utcnow()
                        logger.info(f"✅ Relic healthy: {relic_info.relic_name}")
                        return
                except Exception:
                    pass
                
                await asyncio.sleep(2)
        
        logger.warning(f"⚠️  Relic health check timeout: {relic_info.relic_name}")
    
    def get_relic(self, relic_id: str) -> Optional[RelicInfo]:
        """Get relic info by ID."""
        return self.relics.get(relic_id)
    
    def list_relics(self, session_id: Optional[str] = None) -> List[RelicInfo]:
        """List relics, optionally filtered by session."""
        if session_id:
            return [r for r in self.relics.values() if r.session_id == session_id]
        return list(self.relics.values())
    
    async def stop_relic(self, relic_id: str) -> bool:
        """Stop a relic container."""
        relic_info = self.relics.get(relic_id)
        if not relic_info:
            return False
        
        try:
            container = self.client.containers.get(relic_info.container_id)
            container.stop(timeout=10)
            container.remove(force=True)
            
            relic_info.status = ContainerStatus.EXITED
            logger.info(f"Stopped relic: {relic_info.relic_name}")
            
            # Remove from tracking
            del self.relics[relic_id]
            
            return True
        except Exception as e:
            logger.error(f"Failed to stop relic {relic_id}: {e}")
            return False
    
    # ========================================================================
    # CONTAINER STATS
    # ========================================================================
    
    def get_container_stats(self, container_id: str) -> Optional[ContainerStats]:
        """Get container resource statistics."""
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Parse stats
            memory_stats = stats.get('memory_stats', {})
            memory_used = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            # Calculate CPU percentage
            cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                       precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                          precpu_stats.get('system_cpu_usage', 0)
            
            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_count = cpu_stats.get('online_cpus', 1)
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0
            
            # Network stats
            networks = stats.get('networks', {})
            network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
            network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
            
            # Disk I/O
            blkio_stats = stats.get('blkio_stats', {})
            io_service_bytes = blkio_stats.get('io_service_bytes_recursive', [])
            disk_read = sum(stat.get('value', 0) for stat in io_service_bytes if stat.get('op') == 'Read')
            disk_write = sum(stat.get('value', 0) for stat in io_service_bytes if stat.get('op') == 'Write')
            
            return ContainerStats(
                container_id=container.id,
                name=container.name,
                status=ContainerStatus(container.status),
                running=container.status == 'running',
                cpu_percent=cpu_percent,
                memory_used_mb=memory_used / (1024 * 1024),
                memory_limit_mb=memory_limit / (1024 * 1024),
                memory_percent=(memory_used / memory_limit * 100) if memory_limit > 0 else 0,
                network_rx_mb=network_rx / (1024 * 1024),
                network_tx_mb=network_tx / (1024 * 1024),
                disk_read_mb=disk_read / (1024 * 1024),
                disk_write_mb=disk_write / (1024 * 1024),
                created_at=datetime.fromisoformat(container.attrs['Created'].replace('Z', '+00:00')),
                started_at=datetime.fromisoformat(container.attrs['State']['StartedAt'].replace('Z', '+00:00'))
                    if container.attrs['State'].get('StartedAt') else None
            )
        except Exception as e:
            logger.error(f"Failed to get stats for container {container_id}: {e}")
            return None
    
    def list_all_stats(self) -> List[ContainerStats]:
        """Get stats for all containers."""
        stats = []
        
        # Stats for tool executions
        for result in self.executions.values():
            if result.container_id and result.status == ExecutionStatus.RUNNING:
                container_stats = self.get_container_stats(result.container_id)
                if container_stats:
                    stats.append(container_stats)
        
        # Stats for relics
        for relic in self.relics.values():
            container_stats = self.get_container_stats(relic.container_id)
            if container_stats:
                stats.append(container_stats)
        
        return stats
    
    # ========================================================================
    # SESSION CLEANUP
    # ========================================================================
    
    async def cleanup_session(self, session_id: str, force: bool = False) -> Dict[str, Any]:
        """Cleanup all containers for a session."""
        containers_removed = 0
        errors = []
        
        # Cleanup tool executions
        for execution_id, result in list(self.executions.items()):
            if result.session_id == session_id and result.container_id:
                try:
                    container = self.client.containers.get(result.container_id)
                    container.remove(force=force)
                    containers_removed += 1
                    del self.executions[execution_id]
                except Exception as e:
                    errors.append(f"Failed to remove execution container {result.container_id}: {e}")
        
        # Cleanup relics
        for relic_id, relic in list(self.relics.items()):
            if relic.session_id == session_id:
                success = await self.stop_relic(relic_id)
                if success:
                    containers_removed += 1
                else:
                    errors.append(f"Failed to stop relic {relic.relic_name}")
        
        logger.info(f"🧹 Cleaned up session {session_id}: {containers_removed} containers removed")
        
        return {
            "session_id": session_id,
            "containers_removed": containers_removed,
            "errors": errors
        }
