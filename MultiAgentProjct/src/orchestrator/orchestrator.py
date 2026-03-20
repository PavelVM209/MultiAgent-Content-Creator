"""
Главный оркестратор мультиагентной системы
"""

import asyncio
import time
from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional, Type

from src.agents.base import BaseAgent
from src.state_manager import StateManager, WorkflowState, AgentStep, WorkflowStatus
from src.state_manager.models import QualityThresholds
from src.models.agents import AgentResult
from src.evaluation import QualityEvaluator


class OrchestrationConfig:
    """Конфигурация оркестрации"""
    
    def __init__(
        self,
        max_total_retries: int = 3,
        max_rollbacks: int = 2,
        quality_thresholds: Optional[QualityThresholds] = None,
        enable_parallel_execution: bool = False,
        timeout_per_step: int = 300,
        enable_checkpointing: bool = True
    ):
        self.max_total_retries = max_total_retries
        self.max_rollbacks = max_rollbacks
        self.quality_thresholds = quality_thresholds or QualityThresholds()
        self.enable_parallel_execution = enable_parallel_execution
        self.timeout_per_step = timeout_per_step
        self.enable_checkpointing = enable_checkpointing


class WorkflowResult:
    """Результат выполнения workflow"""
    
    def __init__(
        self,
        workflow_id: str,
        success: bool,
        final_data: Dict[str, Any],
        agent_results: Dict[str, AgentResult],
        quality_scores: Dict[str, float],
        total_time: float,
        steps_completed: int,
        total_steps: int,
        rollbacks_performed: int = 0,
        error: Optional[str] = None
    ):
        self.workflow_id = workflow_id
        self.success = success
        self.final_data = final_data
        self.agent_results = agent_results
        self.quality_scores = quality_scores
        self.total_time = total_time
        self.steps_completed = steps_completed
        self.total_steps = total_steps
        self.rollbacks_performed = rollbacks_performed
        self.error = error
        self.timestamp = datetime.utcnow()
    
    @property
    def completion_rate(self) -> float:
        """Процент выполнения"""
        if self.total_steps == 0:
            return 0.0
        return self.steps_completed / self.total_steps
    
    @property
    def average_quality(self) -> float:
        """Средняя оценка качества"""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores.values()) / len(self.quality_scores)


class Orchestrator:
    """
    Главный оркестратор мультиагентной системы
    
    Управляет выполнением workflow, координирует работу агентов,
    обрабатывает ошибки и принимает решения об откате
    """
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        self.config = config or OrchestrationConfig()
        self.state_manager = StateManager()
        self.quality_evaluator = QualityEvaluator()
        self.agents: Dict[AgentStep, BaseAgent] = {}
        self.logger = getLogger(__name__)
        self._running_workflows: Dict[str, asyncio.Task] = {}
        
        # Определение стандартной последовательности шагов
        self.default_workflow_steps = [
            AgentStep.RESEARCH,
            AgentStep.EXPLANATION,
            AgentStep.SYNTHESIS,
            AgentStep.PRESENTATION,
            AgentStep.IMAGE_GENERATION,
            AgentStep.AUDIO_GENERATION,
            AgentStep.VIDEO_GENERATION
        ]
    
    def register_agent(self, step: AgentStep, agent: BaseAgent):
        """Зарегистрировать агент для шага"""
        self.agents[step] = agent
        self.logger.info(f"Registered agent {agent.__class__.__name__} for step {step}")
    
    async def execute_workflow(
        self,
        input_data: Dict[str, Any],
        custom_steps: Optional[List[AgentStep]] = None,
        workflow_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Выполнить workflow
        
        Args:
            input_data: Входные данные
            custom_steps: Кастомная последовательность шагов
            workflow_id: ID workflow (если None, сгенерируется автоматически)
            
        Returns:
            WorkflowResult: Результат выполнения
        """
        workflow_id = workflow_id or f"workflow_{int(time.time())}"
        steps = custom_steps or self.default_workflow_steps
        
        self.logger.info(f"Starting workflow {workflow_id} with {len(steps)} steps")
        
        try:
            # Создаем workflow
            workflow_state = await self.state_manager.create_workflow(
                input_data=input_data,
                quality_thresholds=self.config.quality_thresholds
            )
            
            # Создаем план выполнения
            await self.state_manager.create_execution_plan(
                workflow_id=workflow_state.workflow_id,
                steps=steps,
                max_retries={step: self.config.max_total_retries for step in steps}
            )
            
            workflow_state.update_status(WorkflowStatus.RUNNING, "Workflow started")
            
            # Выполняем workflow
            result = await self._execute_workflow_steps(workflow_state, steps)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in workflow {workflow_id}: {str(e)}", exc_info=True)
            
            workflow_state = self.state_manager.get_workflow(workflow_id)
            if workflow_state:
                workflow_state.update_status(WorkflowStatus.FAILED, str(e))
            
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                final_data={},
                agent_results={},
                quality_scores={},
                total_time=0.0,
                steps_completed=0,
                total_steps=len(steps),
                error=str(e)
            )
    
    async def _execute_workflow_steps(
        self,
        workflow_state: WorkflowState,
        steps: List[AgentStep]
    ) -> WorkflowResult:
        """Выполнить шаги workflow"""
        start_time = time.time()
        workflow_id = workflow_state.workflow_id
        
        agent_results = {}
        quality_scores = {}
        rollbacks_performed = 0
        current_data = workflow_state.context.input_data.copy()
        
        for i, step in enumerate(steps):
            self.logger.info(f"Executing step {i+1}/{len(steps)}: {step}")
            
            try:
                # ПОПРАВКА: Подготовка данных для агентов ПЕРЕД выполнением
                input_for_step = current_data
                
                if step == AgentStep.EXPLANATION:
                    # Формируем правильные данные для ExplanationAgent
                    research_result = current_data if isinstance(current_data, dict) else {}
                    
                    input_for_step = {
                        "topic": research_result.get("topic", ""),
                        "research_data": {
                            "summary": research_result.get("summary", ""),
                            "key_points": research_result.get("key_points", []),
                            "sources": research_result.get("sources", [])
                        },
                        "structured_results": research_result.get("structured_results", {})
                    }
                    
                    self.logger.info(f"DEBUG: ExplanationAgent input_data keys: {list(input_for_step.keys())}")
                    self.logger.info(f"DEBUG: research_data keys: {list(input_for_step['research_data'].keys())}")
                    
                elif step == AgentStep.SYNTHESIS:
                    # ИСПРАВЛЕНИЕ: SynthesisAgent ожидает правильные research_data и explanation_data
                    if isinstance(current_data, dict):
                        # Берем research_data из ExplanationAgent результата и добавляем topic
                        research_data = current_data.get("research_data", {})
                        research_data["topic"] = current_data.get("topic", "")  # Добавляем topic в research_data
                        
                        # Формируем explanation_data из результата ExplanationAgent
                        # ExplanationAgent должен был выполнен и его результат должен быть в current_data
                        # Но current_data содержит результаты ExplanationAgent, а не входные данные
                        explanation_result = current_data  # Это уже результат ExplanationAgent
                        
                        explanation_data = {
                            "topic": explanation_result.get("topic", ""),
                            "content": explanation_result.get("content", ""),
                            "examples": explanation_result.get("examples", []),
                            "key_concepts": explanation_result.get("key_concepts", []),
                            "difficulty_level": explanation_result.get("difficulty_level", "intermediate"),
                            "target_audience": explanation_result.get("target_audience", "general"),
                            "explanation_style": explanation_result.get("explanation_style", "educational")
                        }
                        
                        input_for_step = {
                            "research_data": research_data,
                            "explanation_data": explanation_data
                        }
                        
                        # ОТЛАДКА: Печатаем прямо в консоль
                        print(f"🔍 DEBUG SynthesisAgent:")
                        print(f"   current_data keys: {list(current_data.keys())}")
                        print(f"   research_data keys: {list(research_data.keys())}")
                        print(f"   research_data has topic: {'topic' in research_data}")
                        print(f"   explanation_data keys: {list(explanation_data.keys())}")
                        print(f"   explanation_data has content: {'content' in explanation_data}")
                        print(f"   explanation_data content length: {len(explanation_data.get('content', ''))}")
                        print(f"   explanation_data content preview: {explanation_data.get('content', '')[:100]}...")
                
                elif step == AgentStep.PRESENTATION:
                    # ИСПРАВЛЕНИЕ: PresentationAgent ожидает synthesis_data и research_data
                    input_for_step = {
                        "synthesis_data": current_data.get("synthesis_data", {}),
                        "research_data": current_data.get("research_data", {})
                    }
                    
                    # ОТЛАДКА
                    print(f"🔍 DEBUG PresentationAgent:")
                    print(f"   synthesis_data keys: {list(input_for_step['synthesis_data'].keys())}")
                    print(f"   research_data keys: {list(input_for_step['research_data'].keys())}")
                
                # Выполняем шаг
                step_result = await self._execute_step_with_retry(
                    workflow_state, step, input_for_step
                )
                
                # Оцениваем качество результата
                quality_metrics = await self.quality_evaluator.evaluate_result(
                    step, step_result.data if step_result.success else {}, current_data
                )
                
                # Обновляем результат с оценкой качества
                if step_result.success:
                    step_result.quality_score = quality_metrics.overall_score
                
                if not step_result.success:
                    # Проверяем, нужно ли откатываться на основе качества
                    if await self._should_rollback(workflow_state, step, step_result, quality_metrics):
                        rollback_result = await self._perform_rollback(
                            workflow_state, step, quality_scores
                        )
                        if rollback_result:
                            rollbacks_performed += 1
                            # После отката прекращаем выполнение (не рекурсия)
                            break
                        else:
                            # Не удалось откатиться, завершаем с ошибкой
                            break
                    
                    # Не удалось выполнить шаг и откат не требуется/возможен
                    workflow_state.update_status(
                        WorkflowStatus.FAILED,
                        f"Step {step} failed: {step_result.error.message if step_result.error else 'Unknown error'}"
                    )
                    break
                
                # Проверяем качество даже при успешном выполнении
                if quality_metrics.overall_score < workflow_state.context.quality_thresholds.critical_threshold:
                    self.logger.warning(f"Step {step} quality too low: {quality_metrics.overall_score}")
                    if await self._should_rollback(workflow_state, step, step_result, quality_metrics):
                        rollback_result = await self._perform_rollback(
                            workflow_state, step, quality_scores
                        )
                        if rollback_result:
                            rollbacks_performed += 1
                            # После отката прекращаем выполнение
                            break
                
                # Шаг выполнен успешно
                agent_results[step.value] = step_result
                quality_scores[step.value] = quality_metrics.overall_score
                
                # Обновляем состояние
                await self.state_manager.update_workflow(
                    workflow_id,
                    step,
                    current_data,
                    agent_results,
                    quality_scores
                )
                
                # Создаем точку отката если включено
                if self.config.enable_checkpointing:
                    snapshot = workflow_state.snapshots[-1] if workflow_state.snapshots else None
                    if snapshot:
                        workflow_state.add_rollback_point(step, snapshot)
                
                # Обновляем данные для следующего шага с учетом типа агента
                if step == AgentStep.RESEARCH:
                    # ResearchAgent возвращает словарь с нужными полями
                    current_data = step_result.data if isinstance(step_result.data, dict) else {"result": step_result.data}
                elif step == AgentStep.EXPLANATION:
                    # ИСПРАВЛЕНИЕ: После ExplanationAgent сохраняем ЕГО результат для SynthesisAgent
                    # step_result.data содержит результат ExplanationAgent с content, examples и т.д.
                    explanation_result = step_result.data if isinstance(step_result.data, dict) else {}
                    
                    # Сохраняем результат ExplanationAgent с research_data для следующего шага
                    current_data = {
                        **explanation_result,  # Все поля от ExplanationAgent (content, examples, etc.)
                        "research_data": current_data.get("research_data", {}) if isinstance(current_data, dict) else {}  # research_data от ResearchAgent
                    }
                elif step == AgentStep.SYNTHESIS:
                    # Для SynthesisAgent передаем данные в правильном формате
                    synthesis_data = step_result.data if isinstance(step_result.data, dict) else {"result": step_result.data}
                    current_data = {
                        "synthesis_data": synthesis_data,  # Сохраняем результат synthesis
                        "research_data": current_data.get("research_data", {}) if isinstance(current_data, dict) else {},
                        "explanation_data": current_data.get("explanation_data", {}) if isinstance(current_data, dict) else {}
                    }
                elif step == AgentStep.PRESENTATION:
                    # ИСПРАВЛЕНИЕ: PresentationAgent ожидает synthesis_data и research_data
                    synthesis_result = step_result.data if isinstance(step_result.data, dict) else {}
                    
                    current_data = {
                        "synthesis_data": synthesis_result,
                        "research_data": current_data.get("research_data", {}) if isinstance(current_data, dict) else {}
                    }
                    
                    # ОТЛАДКА
                    print(f"🔍 DEBUG PresentationAgent:")
                    print(f"   synthesis_data keys: {list(synthesis_result.keys())}")
                    print(f"   research_data keys: {list(current_data.get('research_data', {}).keys())}")
                else:
                    current_data = step_result.data if isinstance(step_result.data, dict) else {"result": step_result.data}
                
                # Переходим к следующему шагу
                await self.state_manager.advance_workflow(workflow_id)
                
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout in step {step}")
                workflow_state.update_status(WorkflowStatus.FAILED, f"Timeout in step {step}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in step {step}: {str(e)}", exc_info=True)
                workflow_state.update_status(WorkflowStatus.FAILED, f"Error in step {step}: {str(e)}")
                break
        
        # Формируем результат
        total_time = time.time() - start_time
        steps_completed = len([s for s in steps if s.value in agent_results])
        
        if workflow_state.status not in [WorkflowStatus.FAILED, WorkflowStatus.PAUSED]:
            workflow_state.update_status(WorkflowStatus.COMPLETED, "All steps completed successfully")
            success = True
        else:
            success = workflow_state.status == WorkflowStatus.COMPLETED
        
        return WorkflowResult(
            workflow_id=workflow_id,
            success=success,
            final_data=current_data,
            agent_results=agent_results,
            quality_scores=quality_scores,
            total_time=total_time,
            steps_completed=steps_completed,
            total_steps=len(steps),
            rollbacks_performed=rollbacks_performed
        )
    
    async def _execute_step_with_retry(
        self,
        workflow_state: WorkflowState,
        step: AgentStep,
        input_data: Dict[str, Any]
    ) -> AgentResult:
        """Выполнить шаг с повторными попытками"""
        agent = self.agents.get(step)
        if not agent:
            raise ValueError(f"No agent registered for step {step}")
        
        max_retries = workflow_state.execution_plan.max_retries.get(step, self.config.max_total_retries)
        retry_count = workflow_state.execution_plan.retry_counts.get(step, 0)
        
        last_result = None
        
        while retry_count <= max_retries:
            try:
                self.logger.info(f"Executing {step}, attempt {retry_count + 1}/{max_retries + 1}")
                
                result = await asyncio.wait_for(
                    agent.execute(input_data),
                    timeout=self.config.timeout_per_step
                )
                
                if result.success:
                    # Сбрасываем счетчик попыток при успехе
                    workflow_state.execution_plan.retry_counts[step] = 0
                    return result
                else:
                    last_result = result
                    self.logger.warning(f"Step {step} failed, attempt {retry_count + 1}: {result.error.message if result.error else 'Unknown error'}")
                    
            except asyncio.TimeoutError:
                from src.models.agents import AgentError
                timeout_error = AgentError(
                    agent_name=agent.__class__.__name__,
                    error_type="timeout",
                    message=f"Timeout after {self.config.timeout_per_step}s",
                    details={"timeout_duration": self.config.timeout_per_step}
                )
                last_result = AgentResult(
                    success=False,
                    error=timeout_error,
                    execution_id=f"timeout_{int(time.time())}",
                    processing_time=self.config.timeout_per_step
                )
                self.logger.warning(f"Step {step} timeout, attempt {retry_count + 1}")
                
            except Exception as e:
                # Создаем правильный AgentError
                from src.models.agents import AgentError
                error_obj = AgentError(
                    agent_name=agent.__class__.__name__,
                    error_type="processing_error",
                    message=str(e),
                    details={"timestamp": time.time()}
                )
                last_result = AgentResult(
                    success=False,
                    error=error_obj,
                    execution_id=f"error_{int(time.time())}",
                    processing_time=0.0
                )
                self.logger.error(f"Step {step} error, attempt {retry_count + 1}: {str(e)}")
            
            retry_count += 1
            workflow_state.execution_plan.retry_counts[step] = retry_count
            
            # Небольшая задержка между попытками
            if retry_count <= max_retries:
                await asyncio.sleep(1.0 * retry_count)
        
        # Создаем правильный AgentError для финального результата
        from src.models.agents import AgentError
        final_error = AgentError(
            agent_name=agent.__class__.__name__,
            error_type="retry_exhausted",
            message="All retry attempts failed",
            details={"attempts": retry_count}
        )
        
        return last_result or AgentResult(
            success=False,
            error=final_error,
            execution_id=f"failed_{int(time.time())}",
            processing_time=0.0
        )
    
    async def _should_rollback(
        self,
        workflow_state: WorkflowState,
        step: AgentStep,
        result: AgentResult,
        quality_metrics=None
    ) -> bool:
        """Определить, нужно ли выполнять откат"""
        if not result.success:
            # Проверяем пороги качества
            if result.quality_score is not None:
                return workflow_state.context.quality_thresholds.should_rollback(step, result.quality_score)
        
        # Если переданы метрики качества, проверяем их
        if quality_metrics and hasattr(quality_metrics, 'overall_score'):
            return workflow_state.context.quality_thresholds.should_rollback(step, quality_metrics.overall_score)
        
        return False
    
    async def _perform_rollback(
        self,
        workflow_state: WorkflowState,
        failed_step: AgentStep,
        quality_scores: Dict[str, float]
    ) -> bool:
        """Выполнить откат"""
        if len(workflow_state.execution_plan.rollback_points) >= self.config.max_rollbacks:
            self.logger.warning(f"Max rollbacks ({self.config.max_rollbacks}) reached")
            return False
        
        # Находим последнюю точку отката
        rollback_point = workflow_state.get_latest_rollback_point()
        if not rollback_point:
            self.logger.warning("No rollback points available")
            return False
        
        # Определяем целевой шаг для отката
        target_step = rollback_point.step
        
        self.logger.info(f"Rolling back from {failed_step} to {target_step}")
        
        # Выполняем откат
        success = await self.state_manager.rollback_workflow(
            workflow_state.workflow_id,
            target_step,
            f"Quality threshold not met in {failed_step}"
        )
        
        return success
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Получить статус workflow"""
        return self.state_manager.get_workflow_history(workflow_id)
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Отменить workflow"""
        workflow_state = self.state_manager.get_workflow(workflow_id)
        if not workflow_state:
            return False
        
        # Отменяем задачу если она выполняется
        if workflow_id in self._running_workflows:
            task = self._running_workflows[workflow_id]
            task.cancel()
            del self._running_workflows[workflow_id]
        
        workflow_state.update_status(WorkflowStatus.FAILED, "Cancelled by user")
        return True
    
    async def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Очистить завершенные workflow"""
        current_time = datetime.utcnow()
        workflows_to_cleanup = []
        
        for workflow_id, workflow_state in self.state_manager.workflows.items():
            age_hours = (current_time - workflow_state.updated_at).total_seconds() / 3600
            
            if (workflow_state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED] and
                age_hours > max_age_hours):
                workflows_to_cleanup.append(workflow_id)
        
        for workflow_id in workflows_to_cleanup:
            await self.state_manager.cleanup_workflow(workflow_id)
            
        self.logger.info(f"Cleaned up {len(workflows_to_cleanup)} workflows")
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Получить активные workflow"""
        return self.state_manager.get_workflows_by_status(WorkflowStatus.RUNNING)
