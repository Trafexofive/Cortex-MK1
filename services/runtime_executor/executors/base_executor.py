"""
Base executor class for all runtime executors
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any

from models.execution_models import (
    ExecutionRequest,
    ExecutionResponse,
    ExecutionStatus,
    RuntimeType,
    ExecutorCapabilities,
    ExecutorStatus
)


class BaseExecutor(ABC):
    """Base class for all runtime executors"""
    
    def __init__(self, runtime_type: RuntimeType):
        self.runtime_type = runtime_type
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }
    
    @abstractmethod
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        """Execute the request and return response"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> ExecutorCapabilities:
        """Get executor capabilities"""
        pass
    
    async def get_status(self) -> ExecutorStatus:
        """Get current executor status"""
        avg_time = None
        if self.stats["total_executions"] > 0:
            avg_time = self.stats["total_execution_time"] / self.stats["total_executions"]
        
        return ExecutorStatus(
            available=True,
            active_executions=len(self.active_executions),
            total_executions=self.stats["total_executions"],
            successful_executions=self.stats["successful_executions"],
            failed_executions=self.stats["failed_executions"],
            average_execution_time_seconds=avg_time
        )
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            del self.active_executions[execution_id]
            return True
        return False
    
    def _create_execution_response(
        self, 
        execution_id: str, 
        status: ExecutionStatus,
        started_at: datetime,
        **kwargs
    ) -> ExecutionResponse:
        """Helper to create execution response"""
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        return ExecutionResponse(
            execution_id=execution_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            runtime_type=self.runtime_type,
            **kwargs
        )
    
    def _update_stats(self, success: bool, duration: float):
        """Update executor statistics"""
        self.stats["total_executions"] += 1
        self.stats["total_execution_time"] += duration
        if success:
            self.stats["successful_executions"] += 1
        else:
            self.stats["failed_executions"] += 1