"""
Модели данных для workflow
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
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class StepStatus(str, Enum):
    """Статусы шагов workflow"""
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class WorkflowStep(BaseModel):
    """Модель шага workflow"""
    step_id: str = Field(..., description="ID шага")
    step_name: str = Field(..., description="Название шага")
    agent_name: str = Field(..., description="Имя агента")
    order: int = Field(..., description="Порядок выполнения")
    status: StepStatus = Field(default=StepStatus.WAITING, description="Статус шага")
    input_data: Optional[Any] = Field(None, description="Входные данные")
    output_data: Optional[Any] = Field(None, description="Выходные данные")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    start_time: Optional[datetime] = Field(None, description="Время начала")
    end_time: Optional[datetime] = Field(None, description="Время окончания")
    processing_time: Optional[float] = Field(None, description="Время выполнения")
    quality_score: Optional[float] = Field(None, description="Оценка качества")
    retry_count: int = Field(default=0, description="Количество попыток")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    
    @property
    def duration(self) -> Optional[float]:
        """Длительность выполнения в секундах"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return self.processing_time


class WorkflowContext(BaseModel):
    """Контекст выполнения workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    topic: str = Field(..., description="Основная тема")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="Статус")
    steps: List[WorkflowStep] = Field(default_factory=list, description="Шаги workflow")
    current_step_index: int = Field(default=0, description="Текущий индекс шага")
    start_time: Optional[datetime] = Field(None, description="Время начала")
    end_time: Optional[datetime] = Field(None, description="Время окончания")
    total_processing_time: Optional[float] = Field(None, description="Общее время выполнения")
    overall_quality_score: Optional[float] = Field(None, description="Общая оценка качества")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    
    def add_step(self, step: WorkflowStep):
        """Добавить шаг в workflow"""
        self.steps.append(step)
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Получить текущий шаг"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_step_by_name(self, step_name: str) -> Optional[WorkflowStep]:
        """Получить шаг по названию"""
        for step in self.steps:
            if step.step_name == step_name:
                return step
        return None
    
    def get_completed_steps(self) -> List[WorkflowStep]:
        """Получить завершенные шаги"""
        return [step for step in self.steps if step.status == StepStatus.COMPLETED]
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Получить неудачные шаги"""
        return [step for step in self.steps if step.status == StepStatus.FAILED]
    
    @property
    def is_completed(self) -> bool:
        """Завершен ли workflow"""
        return self.status == WorkflowStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Завершен ли с ошибкой"""
        return self.status == WorkflowStatus.FAILED
    
    @property
    def progress_percentage(self) -> float:
        """Процент выполнения"""
        if not self.steps:
            return 0.0
        completed_steps = len(self.get_completed_steps())
        return (completed_steps / len(self.steps)) * 100


class WorkflowState(BaseModel):
    """Состояние workflow для сохранения"""
    workflow_id: str
    current_step: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    """Результат выполнения workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    success: bool = Field(..., description="Успешность выполнения")
    status: WorkflowStatus = Field(..., description="Финальный статус")
    final_result: Optional[Any] = Field(None, description="Финальный результат")
    steps_summary: List[Dict[str, Any]] = Field(..., description="Сводка по шагам")
    total_processing_time: float = Field(..., description="Общее время выполнения")
    overall_quality_score: Optional[float] = Field(None, description="Общая оценка качества")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время завершения")
    
    # Дополнительные поля для совместимости с кодом
    final_data: Optional[Any] = Field(None, description="Финальные данные")
    agent_results: Dict[str, Any] = Field(default_factory=dict, description="Результаты агентов")
    quality_scores: Dict[str, float] = Field(default_factory=dict, description="Оценки качества агентов")
    total_time: float = Field(..., description="Общее время выполнения")
    steps_completed: int = Field(default=0, description="Количество выполненных шагов")
    total_steps: int = Field(default=0, description="Общее количество шагов")
    rollbacks_performed: int = Field(default=0, description="Количество выполненных откатов")
    completion_rate: float = Field(default=0.0, description="Процент выполнения")
    average_quality: float = Field(default=0.0, description="Среднее качество")
    error: Optional[str] = Field(None, description="Ошибка выполнения")


class WorkflowConfig(BaseModel):
    """Конфигурация workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    name: str = Field(..., description="Название workflow")
    description: str = Field(default="", description="Описание")
    steps_order: List[str] = Field(..., description="Порядок шагов")
    timeout_per_step: Dict[str, int] = Field(default_factory=dict, description="Таймауты для шагов")
    quality_thresholds: Dict[str, float] = Field(default_factory=dict, description="Пороги качества")
    retry_config: Dict[str, int] = Field(default_factory=dict, description="Конфигурация повторов")
    enabled: bool = Field(default=True, description="Активен ли workflow")


class RollbackDecision(BaseModel):
    """Решение об откате"""
    rollback_needed: bool = Field(..., description="Нужен ли откат")
    target_step: Optional[str] = Field(None, description="Целевой шаг для отката")
    reason: str = Field(..., description="Причина отката")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность в решении")
    alternative_actions: List[str] = Field(default_factory=list, description="Альтернативные действия")


class WorkflowMetrics(BaseModel):
    """Метрики workflow"""
    workflow_id: str
    total_executions: int = Field(default=0, description="Всего выполнений")
    successful_executions: int = Field(default=0, description="Успешных выполнений")
    failed_executions: int = Field(default=0, description="Неудачных выполнений")
    average_processing_time: float = Field(default=0.0, description="Среднее время выполнения")
    average_quality_score: float = Field(default=0.0, description="Средняя оценка качества")
    rollback_count: int = Field(default=0, description="Количество откатов")
    step_success_rates: Dict[str, float] = Field(default_factory=dict, description="Успешность по шагам")
    last_execution_time: Optional[datetime] = Field(None, description="Последнее выполнение")
    
    @property
    def success_rate(self) -> float:
        """Процент успешных выполнений"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    @property
    def failure_rate(self) -> float:
        """Процент неудачных выполнений"""
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions
