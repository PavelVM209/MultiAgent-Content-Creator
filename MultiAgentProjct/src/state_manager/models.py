"""
Модели данных для State Manager
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Статусы workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"


class AgentStep(str, Enum):
    """Шаги агентов в workflow"""
    RESEARCH = "research"
    EXPLANATION = "explanation"
    SYNTHESIS = "synthesis"
    PRESENTATION = "presentation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_GENERATION = "video_generation"


class StateSnapshot(BaseModel):
    """Снимок состояния workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    step: AgentStep = Field(..., description="Текущий шаг")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время снимка")
    data: Dict[str, Any] = Field(default_factory=dict, description="Данные состояния")
    agent_results: Dict[str, Any] = Field(default_factory=dict, description="Результаты агентов")
    quality_scores: Dict[str, float] = Field(default_factory=dict, description="Оценки качества")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StateTransition(BaseModel):
    """Переход между состояниями"""
    from_step: Optional[AgentStep] = Field(None, description="Исходный шаг")
    to_step: AgentStep = Field(..., description="Целевой шаг")
    transition_type: str = Field(..., description="Тип перехода")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время перехода")
    reason: Optional[str] = Field(None, description="Причина перехода")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные перехода")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RollbackPoint(BaseModel):
    """Точка отката"""
    step: AgentStep = Field(..., description="Шаг для отката")
    snapshot: StateSnapshot = Field(..., description="Снимок состояния")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    is_available: bool = Field(default=True, description="Доступна ли точка отката")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WorkflowExecutionPlan(BaseModel):
    """План выполнения workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    steps: List[AgentStep] = Field(..., description="Последовательность шагов")
    current_step_index: int = Field(default=0, description="Индекс текущего шага")
    rollback_points: List[RollbackPoint] = Field(default_factory=list, description="Точки отката")
    max_retries: Dict[AgentStep, int] = Field(default_factory=dict, description="Максимальное количество попыток")
    retry_counts: Dict[AgentStep, int] = Field(default_factory=dict, description="Счетчики попыток")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @property
    def current_step(self) -> Optional[AgentStep]:
        """Получить текущий шаг"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    @property
    def is_completed(self) -> bool:
        """Завершен ли план"""
        return self.current_step_index >= len(self.steps)
    
    def advance_step(self):
        """Перейти к следующему шагу"""
        if not self.is_completed:
            self.current_step_index += 1
    
    def rollback_to_step(self, target_step: AgentStep) -> bool:
        """Откатить к указанному шагу"""
        try:
            step_index = self.steps.index(target_step)
            if step_index < self.current_step_index:
                self.current_step_index = step_index
                return True
        except ValueError:
            pass
        return False


class QualityThresholds(BaseModel):
    """Пороговые значения качества"""
    overall_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Общий порог")
    step_thresholds: Dict[AgentStep, float] = Field(default_factory=dict, description="Пороги по шагам")
    critical_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Критический порог")
    
    def should_rollback(self, step: AgentStep, score: float) -> bool:
        """Определить, нужно ли откатывать"""
        if score < self.critical_threshold:
            return True
        
        step_threshold = self.step_thresholds.get(step, self.overall_threshold)
        return score < step_threshold
    
    def should_retry(self, step: AgentStep, score: float) -> bool:
        """Определить, нужно ли повторить попытку"""
        step_threshold = self.step_thresholds.get(step, self.overall_threshold)
        return score < step_threshold and score >= self.critical_threshold


class WorkflowContext(BaseModel):
    """Контекст выполнения workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Входные данные")
    config: Dict[str, Any] = Field(default_factory=dict, description="Конфигурация")
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds, description="Пороги качества")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="Пользовательские настройки")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Время создания")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
