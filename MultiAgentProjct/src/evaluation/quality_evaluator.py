"""
Основной класс для оценки качества результатов агентов
"""

import asyncio
from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from state_manager.models import AgentStep


class EvaluationMetric(Enum):
    """Метрики оценки качества"""
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CLARITY = "clarity"
    STRUCTURE = "structure"
    CREATIVITY = "creativity"
    TECHNICAL_QUALITY = "technical_quality"


class QualityMetrics:
    """Метрики качества для конкретного результата"""
    
    def __init__(
        self,
        overall_score: float,
        metric_scores: Dict[EvaluationMetric, float],
        confidence: float,
        issues: List[str],
        suggestions: List[str]
    ):
        self.overall_score = overall_score
        self.metric_scores = metric_scores
        self.confidence = confidence
        self.issues = issues
        self.suggestions = suggestions
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь"""
        return {
            "overall_score": self.overall_score,
            "metric_scores": {metric.value: score for metric, score in self.metric_scores.items()},
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }


class EvaluationCriteria:
    """Критерии оценки для разных типов агентов"""
    
    def __init__(self):
        self.step_criteria = self._initialize_step_criteria()
    
    def _initialize_step_criteria(self) -> Dict[AgentStep, Dict[EvaluationMetric, float]]:
        """Инициализировать критерии для каждого шага"""
        return {
            AgentStep.RESEARCH: {
                EvaluationMetric.RELEVANCE: 0.3,
                EvaluationMetric.COMPLETENESS: 0.25,
                EvaluationMetric.ACCURACY: 0.25,
                EvaluationMetric.STRUCTURE: 0.2
            },
            AgentStep.EXPLANATION: {
                EvaluationMetric.CLARITY: 0.3,
                EvaluationMetric.COMPLETENESS: 0.25,
                EvaluationMetric.ACCURACY: 0.25,
                EvaluationMetric.RELEVANCE: 0.2
            },
            AgentStep.SYNTHESIS: {
                EvaluationMetric.STRUCTURE: 0.3,
                EvaluationMetric.RELEVANCE: 0.25,
                EvaluationMetric.COMPLETENESS: 0.25,
                EvaluationMetric.CLARITY: 0.2
            },
            AgentStep.PRESENTATION: {
                EvaluationMetric.STRUCTURE: 0.3,
                EvaluationMetric.CLARITY: 0.25,
                EvaluationMetric.CREATIVITY: 0.25,
                EvaluationMetric.RELEVANCE: 0.2
            },
            AgentStep.IMAGE_GENERATION: {
                EvaluationMetric.TECHNICAL_QUALITY: 0.4,
                EvaluationMetric.RELEVANCE: 0.3,
                EvaluationMetric.CREATIVITY: 0.3
            },
            AgentStep.AUDIO_GENERATION: {
                EvaluationMetric.TECHNICAL_QUALITY: 0.4,
                EvaluationMetric.CLARITY: 0.3,
                EvaluationMetric.RELEVANCE: 0.3
            },
            AgentStep.VIDEO_GENERATION: {
                EvaluationMetric.TECHNICAL_QUALITY: 0.35,
                EvaluationMetric.STRUCTURE: 0.25,
                EvaluationMetric.RELEVANCE: 0.2,
                EvaluationMetric.CREATIVITY: 0.2
            }
        }
    
    def get_criteria(self, step: AgentStep) -> Dict[EvaluationMetric, float]:
        """Получить критерии для шага"""
        return self.step_criteria.get(step, {
            EvaluationMetric.RELEVANCE: 0.25,
            EvaluationMetric.COMPLETENESS: 0.25,
            EvaluationMetric.ACCURACY: 0.25,
            EvaluationMetric.CLARITY: 0.25
        })


class QualityEvaluator:
    """
    Основной класс для оценки качества результатов агентов
    
    Использует различные метрики и подходы для комплексной оценки
    """
    
    def __init__(self, criteria: Optional[EvaluationCriteria] = None):
        self.criteria = criteria or EvaluationCriteria()
        self.logger = getLogger(__name__)
    
    async def evaluate_result(
        self,
        step: AgentStep,
        result_data: Any,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> QualityMetrics:
        """
        Оценить качество результата агента
        
        Args:
            step: Шаг workflow
            result_data: Результат выполнения агента
            input_data: Исходные входные данные
            context: Дополнительный контекст
            
        Returns:
            QualityMetrics: Метрики качества
        """
        self.logger.info(f"Evaluating quality for step {step}")
        
        try:
            # Получаем критерии для шага
            step_criteria = self.criteria.get_criteria(step)
            
            # Оцениваем каждую метрику
            metric_scores = {}
            for metric, weight in step_criteria.items():
                score = await self._evaluate_metric(
                    metric, step, result_data, input_data, context
                )
                metric_scores[metric] = score
            
            # Рассчитываем общую оценку
            overall_score = self._calculate_overall_score(metric_scores, step_criteria)
            
            # Определяем проблемы и предложения
            issues, suggestions = await self._analyze_quality(
                metric_scores, step, result_data
            )
            
            # Рассчитываем уверенность в оценке
            confidence = self._calculate_confidence(metric_scores, result_data)
            
            return QualityMetrics(
                overall_score=overall_score,
                metric_scores=metric_scores,
                confidence=confidence,
                issues=issues,
                suggestions=suggestions
            )
            
        except Exception as e:
            self.logger.error(f"Error evaluating quality for {step}: {str(e)}", exc_info=True)
            
            # Возвращаем минимальную оценку при ошибке
            return QualityMetrics(
                overall_score=0.0,
                metric_scores={},
                confidence=0.0,
                issues=[f"Evaluation error: {str(e)}"],
                suggestions=[]
            )
    
    async def _evaluate_metric(
        self,
        metric: EvaluationMetric,
        step: AgentStep,
        result_data: Any,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Оценить конкретную метрику"""
        
        if metric == EvaluationMetric.RELEVANCE:
            return await self._evaluate_relevance(step, result_data, input_data)
        elif metric == EvaluationMetric.COMPLETENESS:
            return await self._evaluate_completeness(step, result_data, input_data)
        elif metric == EvaluationMetric.ACCURACY:
            return await self._evaluate_accuracy(step, result_data, input_data)
        elif metric == EvaluationMetric.CLARITY:
            return await self._evaluate_clarity(step, result_data)
        elif metric == EvaluationMetric.STRUCTURE:
            return await self._evaluate_structure(step, result_data)
        elif metric == EvaluationMetric.CREATIVITY:
            return await self._evaluate_creativity(step, result_data, input_data)
        elif metric == EvaluationMetric.TECHNICAL_QUALITY:
            return await self._evaluate_technical_quality(step, result_data)
        
        return 0.5  # Значение по умолчанию
    
    async def _evaluate_relevance(
        self,
        step: AgentStep,
        result_data: Any,
        input_data: Dict[str, Any]
    ) -> float:
        """Оценить релевантность результата"""
        if not isinstance(result_data, dict):
            return 0.0
        
        # Извлекаем ключевые слова из входных данных
        input_text = " ".join(str(v) for v in input_data.values())
        input_keywords = set(input_text.lower().split())
        
        # Извлекаем ключевые слова из результата
        if isinstance(result_data.get("data"), str):
            result_text = result_data["data"]
        elif isinstance(result_data.get("summary"), str):
            result_text = result_data["summary"]
        else:
            result_text = str(result_data)
        
        result_keywords = set(result_text.lower().split())
        
        # Рассчитываем пересечение ключевых слов
        if not input_keywords:
            return 0.8  # Если нет ключевых слов, даем среднюю оценку
        
        intersection = input_keywords.intersection(result_keywords)
        relevance_score = len(intersection) / len(input_keywords)
        
        return min(relevance_score * 1.2, 1.0)  # Немного усиливаем оценку
    
    async def _evaluate_completeness(
        self,
        step: AgentStep,
        result_data: Any,
        input_data: Dict[str, Any]
    ) -> float:
        """Оценить полноту результата"""
        if not isinstance(result_data, dict):
            return 0.3
        
        # Базовые поля, которые должны быть в результатах
        required_fields = {
            AgentStep.RESEARCH: ["search_results", "summary", "key_points"],
            AgentStep.EXPLANATION: ["content", "examples", "key_concepts"],
            AgentStep.SYNTHESIS: ["synthesized_content", "connections"],
            AgentStep.PRESENTATION: ["slides", "structure"],
            AgentStep.IMAGE_GENERATION: ["images", "descriptions"],
            AgentStep.AUDIO_GENERATION: ["audio_segments", "duration"],
            AgentStep.VIDEO_GENERATION: ["video_scenes", "timeline"]
        }
        
        step_fields = required_fields.get(step, ["data"])
        present_fields = sum(1 for field in step_fields if field in result_data and result_data[field])
        
        completeness_score = present_fields / len(step_fields)
        
        # Дополнительные баллы за объем контента
        if "data" in result_data and isinstance(result_data["data"], (str, list)):
            content_size = len(result_data["data"])
            size_bonus = min(content_size / 1000, 0.2)  # Максимум 0.2 бонуса
            completeness_score += size_bonus
        
        return min(completeness_score, 1.0)
    
    async def _evaluate_accuracy(
        self,
        step: AgentStep,
        result_data: Any,
        input_data: Dict[str, Any]
    ) -> float:
        """Оценить точность результата"""
        # Это упрощенная оценка точности
        # В реальной системе здесь может быть проверка фактов, валидация данных и т.д.
        
        if not isinstance(result_data, dict):
            return 0.5
        
        accuracy_score = 0.7  # Базовая оценка
        
        # Проверяем наличие источников (для исследовательских шагов)
        if step == AgentStep.RESEARCH and "sources" in result_data:
            sources = result_data["sources"]
            if isinstance(sources, list) and len(sources) > 0:
                accuracy_score += 0.2
        
        # Проверяем confidence score если он есть
        if "confidence_score" in result_data:
            confidence = result_data["confidence_score"]
            if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
                accuracy_score = confidence * 0.3 + accuracy_score * 0.7
        
        return min(accuracy_score, 1.0)
    
    async def _evaluate_clarity(
        self,
        step: AgentStep,
        result_data: Any
    ) -> float:
        """Оценить ясность изложения"""
        if not isinstance(result_data, dict):
            return 0.4
        
        # Извлекаем текстовый контент
        text_content = ""
        for key in ["summary", "content", "data", "description"]:
            if key in result_data and isinstance(result_data[key], str):
                text_content += result_data[key] + " "
        
        if not text_content:
            return 0.5
        
        # Простые метрики ясности
        sentences = text_content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Идеальная длина предложения 15-25 слов
        length_score = 1.0 - min(abs(avg_sentence_length - 20) / 20, 1.0)
        
        # Наличие структуры (списки, заголовки)
        structure_indicators = sum(1 for indicator in ["-", "*", "1.", "##", "**"] if indicator in text_content)
        structure_score = min(structure_indicators / 5, 1.0)
        
        clarity_score = (length_score * 0.6 + structure_score * 0.4)
        
        return min(clarity_score, 1.0)
    
    async def _evaluate_structure(
        self,
        step: AgentStep,
        result_data: Any
    ) -> float:
        """Оценить структуру результата"""
        if not isinstance(result_data, dict):
            return 0.3
        
        structure_score = 0.0
        
        # Наличие ключевых полей структуры
        structure_fields = {
            "title": 0.2,
            "sections": 0.2,
            "summary": 0.2,
            "order": 0.2,
            "hierarchy": 0.2
        }
        
        for field, weight in structure_fields.items():
            if field in result_data:
                structure_score += weight
        
        # Для презентаций проверяем структуру слайдов
        if step == AgentStep.PRESENTATION and "slides" in result_data:
            slides = result_data["slides"]
            if isinstance(slides, list) and len(slides) > 0:
                slide_structure_score = 0.5
                for slide in slides:
                    if isinstance(slide, dict) and "title" in slide and "content" in slide:
                        slide_structure_score += 0.1
                structure_score = min(structure_score + slide_structure_score, 1.0)
        
        return min(structure_score, 1.0)
    
    async def _evaluate_creativity(
        self,
        step: AgentStep,
        result_data: Any,
        input_data: Dict[str, Any]
    ) -> float:
        """Оценить креативность результата"""
        # Упрощенная оценка креативности на основе разнообразия контента
        
        if not isinstance(result_data, dict):
            return 0.4
        
        creativity_score = 0.5  # Базовая оценка
        
        # Проверяем разнообразие форматов
        formats_present = 0
        for key in ["images", "videos", "audio", "interactive", "animations"]:
            if key in result_data:
                formats_present += 1
        
        if formats_present > 0:
            creativity_score += min(formats_present * 0.1, 0.3)
        
        # Проверяем уникальность контента (упрощенно)
        if "data" in result_data and isinstance(result_data["data"], str):
            unique_words = len(set(result_data["data"].lower().split()))
            total_words = len(result_data["data"].split())
            if total_words > 0:
                uniqueness_ratio = unique_words / total_words
                creativity_score += uniqueness_ratio * 0.2
        
        return min(creativity_score, 1.0)
    
    async def _evaluate_technical_quality(
        self,
        step: AgentStep,
        result_data: Any
    ) -> float:
        """Оценить техническое качество"""
        if not isinstance(result_data, dict):
            return 0.3
        
        tech_score = 0.6  # Базовая оценка
        
        # Проверяем технические метрики
        tech_fields = {
            "resolution": 0.1,
            "duration": 0.1,
            "format": 0.1,
            "size": 0.1,
            "quality_metrics": 0.2
        }
        
        for field, weight in tech_fields.items():
            if field in result_data:
                tech_score += weight
        
        # Проверяем отсутствие ошибок
        if "errors" in result_data:
            errors = result_data["errors"]
            if isinstance(errors, list):
                error_penalty = min(len(errors) * 0.1, 0.5)
                tech_score -= error_penalty
        
        return max(min(tech_score, 1.0), 0.0)
    
    def _calculate_overall_score(
        self,
        metric_scores: Dict[EvaluationMetric, float],
        criteria: Dict[EvaluationMetric, float]
    ) -> float:
        """Рассчитать общую оценку качества"""
        overall_score = 0.0
        total_weight = 0.0
        
        for metric, score in metric_scores.items():
            weight = criteria.get(metric, 0.25)
            overall_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            overall_score /= total_weight
        
        return round(overall_score, 3)
    
    async def _analyze_quality(
        self,
        metric_scores: Dict[EvaluationMetric, float],
        step: AgentStep,
        result_data: Any
    ) -> Tuple[List[str], List[str]]:
        """Проанализировать качество и выявить проблемы/предложения"""
        issues = []
        suggestions = []
        
        # Анализируем каждую метрику
        for metric, score in metric_scores.items():
            if score < 0.5:
                if metric == EvaluationMetric.RELEVANCE:
                    issues.append("Низкая релевантность результата входным данным")
                    suggestions.append("Улучшить соответствие содержания исходному запросу")
                elif metric == EvaluationMetric.COMPLETENESS:
                    issues.append("Результат неполный, отсутствуют важные компоненты")
                    suggestions.append("Добавить недостающую информацию и детали")
                elif metric == EvaluationMetric.ACCURACY:
                    issues.append("Возможны неточности в представленных данных")
                    suggestions.append("Проверить факты и добавить источники")
                elif metric == EvaluationMetric.CLARITY:
                    issues.append("Содержание недостаточно ясно и структурировано")
                    suggestions.append("Улучшить структуру и ясность изложения")
                elif metric == EvaluationMetric.STRUCTURE:
                    issues.append("Слабая организация контента")
                    suggestions.append("Добавить четкую структуру с заголовками и разделами")
        
        return issues, suggestions
    
    def _calculate_confidence(
        self,
        metric_scores: Dict[EvaluationMetric, float],
        result_data: Any
    ) -> float:
        """Рассчитать уверенность в оценке"""
        if not metric_scores:
            return 0.0
        
        # Уверенность на основе количества оцененных метрик
        metrics_count = len(metric_scores)
        base_confidence = min(metrics_count / 4, 1.0)  # Максимум 4 метрики для базовой уверенности
        
        # Уверенность на основе качества данных
        if isinstance(result_data, dict):
            data_richness = len(result_data) / 10  # Чем больше данных, тем выше уверенность
            data_confidence = min(data_richness, 0.3)
        else:
            data_confidence = 0.1
        
        # Уверенность на основе стабильности оценок
        if len(metric_scores) > 1:
            scores = list(metric_scores.values())
            score_std = max(scores) - min(scores)
            stability_confidence = max(0, 1.0 - score_std)
        else:
            stability_confidence = 0.5
        
        total_confidence = (base_confidence * 0.5 + data_confidence * 0.2 + stability_confidence * 0.3)
        
        return round(min(total_confidence, 1.0), 3)
