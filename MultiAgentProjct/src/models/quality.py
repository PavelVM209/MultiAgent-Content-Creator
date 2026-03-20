"""
Модели данных для системы контроля качества
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QualityMetricType(str, Enum):
    """Типы метрик качества"""
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    STRUCTURE = "structure"
    TIMING = "timing"
    VISUAL_QUALITY = "visual_quality"
    AUDIO_QUALITY = "audio_quality"
    SYNCHRONIZATION = "synchronization"


class ValidationLevel(str, Enum):
    """Уровни валидации"""
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


class QualityMetric(BaseModel):
    """Метрика качества"""
    metric_type: QualityMetricType = Field(..., description="Тип метрики")
    name: str = Field(..., description="Название метрики")
    value: float = Field(..., ge=0.0, le=1.0, description="Значение метрики")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Пороговое значение")
    weight: float = Field(default=1.0, ge=0.0, description="Вес метрики")
    passed: bool = Field(..., description="Пройдена ли метрика")
    description: str = Field(default="", description="Описание метрики")
    issues: List[str] = Field(default_factory=list, description="Обнаруженные проблемы")
    suggestions: List[str] = Field(default_factory=list, description="Рекомендации")


class QualityResult(BaseModel):
    """Результат оценки качества"""
    agent_name: str = Field(..., description="Имя агента")
    step_name: str = Field(..., description="Название шага")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Общая оценка")
    passed: bool = Field(..., description="Пройдена ли проверка")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Пороговое значение")
    metrics: Dict[QualityMetricType, QualityMetric] = Field(..., description="Метрики")
    validation_level: ValidationLevel = Field(default=ValidationLevel.NORMAL, description="Уровень валидации")
    processing_time: float = Field(..., description="Время оценки")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время оценки")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Метаданные")
    
    def get_failed_metrics(self) -> List[QualityMetric]:
        """Получить проваленные метрики"""
        return [metric for metric in self.metrics.values() if not metric.passed]
    
    def get_critical_issues(self) -> List[str]:
        """Получить критические проблемы"""
        issues = []
        for metric in self.get_failed_metrics():
            if metric.value < metric.threshold * 0.5:  # Менее 50% от порога
                issues.extend(metric.issues)
        return issues


class QualityThreshold(BaseModel):
    """Пороговые значения качества для агента"""
    agent_name: str = Field(..., description="Имя агента")
    overall_threshold: float = Field(..., ge=0.0, le=1.0, description="Общий порог")
    metric_thresholds: Dict[QualityMetricType, float] = Field(..., description="Пороги по метрикам")
    validation_level: ValidationLevel = Field(default=ValidationLevel.NORMAL, description="Уровень валидации")
    custom_rules: Dict[str, Any] = Field(default_factory=dict, description="Пользовательские правила")


class QualityMetrics(BaseModel):
    """Агрегированные метрики качества"""
    agent_name: str
    total_evaluations: int = Field(default=0, description="Всего оценок")
    passed_evaluations: int = Field(default=0, description="Прошедших оценок")
    failed_evaluations: int = Field(default=0, description="Проваленных оценок")
    average_score: float = Field(default=0.0, description="Средняя оценка")
    average_processing_time: float = Field(default=0.0, description="Среднее время оценки")
    metric_averages: Dict[QualityMetricType, float] = Field(default_factory=dict, description="Средние по метрикам")
    last_evaluation_time: Optional[datetime] = Field(None, description="Последняя оценка")
    
    @property
    def pass_rate(self) -> float:
        """Процент прохождения"""
        if self.total_evaluations == 0:
            return 0.0
        return self.passed_evaluations / self.total_evaluations
    
    @property
    def failure_rate(self) -> float:
        """Процент провалов"""
        if self.total_evaluations == 0:
            return 0.0
        return self.failed_evaluations / self.total_evaluations


class QualityRule(BaseModel):
    """Правило валидации качества"""
    rule_id: str = Field(..., description="ID правила")
    name: str = Field(..., description="Название правила")
    description: str = Field(..., description="Описание правила")
    metric_type: QualityMetricType = Field(..., description="Тип метрики")
    condition: str = Field(..., description="Условие правила")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Порог")
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$", description="Строгость")
    enabled: bool = Field(default=True, description="Активно ли правило")
    custom_logic: Optional[str] = Field(None, description="Пользовательская логика")


class QualityProfile(BaseModel):
    """Профиль качества для типа контента"""
    profile_id: str = Field(..., description="ID профиля")
    name: str = Field(..., description="Название профиля")
    description: str = Field(default="", description="Описание")
    content_type: str = Field(..., description="Тип контента")
    thresholds: Dict[str, QualityThreshold] = Field(..., description="Пороги для агентов")
    rules: List[QualityRule] = Field(default_factory=list, description="Правила валидации")
    validation_level: ValidationLevel = Field(default=ValidationLevel.NORMAL, description="Уровень валидации")
    enabled: bool = Field(default=True, description="Активен ли профиль")


class QualityReport(BaseModel):
    """Отчет о качестве для workflow"""
    workflow_id: str = Field(..., description="ID workflow")
    execution_id: str = Field(..., description="ID выполнения")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Общая оценка")
    passed: bool = Field(..., description="Пройдена ли проверка")
    agent_results: Dict[str, QualityResult] = Field(..., description="Результаты по агентам")
    step_summary: Dict[str, Dict[str, Any]] = Field(..., description="Сводка по шагам")
    critical_issues: List[str] = Field(default_factory=list, description="Критические проблемы")
    recommendations: List[str] = Field(default_factory=list, description="Рекомендации")
    processing_time: float = Field(..., description="Общее время оценки")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время отчета")
    
    def get_weakest_agent(self) -> Optional[str]:
        """Получить агент с самой низкой оценкой"""
        if not self.agent_results:
            return None
        
        weakest_agent = min(
            self.agent_results.items(),
            key=lambda x: x[1].overall_score
        )
        return weakest_agent[0]
    
    def get_improvement_areas(self) -> List[str]:
        """Получить области для улучшения"""
        areas = []
        for agent_name, result in self.agent_results.items():
            failed_metrics = result.get_failed_metrics()
            if failed_metrics:
                metric_names = [metric.name for metric in failed_metrics]
                areas.append(f"{agent_name}: {', '.join(metric_names)}")
        return areas


class QualityTrend(BaseModel):
    """Тренд качества во времени"""
    agent_name: str = Field(..., description="Имя агента")
    time_period: str = Field(..., description="Период (day/week/month)")
    data_points: List[Dict[str, Any]] = Field(..., description="Точки данных")
    trend_direction: str = Field(..., pattern="^(improving|declining|stable)$", description="Направление тренда")
    trend_strength: float = Field(..., ge=0.0, le=1.0, description="Сила тренда")
    average_score: float = Field(..., ge=0.0, le=1.0, description="Средняя оценка")
    score_variance: float = Field(..., ge=0.0, description="Дисперсия оценок")


class QualityAlert(BaseModel):
    """Оповещение о качестве"""
    alert_id: str = Field(..., description="ID оповещения")
    agent_name: str = Field(..., description="Имя агента")
    workflow_id: str = Field(..., description="ID workflow")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$", description="Строгость")
    message: str = Field(..., description="Сообщение")
    metrics_involved: List[QualityMetricType] = Field(..., description="Затронутые метрики")
    current_score: float = Field(..., ge=0.0, le=1.0, description="Текущая оценка")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Порог")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время")
    acknowledged: bool = Field(default=False, description="Подтверждено ли")
    resolved: bool = Field(default=False, description="Решено ли")
    resolution_notes: Optional[str] = Field(None, description="Заметки о решении")


class QualityConfig(BaseModel):
    """Конфигурация системы качества"""
    enabled: bool = Field(default=True, description="Включена ли система")
    validation_level: ValidationLevel = Field(default=ValidationLevel.NORMAL, description="Уровень валидации")
    evaluation_timeout: int = Field(default=30, description="Таймаут оценки")
    parallel_evaluation: bool = Field(default=True, description="Параллельная оценка")
    cache_results: bool = Field(default=True, description="Кэширование результатов")
    cache_ttl: int = Field(default=3600, description="TTL кэша")
    alert_thresholds: Dict[str, float] = Field(default_factory=dict, description="Пороги для оповещений")
    custom_validators: Dict[str, str] = Field(default_factory=dict, description="Пользовательские валидаторы")
    reporting_enabled: bool = Field(default=True, description="Включена отчетность")
    trend_analysis_enabled: bool = Field(default=True, description="Включен анализ трендов")
