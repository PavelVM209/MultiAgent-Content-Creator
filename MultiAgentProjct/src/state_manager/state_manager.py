"""
State Manager для управления состоянием мультиагентной системы
"""

import asyncio
import uuid
from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    WorkflowStatus,
    AgentStep,
    StateSnapshot,
    StateTransition,
    RollbackPoint,
    WorkflowExecutionPlan,
    QualityThresholds,
    WorkflowContext
)


class WorkflowState:
    """Состояние workflow"""
    
    def __init__(self, workflow_id: str, context: WorkflowContext):
        self.workflow_id = workflow_id
        self.context = context
        self.status = WorkflowStatus.PENDING
        self.current_step: Optional[AgentStep] = None
        self.snapshots: List[StateSnapshot] = []
        self.transitions: List[StateTransition] = []
        self.rollback_points: List[RollbackPoint] = []
        self.execution_plan: Optional[WorkflowExecutionPlan] = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.logger = getLogger(f"{__name__}.WorkflowState.{workflow_id}")
    
    def create_snapshot(
        self,
        step: AgentStep,
        data: Dict[str, Any],
        agent_results: Dict[str, Any],
        quality_scores: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateSnapshot:
        """Создать снимок состояния"""
        snapshot = StateSnapshot(
            workflow_id=self.workflow_id,
            step=step,
            data=data.copy(),
            agent_results=agent_results.copy(),
            quality_scores=quality_scores.copy(),
            metadata=metadata or {}
        )
        
        self.snapshots.append(snapshot)
        self.updated_at = datetime.utcnow()
        
        self.logger.info(
            f"Created snapshot for step {step}",
            extra={
                "workflow_id": self.workflow_id,
                "step": step,
                "snapshot_count": len(self.snapshots)
            }
        )
        
        return snapshot
    
    def add_transition(
        self,
        to_step: AgentStep,
        transition_type: str,
        from_step: Optional[AgentStep] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateTransition:
        """Добавить переход между состояниями"""
        transition = StateTransition(
            from_step=from_step or self.current_step,
            to_step=to_step,
            transition_type=transition_type,
            reason=reason,
            metadata=metadata or {}
        )
        
        self.transitions.append(transition)
        self.current_step = to_step
        self.updated_at = datetime.utcnow()
        
        self.logger.info(
            f"Transition from {from_step} to {to_step} ({transition_type})",
            extra={
                "workflow_id": self.workflow_id,
                "from_step": from_step,
                "to_step": to_step,
                "transition_type": transition_type,
                "reason": reason
            }
        )
        
        return transition
    
    def add_rollback_point(self, step: AgentStep, snapshot: StateSnapshot) -> RollbackPoint:
        """Добавить точку отката"""
        rollback_point = RollbackPoint(
            step=step,
            snapshot=snapshot
        )
        
        self.rollback_points.append(rollback_point)
        self.updated_at = datetime.utcnow()
        
        self.logger.info(
            f"Added rollback point for step {step}",
            extra={
                "workflow_id": self.workflow_id,
                "step": step,
                "rollback_points_count": len(self.rollback_points)
            }
        )
        
        return rollback_point
    
    def get_rollback_point(self, step: AgentStep) -> Optional[RollbackPoint]:
        """Получить точку отката для шага"""
        for rp in reversed(self.rollback_points):
            if rp.step == step and rp.is_available:
                return rp
        return None
    
    def get_latest_rollback_point(self) -> Optional[RollbackPoint]:
        """Получить последнюю доступную точку отката"""
        for rp in reversed(self.rollback_points):
            if rp.is_available:
                return rp
        return None
    
    def invalidate_rollback_points(self, from_step: AgentStep):
        """Инвалидировать точки отката начиная с указанного шага"""
        for rp in self.rollback_points:
            if rp.step == from_step:
                rp.is_available = False
            # Инвалидируем все последующие точки
            step_index = self.execution_plan.steps.index(from_step) if self.execution_plan else -1
            if step_index >= 0:
                try:
                    rp_index = self.execution_plan.steps.index(rp.step)
                    if rp_index >= step_index:
                        rp.is_available = False
                except ValueError:
                    pass
    
    def update_status(self, status: WorkflowStatus, reason: Optional[str] = None):
        """Обновить статус workflow"""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.utcnow()
        
        self.logger.info(
            f"Status changed from {old_status} to {status}",
            extra={
                "workflow_id": self.workflow_id,
                "old_status": old_status,
                "new_status": status,
                "reason": reason
            }
        )


class StateManager:
    """Менеджер состояний workflow"""
    
    def __init__(self):
        self.workflows: Dict[str, WorkflowState] = {}
        self.logger = getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def create_workflow(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        quality_thresholds: Optional[QualityThresholds] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """Создать новый workflow"""
        async with self._lock:
            workflow_id = str(uuid.uuid4())
            
            context = WorkflowContext(
                workflow_id=workflow_id,
                input_data=input_data.copy(),
                config=config or {},
                quality_thresholds=quality_thresholds.dict() if quality_thresholds else QualityThresholds().dict(),
                user_preferences=user_preferences or {}
            )
            
            workflow_state = WorkflowState(workflow_id, context)
            self.workflows[workflow_id] = workflow_state
            
            self.logger.info(
                f"Created workflow {workflow_id}",
                extra={
                    "workflow_id": workflow_id,
                    "input_data_keys": list(input_data.keys())
                }
            )
            
            return workflow_state
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Получить состояние workflow"""
        return self.workflows.get(workflow_id)
    
    async def update_workflow(
        self,
        workflow_id: str,
        step: AgentStep,
        data: Dict[str, Any],
        agent_results: Dict[str, Any],
        quality_scores: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> StateSnapshot:
        """Обновить состояние workflow"""
        workflow_state = self.get_workflow(workflow_id)
        if not workflow_state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Создаем снимок состояния
        snapshot = workflow_state.create_snapshot(
            step=step,
            data=data,
            agent_results=agent_results,
            quality_scores=quality_scores,
            metadata=metadata
        )
        
        # Добавляем переход
        transition = workflow_state.add_transition(
            to_step=step,
            transition_type="step_completion",
            reason="Agent completed execution"
        )
        
        return snapshot
    
    async def create_execution_plan(
        self,
        workflow_id: str,
        steps: List[AgentStep],
        max_retries: Optional[Dict[AgentStep, int]] = None
    ) -> WorkflowExecutionPlan:
        """Создать план выполнения"""
        workflow_state = self.get_workflow(workflow_id)
        if not workflow_state:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_plan = WorkflowExecutionPlan(
            workflow_id=workflow_id,
            steps=steps,
            max_retries=max_retries or {}
        )
        
        workflow_state.execution_plan = execution_plan
        
        self.logger.info(
            f"Created execution plan for workflow {workflow_id}",
            extra={
                "workflow_id": workflow_id,
                "steps": [step.value for step in steps],
                "total_steps": len(steps)
            }
        )
        
        return execution_plan
    
    async def advance_workflow(self, workflow_id: str) -> bool:
        """Продвинуть workflow к следующему шагу"""
        workflow_state = self.get_workflow(workflow_id)
        if not workflow_state or not workflow_state.execution_plan:
            return False
        
        plan = workflow_state.execution_plan
        
        if plan.is_completed:
            workflow_state.update_status(WorkflowStatus.COMPLETED, "All steps completed")
            return False
        
        old_step = plan.current_step
        plan.advance_step()
        new_step = plan.current_step
        
        if new_step:
            workflow_state.add_transition(
                to_step=new_step,
                transition_type="advancement",
                from_step=old_step,
                reason="Advanced to next step"
            )
            
            return True
        
        return False
    
    async def rollback_workflow(
        self,
        workflow_id: str,
        target_step: AgentStep,
        reason: Optional[str] = None
    ) -> bool:
        """Откатить workflow к указанному шагу"""
        workflow_state = self.get_workflow(workflow_id)
        if not workflow_state or not workflow_state.execution_plan:
            return False
        
        plan = workflow_state.execution_plan
        
        if not plan.rollback_to_step(target_step):
            return False
        
        # Инвалидируем точки отката после целевого шага
        workflow_state.invalidate_rollback_points(target_step)
        
        workflow_state.add_transition(
            to_step=target_step,
            transition_type="rollback",
            reason=reason or "Quality threshold not met"
        )
        
        workflow_state.update_status(
            WorkflowStatus.ROLLED_BACK,
            f"Rolled back to {target_step}: {reason}"
        )
        
        self.logger.info(
            f"Rolled back workflow {workflow_id} to {target_step}",
            extra={
                "workflow_id": workflow_id,
                "target_step": target_step,
                "reason": reason
            }
        )
        
        return True
    
    def get_workflow_history(self, workflow_id: str) -> Dict[str, Any]:
        """Получить историю выполнения workflow"""
        workflow_state = self.get_workflow(workflow_id)
        if not workflow_state:
            return {}
        
        return {
            "workflow_id": workflow_id,
            "status": workflow_state.status.value,
            "current_step": workflow_state.current_step.value if workflow_state.current_step else None,
            "created_at": workflow_state.created_at.isoformat(),
            "updated_at": workflow_state.updated_at.isoformat(),
            "snapshots_count": len(workflow_state.snapshots),
            "transitions_count": len(workflow_state.transitions),
            "rollback_points_count": len([rp for rp in workflow_state.rollback_points if rp.is_available]),
            "execution_plan": workflow_state.execution_plan.dict() if workflow_state.execution_plan else None
        }
    
    async def cleanup_workflow(self, workflow_id: str):
        """Очистить workflow"""
        async with self._lock:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
                self.logger.info(f"Cleaned up workflow {workflow_id}")
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Получить информацию о всех workflow"""
        return [
            {
                "workflow_id": workflow_id,
                "status": state.status.value,
                "current_step": state.current_step.value if state.current_step else None,
                "created_at": state.created_at.isoformat(),
                "updated_at": state.updated_at.isoformat()
            }
            for workflow_id, state in self.workflows.items()
        ]
    
    def get_workflows_by_status(self, status: WorkflowStatus) -> List[WorkflowState]:
        """Получить workflow по статусу"""
        return [
            state for state in self.workflows.values()
            if state.status == status
        ]
