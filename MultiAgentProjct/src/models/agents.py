"""
Модели данных для агентов
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentError(BaseModel):
    """Модель ошибки агента"""
    agent_name: str = Field(..., description="Имя агента")
    error_type: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    retry_count: int = Field(default=0, description="Количество попыток повтора")
    can_retry: bool = Field(default=True, description="Можно ли повторить попытку")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время ошибки")
    stack_trace: Optional[str] = Field(None, description="Stack trace для отладки")


class ValidationResult(BaseModel):
    """Результат валидации"""
    valid: bool = Field(..., description="Валидны ли данные")
    score: float = Field(..., ge=0.0, le=1.0, description="Оценка валидации (0-1)")
    issues: List[str] = Field(default_factory=list, description="Обнаруженные проблемы")
    suggestions: List[str] = Field(default_factory=list, description="Рекомендации по исправлению")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Уверенность в валидации")


class AgentConfig(BaseModel):
    """Конфигурация агента"""
    agent_name: str = Field(..., description="Имя агента")
    version: str = Field(default="1.0.0", description="Версия агента")
    enabled: bool = Field(default=True, description="Активен ли агент")
    timeout: int = Field(default=60, description="Таймаут выполнения в секундах")
    max_retries: int = Field(default=3, description="Максимальное количество попыток")
    retry_delay: float = Field(default=1.0, description="Задержка между попытками в секундах")
    cache_enabled: bool = Field(default=True, description="Включено ли кэширование")
    cache_ttl: int = Field(default=3600, description="TTL кэша в секундах")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные параметры")


class TimeoutConfig(BaseModel):
    """Конфигурация таймаутов"""
    input_validation: int = Field(default=5, description="Таймаут валидации входных данных")
    processing: int = Field(default=60, description="Таймаут основной обработки")
    output_validation: int = Field(default=5, description="Таймаут валидации выходных данных")
    total: int = Field(default=300, description="Общий таймаут выполнения")


class AgentResult(BaseModel):
    """Результат выполнения агента"""
    success: bool = Field(..., description="Успешно ли выполнено")
    data: Optional[Any] = Field(None, description="Результативные данные")
    error: Optional[AgentError] = Field(None, description="Ошибка выполнения")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные выполнения")
    processing_time: float = Field(..., description="Время выполнения в секундах")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Оценка качества")
    input_validation: Optional[ValidationResult] = Field(None, description="Результат валидации входных данных")
    output_validation: Optional[ValidationResult] = Field(None, description="Результат валидации выходных данных")
    agent_version: str = Field(default="1.0.0", description="Версия агента")
    execution_id: str = Field(..., description="ID выполнения")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время выполнения")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentMetrics(BaseModel):
    """Метрики производительности агента"""
    agent_name: str
    total_executions: int = Field(default=0, description="Всего выполнений")
    successful_executions: int = Field(default=0, description="Успешных выполнений")
    failed_executions: int = Field(default=0, description="Неудачных выполнений")
    average_processing_time: float = Field(default=0.0, description="Среднее время выполнения")
    average_quality_score: float = Field(default=0.0, description="Средняя оценка качества")
    last_execution_time: Optional[datetime] = Field(None, description="Время последнего выполнения")
    error_types: Dict[str, int] = Field(default_factory=dict, description="Статистика ошибок по типам")
    
    @property
    def success_rate(self) -> float:
        """Рассчитать процент успешных выполнений"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    @property
    def failure_rate(self) -> float:
        """Рассчитать процент неудачных выполнений"""
        if self.total_executions == 0:
            return 0.0
        return self.failed_executions / self.total_executions


# Специализированные модели для разных типов агентов

class ResearchInput(BaseModel):
    """Входные данные для ResearchAgent"""
    topic: str = Field(..., min_length=1, max_length=200, description="Тема для исследования")
    language: str = Field(default="ru", description="Язык поиска")
    max_results: int = Field(default=10, ge=1, le=50, description="Максимальное количество результатов")
    search_depth: str = Field(default="basic", pattern="^(basic|advanced|comprehensive)$", description="Глубина поиска")


class ResearchResult(BaseModel):
    """Результат выполнения ResearchAgent"""
    topic: str
    search_results: List[Dict[str, Any]]
    summary: str
    key_points: List[str]
    sources: List[str]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_metadata: Dict[str, Any]


class ExplanationInput(BaseModel):
    """Входные данные для ExplanationAgent"""
    topic: str
    research_data: ResearchResult
    target_audience: str = Field(default="general", pattern="^(general|student|expert)$")
    explanation_style: str = Field(default="educational", pattern="^(simple|detailed|technical)$")
    include_examples: bool = Field(default=True)
    language: str = Field(default="ru")


class ExplanationResult(BaseModel):
    """Результат выполнения ExplanationAgent"""
    topic: str
    explanation: str
    examples: List[str]
    analogies: List[str]
    key_concepts: List[str]
    difficulty_level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    estimated_reading_time: int  # в минутах
    clarity_score: float = Field(..., ge=0.0, le=1.0)


class SynthesisInput(BaseModel):
    """Входные данные для SynthesisAgent"""
    topic: str
    research_result: ResearchResult
    explanation_result: ExplanationResult
    synthesis_type: str = Field(default="comprehensive", pattern="^(brief|comprehensive|detailed)$")
    target_format: str = Field(default="structured", pattern="^(structured|narrative|bulleted)$")


class SynthesisResult(BaseModel):
    """Результат выполнения SynthesisAgent"""
    topic: str
    final_description: str
    key_insights: List[str]
    practical_applications: List[str]
    related_concepts: List[str]
    summary_points: List[str]
    coherence_score: float = Field(..., ge=0.0, le=1.0)
    completeness_score: float = Field(..., ge=0.0, le=1.0)


class Slide(BaseModel):
    """Модель слайда презентации"""
    slide_number: int
    title: str
    content: str
    speaker_notes: str
    duration_estimate: int  # в секундах
    visual_type: str = Field(..., pattern="^(image|chart|diagram|text)$")
    visual_description: str


class PresentationInput(BaseModel):
    """Входные данные для PresentationAgent"""
    topic: str
    synthesis_result: SynthesisResult
    target_duration: int = Field(default=60, ge=30, le=180)
    max_slides: int = Field(default=5, ge=3, le=10)
    min_slides: int = Field(default=4, ge=2, le=8)
    presentation_style: str = Field(default="educational", pattern="^(educational|professional|casual)$")


class PresentationResult(BaseModel):
    """Результат выполнения PresentationAgent"""
    topic: str
    slides: List[Slide]
    total_duration: int
    slide_timings: List[int]
    narrative_flow: str
    visual_suggestions: List[str]
    structure_score: float = Field(..., ge=0.0, le=1.0)
