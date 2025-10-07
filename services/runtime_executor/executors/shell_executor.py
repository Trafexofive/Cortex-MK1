"""
Shell/Bash script executor with security constraints
"""

import os
import uuid
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from loguru import logger
from models.execution_models import (
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatus,
    RuntimeType,
    ExecutorCapabilities,
    SecurityLevel
)
from .base_executor import BaseExecutor


class ShellExecutor(BaseExecutor):
    """Secure shell script executor"""
    
    def __init__(self):
        super().__init__(RuntimeType.SHELL)
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute shell script with security constraints"""
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        try:
            self.active_executions[execution_id] = asyncio.current_task()
            
            # For now, basic shell execution
            # In production, this would need extensive security hardening
            
            script_path = await self._prepare_script(request)
            result = await self._execute_shell_script(script_path, request)
            
            duration = (datetime.utcnow() - started_at).total_seconds()
            self._update_stats(result["success"], duration)
            
            return self._create_execution_response(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED if result["success"] else ExecutionStatus.FAILED,
                started_at=started_at,
                stdout=result.get("stdout"),
                stderr=result.get("stderr"),
                exit_code=result.get("exit_code"),
                error=result.get("error")
            )
            
        except Exception as e:
            logger.error(f"Shell execution failed: {str(e)}")
            duration = (datetime.utcnow() - started_at).total_seconds()
            self._update_stats(False, duration)
            
            return self._create_execution_response(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                error=str(e)
            )
        finally:
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _prepare_script(self, request: ExecutionRequest) -> Path:
        """Get script path from manifest"""
        manifest = request.manifest_data
        
        script_path = None
        if "path" in manifest:
            script_path = manifest["path"]
        elif "implementation" in manifest and "path" in manifest["implementation"]:
            script_path = manifest["implementation"]["path"]
        
        if not script_path:
            raise ValueError("No script path found in manifest")
        
        return Path(script_path)
    
    async def _execute_shell_script(self, script_path: Path, request: ExecutionRequest) -> Dict[str, Any]:
        """Execute the shell script"""
        try:
            timeout = request.context.timeout_seconds or 300
            
            process = await asyncio.create_subprocess_exec(
                "bash", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8') if stdout else "",
                "stderr": stderr.decode('utf-8') if stderr else "",
                "exit_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Execution timed out after {timeout} seconds",
                "exit_code": -1
            }
    
    async def get_capabilities(self) -> ExecutorCapabilities:
        """Get shell executor capabilities"""
        return ExecutorCapabilities(
            runtime_type=RuntimeType.SHELL,
            supported_languages=["bash", "sh"],
            supports_isolation=False,  # Basic shell execution
            supports_resource_limits=False,
            supports_networking=True,
            supports_file_system=True
        )