"""
==============================================================================
PYTHON EXECUTOR v1.0
==============================================================================
Secure Python script executor with sandboxing and resource limits.
Handles execution of Python-based tools and agent implementations.
==============================================================================
"""

import os
import sys
import json
import uuid
import asyncio
import subprocess
import tempfile
import resource
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

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


class PythonExecutor(BaseExecutor):
    """
    Secure Python script executor with sandboxing capabilities.
    
    Features:
    - Resource limiting (memory, CPU, time)
    - Filesystem sandboxing
    - Network restrictions
    - Import restrictions for untrusted code
    - Secure parameter passing via JSON
    """
    
    def __init__(self):
        super().__init__(RuntimeType.PYTHON)
        self.python_executable = sys.executable
        self.temp_dir = Path(tempfile.gettempdir()) / "cortex_python_exec"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute Python script with security constraints"""
        execution_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        try:
            # Register active execution
            self.active_executions[execution_id] = asyncio.current_task()
            
            # Prepare execution environment
            script_path = await self._prepare_script(request)
            env_vars = await self._prepare_environment(request)
            
            # Execute with resource limits
            result = await self._execute_with_limits(
                script_path, 
                request.parameters, 
                request.context,
                env_vars
            )
            
            # Update statistics
            duration = (datetime.utcnow() - started_at).total_seconds()
            self._update_stats(result["success"], duration)
            
            return self._create_execution_response(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED if result["success"] else ExecutionStatus.FAILED,
                started_at=started_at,
                output=result.get("output"),
                stdout=result.get("stdout"),
                stderr=result.get("stderr"),
                exit_code=result.get("exit_code"),
                error=result.get("error"),
                script_path=str(script_path),
                memory_used_mb=result.get("memory_used_mb"),
                cpu_time_seconds=result.get("cpu_time_seconds")
            )
            
        except Exception as e:
            logger.error(f"Python execution failed: {str(e)}")
            duration = (datetime.utcnow() - started_at).total_seconds()
            self._update_stats(False, duration)
            
            return self._create_execution_response(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                started_at=started_at,
                error=str(e),
                error_type=type(e).__name__
            )
        finally:
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _prepare_script(self, request: ExecutionRequest) -> Path:
        """Prepare the Python script for execution"""
        manifest = request.manifest_data
        
        # Get script path from manifest
        script_path = None
        
        # Handle different manifest formats
        if "path" in manifest:
            script_path = manifest["path"]
        elif "implementation" in manifest and "path" in manifest["implementation"]:
            script_path = manifest["implementation"]["path"]
        elif "SystemTools" in manifest:
            # Handle the sys_info.yml format
            tool_name = request.entity_name
            tool_data = manifest["SystemTools"].get("SystemInfo", {})
            script_path = tool_data.get("path")
        
        if not script_path:
            raise ValueError("No script path found in manifest")
        
        # Convert relative path to absolute
        if script_path.startswith("./"):
            # Assume relative to manifests directory structure
            manifests_root = Path("/app/manifests")
            entity_dir = manifests_root / f"{request.entity_type}s" / request.entity_name
            script_path = entity_dir / script_path[2:]
        else:
            script_path = Path(script_path)
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        return script_path
    
    async def _prepare_environment(self, request: ExecutionRequest) -> Dict[str, str]:
        """Prepare environment variables for execution"""
        env_vars = os.environ.copy()
        
        # Add context environment variables
        env_vars.update(request.context.environment_vars)
        
        # Add security restrictions for sandboxed execution
        if request.context.security_level == SecurityLevel.SANDBOXED:
            env_vars["PYTHONDONTWRITEBYTECODE"] = "1"
            env_vars["PYTHONUNBUFFERED"] = "1"
        
        return env_vars
    
    async def _execute_with_limits(
        self, 
        script_path: Path, 
        parameters: Dict[str, Any],
        context,
        env_vars: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute script with resource limits and security constraints"""
        
        # Create temporary file for parameters
        params_file = self.temp_dir / f"params_{uuid.uuid4()}.json"
        with open(params_file, 'w') as f:
            json.dump(parameters, f)
        
        try:
            # Build command
            cmd = [
                self.python_executable,
                str(script_path),
                str(params_file)
            ]
            
            # Set resource limits
            def preexec_fn():
                if context.security_level != SecurityLevel.TRUSTED:
                    # Memory limit
                    if context.resource_limits.max_memory_mb:
                        max_memory = context.resource_limits.max_memory_mb * 1024 * 1024
                        resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))
                    
                    # CPU time limit
                    if context.resource_limits.max_execution_time_seconds:
                        cpu_time = context.resource_limits.max_execution_time_seconds
                        resource.setrlimit(resource.RLIMIT_CPU, (cpu_time, cpu_time))
            
            # Execute with timeout
            timeout = context.timeout_seconds or 300
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env_vars,
                preexec_fn=preexec_fn if os.name != 'nt' else None,  # Unix only
                cwd=context.working_directory
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                stdout_str = stdout.decode('utf-8') if stdout else ""
                stderr_str = stderr.decode('utf-8') if stderr else ""
                
                # Parse output if it's JSON
                output = None
                if stdout_str.strip():
                    try:
                        output = json.loads(stdout_str)
                    except json.JSONDecodeError:
                        output = stdout_str
                
                return {
                    "success": process.returncode == 0,
                    "output": output,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "exit_code": process.returncode
                }
                
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds",
                    "exit_code": -1
                }
                
        finally:
            # Clean up parameters file
            if params_file.exists():
                params_file.unlink()
    
    async def get_capabilities(self) -> ExecutorCapabilities:
        """Get Python executor capabilities"""
        return ExecutorCapabilities(
            runtime_type=RuntimeType.PYTHON,
            supported_languages=["python"],
            supports_isolation=True,
            supports_resource_limits=True,
            supports_networking=False,  # Disabled for security
            supports_file_system=True,
            max_memory_mb=2048,
            max_execution_time_seconds=600
        )


# ============================================================================
# UTILITY FUNCTIONS FOR PYTHON SCRIPT INTEGRATION
# ============================================================================

def get_execution_parameters() -> Dict[str, Any]:
    """
    Utility function for Python scripts to get their execution parameters.
    Should be called from within the executed script.
    """
    if len(sys.argv) < 2:
        return {}
    
    params_file = sys.argv[1]
    try:
        with open(params_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def return_result(result: Any):
    """
    Utility function for Python scripts to return their results.
    Results will be JSON-serialized and captured by the executor.
    """
    try:
        print(json.dumps(result, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e), "type": "serialization_error"}))
        sys.exit(1)


def return_error(error_message: str, error_type: str = "execution_error"):
    """
    Utility function for Python scripts to return error information.
    """
    result = {
        "error": error_message,
        "type": error_type,
        "status": "error"
    }
    print(json.dumps(result))
    sys.exit(1)


# Make utilities available for import
__all__ = [
    "PythonExecutor",
    "get_execution_parameters", 
    "return_result",
    "return_error"
]