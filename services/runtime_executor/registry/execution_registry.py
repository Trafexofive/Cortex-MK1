"""
Execution registry for tracking and managing runtime executions
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from models.execution_models import (
    ExecutionRequest,
    ExecutionResponse,
    ExecutionSummary,
    ExecutionStatus
)


class ExecutionRegistry:
    """Registry for tracking execution history and status"""
    
    def __init__(self):
        self.executions: Dict[str, ExecutionResponse] = {}
        self.execution_history: List[ExecutionSummary] = []
        self.max_history_size = 10000
    
    async def register_execution(self, request: ExecutionRequest) -> str:
        """Register a new execution and return execution ID"""
        execution_id = str(uuid.uuid4())
        
        # Create initial response
        response = ExecutionResponse(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            started_at=datetime.utcnow()
        )
        
        self.executions[execution_id] = response
        
        # Add to history
        summary = ExecutionSummary(
            execution_id=execution_id,
            entity_type=request.entity_type,
            entity_name=request.entity_name,
            status=ExecutionStatus.PENDING,
            started_at=response.started_at,
            user_id=request.context.user_id
        )
        
        self.execution_history.append(summary)
        
        # Trim history if needed
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
        
        return execution_id
    
    async def update_execution(self, execution_id: str, response: ExecutionResponse):
        """Update execution with results"""
        self.executions[execution_id] = response
        
        # Update history summary
        for summary in self.execution_history:
            if summary.execution_id == execution_id:
                summary.status = response.status
                summary.completed_at = response.completed_at
                summary.duration_seconds = response.duration_seconds
                summary.error = response.error
                break
    
    async def get_execution(self, execution_id: str) -> Optional[ExecutionResponse]:
        """Get execution details by ID"""
        return self.executions.get(execution_id)
    
    async def list_executions(
        self,
        status: Optional[ExecutionStatus] = None,
        entity_type: Optional[str] = None,
        limit: int = 50
    ) -> List[ExecutionSummary]:
        """List executions with optional filters"""
        filtered_history = self.execution_history
        
        if status:
            filtered_history = [e for e in filtered_history if e.status == status]
        
        if entity_type:
            filtered_history = [e for e in filtered_history if e.entity_type == entity_type]
        
        # Return most recent first
        return list(reversed(filtered_history[-limit:]))
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Mark execution as cancelled"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
                execution.status = ExecutionStatus.CANCELLED
                execution.completed_at = datetime.utcnow()
                
                # Update history
                for summary in self.execution_history:
                    if summary.execution_id == execution_id:
                        summary.status = ExecutionStatus.CANCELLED
                        summary.completed_at = execution.completed_at
                        break
                
                return True
        return False
    
    async def get_statistics(self) -> Dict[str, any]:
        """Get execution statistics"""
        stats = defaultdict(int)
        
        for summary in self.execution_history:
            stats[f"total_{summary.entity_type}"] += 1
            stats[f"status_{summary.status.value}"] += 1
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_executions = [
            e for e in self.execution_history 
            if e.started_at >= recent_cutoff
        ]
        
        stats["recent_24h"] = len(recent_executions)
        stats["total_executions"] = len(self.execution_history)
        stats["active_executions"] = len([
            e for e in self.executions.values() 
            if e.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        ])
        
        return dict(stats)