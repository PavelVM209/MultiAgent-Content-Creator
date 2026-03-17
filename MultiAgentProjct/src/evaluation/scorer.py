"""
Вспомогательные классы для подсчета оценок качества
"""

from typing import Dict, Any, Optional
from .quality_evaluator import EvaluationMetric


class QualityScorer:
    """
    Утилита для подсчета и агрегации оценок качества
    """
    
    @staticmethod
    def weighted_average(scores: Dict[EvaluationMetric, float], weights: Dict[EvaluationMetric, float]) -> float:
        """Рассчитать взвешенное среднее"""
        total_score = 0.0
        total_weight = 0.0
        
        for metric, score in scores.items():
            weight = weights.get(metric, 1.0)
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def calculate_improvement(old_scores: Dict[EvaluationMetric, float], 
                            new_scores: Dict[EvaluationMetric, float]) -> Dict[str, float]:
        """Рассчитать улучшение оценок"""
        improvements = {}
        
        for metric in EvaluationMetric:
            old_score = old_scores.get(metric, 0.0)
            new_score = new_scores.get(metric, 0.0)
            
            if old_score > 0:
                improvement = ((new_score - old_score) / old_score) * 100
                improvements[metric.value] = improvement
        
        return improvements
    
    @staticmethod
    def get_quality_level(score: float) -> str:
        """Получить уровень качества на основе оценки"""
        if score >= 0.9:
            return "Отлично"
        elif score >= 0.8:
            return "Хорошо"
        elif score >= 0.7:
            return "Удовлетворительно"
        elif score >= 0.6:
            return "Требует улучшения"
        else:
            return "Неудовлетворительно"
