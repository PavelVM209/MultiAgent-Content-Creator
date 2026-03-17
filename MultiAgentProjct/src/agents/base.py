"""
Базовый интерфейс для всех агентов мультиагентной системы
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Dict, Optional

from src.models.agents import (
    AgentConfig, 
    AgentResult, 
    AgentError, 
    ValidationResult, 
    TimeoutConfig,
    AgentMetrics
)


class BaseAgent(ABC):
    """
    Базовый абстрактный класс для всех агентов системы.
    
    Определяет стандартный интерфейс и шаблон выполнения для всех агентов.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Инициализация агента
        
        Args:
            config: Конфигурация агента
        """
        self.config = config or self._get_default_config()
        self.logger = getLogger(f"{__name__}.{self.__class__.__name__}")
        self.metrics = AgentMetrics(agent_name=self.config.agent_name)
        self._setup_logger()
    
    @abstractmethod
    async def validate_input(self, data: Any) -> ValidationResult:
        """
        Валидация входных данных
        
        Args:
            data: Входные данные для валидации
            
        Returns:
            ValidationResult: Результат валидации с оценкой и проблемами
        """
        pass
    
    @abstractmethod
    async def process_data(self, validated_data: Any) -> Any:
        """
        Основная обработка данных агентом
        
        Args:
            validated_data: Валидированные входные данные
            
        Returns:
            Any: Результат обработки
        """
        pass
    
    @abstractmethod
    async def validate_output(self, result: Any) -> ValidationResult:
        """
        Валидация выходных данных
        
        Args:
            result: Результат обработки для валидации
            
        Returns:
            ValidationResult: Результат валидации
        """
        pass
    
    @abstractmethod
    def get_quality_thresholds(self) -> Dict[str, float]:
        """
        Получить пороговые значения качества для агента
        
        Returns:
            Dict[str, float]: Словарь с пороговыми значениями
        """
        pass
    
    async def execute(self, input_data: Any) -> AgentResult:
        """
        Основной метод выполнения агента - шаблонный метод
        
        Args:
            input_data: Входные данные
            
        Returns:
            AgentResult: Результат выполнения агента
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            self.logger.info(
                f"Starting execution {execution_id}", 
                extra={"execution_id": execution_id, "agent": self.config.agent_name}
            )
            
            # 1. Валидация входных данных
            input_validation = await self._validate_with_timeout(
                input_data, 
                self.get_timeout_config().input_validation
            )
            
            if not input_validation.valid:
                return self._create_error_result(
                    execution_id,
                    "ValidationError",
                    f"Input validation failed: {input_validation.issues}",
                    start_time,
                    input_validation=input_validation
                )
            
            # 2. Обработка данных
            validated_data = await self._prepare_input_data(input_data, input_validation)
            processed_data = await self._process_with_timeout(
                validated_data,
                self.get_timeout_config().processing
            )
            
            # 3. Валидация выходных данных
            output_validation = await self._validate_output_with_timeout(
                processed_data,
                self.get_timeout_config().output_validation
            )
            
            if not output_validation.valid:
                return self._create_error_result(
                    execution_id,
                    "ValidationError", 
                    f"Output validation failed: {output_validation.issues}",
                    start_time,
                    input_validation=input_validation,
                    output_validation=output_validation
                )
            
            # 4. Формирование успешного результата
            result = await self._create_success_result(
                execution_id,
                processed_data,
                start_time,
                input_validation,
                output_validation
            )
            
            # 5. Обновление метрик
            self._update_metrics(result)
            
            self.logger.info(
                f"Successfully completed execution {execution_id}",
                extra={
                    "execution_id": execution_id,
                    "agent": self.config.agent_name,
                    "processing_time": result.processing_time,
                    "quality_score": result.quality_score
                }
            )
            
            return result
            
        except asyncio.TimeoutError:
            error_result = self._create_error_result(
                execution_id,
                "TimeoutError",
                f"Execution timeout after {self.get_timeout_config().total}s",
                start_time
            )
            self._update_metrics(error_result)
            return error_result
            
        except Exception as e:
            self.logger.error(
                f"Error in execution {execution_id}: {str(e)}",
                extra={"execution_id": execution_id, "agent": self.config.agent_name},
                exc_info=True
            )
            
            error_result = self._create_error_result(
                execution_id,
                type(e).__name__,
                str(e),
                start_time,
                stack_trace=self._get_stack_trace()
            )
            self._update_metrics(error_result)
            return error_result
    
    async def _validate_with_timeout(self, data: Any, timeout: int) -> ValidationResult:
        """Валидация с таймаутом"""
        try:
            return await asyncio.wait_for(
                self.validate_input(data),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return ValidationResult(
                valid=False,
                score=0.0,
                issues=[f"Validation timeout after {timeout}s"],
                confidence=0.0
            )
    
    async def _process_with_timeout(self, data: Any, timeout: int) -> Any:
        """Обработка с таймаутом"""
        try:
            return await asyncio.wait_for(
                self.process_data(data),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Processing timeout after {timeout}s")
    
    async def _validate_output_with_timeout(self, data: Any, timeout: int) -> ValidationResult:
        """Валидация выходных данных с таймаутом"""
        try:
            return await asyncio.wait_for(
                self.validate_output(data),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return ValidationResult(
                valid=False,
                score=0.0,
                issues=[f"Output validation timeout after {timeout}s"],
                confidence=0.0
            )
    
    async def _create_success_result(
        self,
        execution_id: str,
        data: Any,
        start_time: float,
        input_validation: ValidationResult,
        output_validation: ValidationResult
    ) -> AgentResult:
        """Создание успешного результата"""
        processing_time = time.time() - start_time
        quality_score = await self._calculate_quality_score(data, input_validation, output_validation)
        
        return AgentResult(
            success=True,
            data=data,
            processing_time=processing_time,
            quality_score=quality_score,
            input_validation=input_validation,
            output_validation=output_validation,
            agent_version=self.config.version,
            execution_id=execution_id,
            metadata=self._get_metadata(data)
        )
    
    def _create_error_result(
        self,
        execution_id: str,
        error_type: str,
        message: str,
        start_time: float,
        input_validation: Optional[ValidationResult] = None,
        output_validation: Optional[ValidationResult] = None,
        stack_trace: Optional[str] = None
    ) -> AgentResult:
        """Создание результата с ошибкой"""
        processing_time = time.time() - start_time
        
        error = AgentError(
            agent_name=self.config.agent_name,
            error_type=error_type,
            message=message,
            retry_count=0,
            can_retry=self._can_retry_error(error_type),
            stack_trace=stack_trace
        )
        
        return AgentResult(
            success=False,
            error=error,
            processing_time=processing_time,
            input_validation=input_validation,
            output_validation=output_validation,
            agent_version=self.config.version,
            execution_id=execution_id,
            metadata={}
        )
    
    async def _calculate_quality_score(
        self,
        data: Any,
        input_validation: ValidationResult,
        output_validation: ValidationResult
    ) -> float:
        """
        Расчет общей оценки качества
        
        Args:
            data: Результат обработки
            input_validation: Результат валидации входных данных
            output_validation: Результат валидации выходных данных
            
        Returns:
            float: Общая оценка качества (0-1)
        """
        # Базовые компоненты качества
        input_score = input_validation.score if input_validation else 0.0
        output_score = output_validation.score if output_validation else 0.0
        
        # Специфичная для агента оценка
        agent_score = await self._calculate_agent_specific_quality(data)
        
        # Взвешенное среднее
        weights = self._get_quality_weights()
        total_score = (
            input_score * weights['input'] +
            output_score * weights['output'] +
            agent_score * weights['agent_specific']
        )
        
        return round(total_score, 3)
    
    def _can_retry_error(self, error_type: str) -> bool:
        """Определить, можно ли повторить попытку при ошибке"""
        retryable_errors = {
            'TimeoutError',
            'ConnectionError',
            'APIError',
            'TemporaryError'
        }
        return error_type in retryable_errors
    
    def _update_metrics(self, result: AgentResult):
        """Обновление метрик агента"""
        self.metrics.total_executions += 1
        self.metrics.last_execution_time = result.timestamp
        
        if result.success:
            self.metrics.successful_executions += 1
            if result.quality_score is not None:
                # Обновление среднего качества
                total_quality = (
                    self.metrics.average_quality_score * 
                    (self.metrics.successful_executions - 1) + 
                    result.quality_score
                )
                self.metrics.average_quality_score = (
                    total_quality / self.metrics.successful_executions
                )
        else:
            self.metrics.failed_executions += 1
            if result.error:
                error_count = self.metrics.error_types.get(result.error.error_type, 0)
                self.metrics.error_types[result.error.error_type] = error_count + 1
        
        # Обновление среднего времени выполнения
        total_time = (
            self.metrics.average_processing_time * 
            (self.metrics.total_executions - 1) + 
            result.processing_time
        )
        self.metrics.average_processing_time = (
            total_time / self.metrics.total_executions
        )
    
    def _setup_logger(self):
        """Настройка логгера для агента"""
        self.logger.setLevel(getLogger().level)
        # Можно добавить дополнительные настройки логгера
    
    def _get_stack_trace(self) -> str:
        """Получить stack trace для отладки"""
        import traceback
        return traceback.format_exc()
    
    # Методы для переопределения в дочерних классах
    
    def _get_default_config(self) -> AgentConfig:
        """Получить конфигурацию по умолчанию"""
        return AgentConfig(
            agent_name=self.__class__.__name__,
            version="1.0.0"
        )
    
    def get_timeout_config(self) -> TimeoutConfig:
        """Получить конфигурацию таймаутов"""
        return TimeoutConfig(
            total=self.config.timeout
        )
    
    async def _prepare_input_data(self, input_data: Any, validation: ValidationResult) -> Any:
        """Подготовка входных данных после валидации"""
        return input_data
    
    def _get_quality_weights(self) -> Dict[str, float]:
        """Получить веса для расчета качества"""
        return {
            'input': 0.2,
            'output': 0.3,
            'agent_specific': 0.5
        }
    
    async def _calculate_agent_specific_quality(self, data: Any) -> float:
        """
        Расчет специфичной для агента оценки качества.
        Переопределяется в дочерних классах.
        
        Args:
            data: Результат обработки
            
        Returns:
            float: Оценка качества (0-1)
        """
        return 1.0  # По умолчанию максимальная оценка
    
    def _get_metadata(self, data: Any) -> Dict[str, Any]:
        """Получить метаданные для результата"""
        return {
            'agent_name': self.config.agent_name,
            'agent_version': self.config.version,
            'config': self.config.dict(exclude={'custom_params'}),
            'processing_timestamp': time.time()
        }
    
    # Utility методы
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья агента
        
        Returns:
            Dict[str, Any]: Статус здоровья агента
        """
        return {
            'agent_name': self.config.agent_name,
            'version': self.config.version,
            'enabled': self.config.enabled,
            'metrics': self.metrics.dict(),
            'status': 'healthy' if self.config.enabled else 'disabled'
        }
    
    def get_metrics(self) -> AgentMetrics:
        """Получить текущие метрики агента"""
        return self.metrics
    
    def reset_metrics(self):
        """Сбросить метрики агента"""
        self.metrics = AgentMetrics(agent_name=self.config.agent_name)
