"""
ExplanationAgent - агент для создания расширенных объяснений на основеresearch данных
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import re

from .base import BaseAgent
from src.models.agents import ValidationResult, AgentConfig


class ExplanationAgent(BaseAgent):
    """
    Агент для создания подробных объяснений и разъяснений
    
    Задачи:
    - Анализ research данных
    - Создание структурированных объяснений
    - Адаптация контента под разную аудиторию
    - Генерация примеров и аналогий
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_name="ExplanationAgent",
                version="1.0.0",
                timeout=90,
                max_retries=3,
                custom_params={
                    "target_audience": "general",
                    "explanation_style": "educational",
                    "include_examples": True,
                    "include_analogies": True,
                    "difficulty_level": "intermediate",
                    "max_length": 2000
                }
            )
        super().__init__(config)
    
    async def validate_input(self, data: Any) -> ValidationResult:
        """Валидация входных данных"""
        issues = []
        
        if isinstance(data, dict):
            # Проверяем наличие необходимых полей
            required_fields = ["topic", "research_data", "structured_results"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
            
            # Проверяем качество research данных
            research_data = data.get("research_data", {})
            if not research_data.get("summary"):
                issues.append("Отсутствует summary из research данных")
            
            if not research_data.get("key_points"):
                issues.append("Отсутствуют ключевые точки из research данных")
            
        elif hasattr(data, 'topic'):
            # Простой объект с topic
            if not data.topic:
                issues.append("Topic не указан")
        else:
            issues.append("Некорректный формат входных данных")
        
        score = 1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.25)
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Убедитесь что данные содержат результаты исследования",
                "Проверьте наличие темы и ключевых точек"
            ] if issues else [],
            confidence=0.8 if len(issues) == 0 else 0.5
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Основная обработка - создание объяснений"""
        self.logger.info("Starting explanation generation")
        
        try:
            # Извлекаем и подготавливаем данные
            topic, research_data, metadata = self._extract_input_data(validated_data)
            
            # Анализируем целевую аудиторию и стиль
            audience = self.config.custom_params.get("target_audience", "general")
            style = self.config.custom_params.get("explanation_style", "educational")
            
            # Создаем основное содержание
            main_content = await self._generate_main_content(topic, research_data, audience, style)
            
            # Генерируем примеры
            examples = await self._generate_examples(topic, research_data, audience)
            
            # Создаем аналогии
            analogies = await self._generate_analogies(topic, research_data, audience)
            
            # Извлекаем ключевые концепции
            key_concepts = await self._extract_key_concepts(research_data)
            
            # Создаем структуру объяснения
            structure = await self._create_explanation_structure(topic, main_content, examples)
            
            # Определяем уровень сложности
            difficulty = self._determine_difficulty_level(research_data, audience)
            
            # Рассчитываем примерное время чтения
            reading_time = self._estimate_reading_time(main_content)
            
            result_data = {
                "topic": topic,
                "content": main_content,
                "examples": examples,
                "analogies": analogies,
                "key_concepts": key_concepts,
                "structure": structure,
                "difficulty_level": difficulty,
                "target_audience": audience,
                "explanation_style": style,
                "estimated_reading_time": reading_time,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "source_type": "research_based",
                    "content_length": len(main_content),
                    "examples_count": len(examples),
                    "concepts_count": len(key_concepts)
                }
            }
            
            self.logger.info(f"Explanation generated for '{topic}' with {len(examples)} examples")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error during explanation generation: {str(e)}")
            raise
    
    async def validate_output(self, result: Any) -> ValidationResult:
        """Валидация выходных данных"""
        if not isinstance(result, dict):
            return ValidationResult(
                valid=False,
                score=0.0,
                issues=["Результат должен быть словарем"],
                suggestions=["Проверьте формат выходных данных"],
                confidence=0.0
            )
        
        required_fields = ["topic", "content", "examples", "key_concepts", "structure"]
        missing_fields = [field for field in required_fields if field not in result]
        
        issues = []
        
        if missing_fields:
            issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        
        # Проверяем качество контента
        content = result.get("content", "")
        if len(content) < 100:
            issues.append("Содержание объяснения слишком короткое")
        
        if len(content) > self.config.custom_params.get("max_length", 2000):
            issues.append("Содержание объяснения слишком длинное")
        
        # Проверяем наличие примеров
        examples = result.get("examples", [])
        if len(examples) < 2:
            issues.append("Недостаточно примеров для хорошего объяснения")
        
        # Проверяем структуру
        structure = result.get("structure", {})
        required_structure_parts = ["introduction", "main_content", "conclusion"]
        missing_structure = [part for part in required_structure_parts if part not in structure]
        if missing_structure:
            issues.append(f"Отсутствуют части структуры: {', '.join(missing_structure)}")
        
        score = min(1.0, max(0.0, 1.0 - len(issues) * 0.2))
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Расширьте содержание и добавьте больше примеров",
                "Улучшите структуру объяснения"
            ] if issues else [],
            confidence=0.8
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "overall": 0.75,
            "content_quality": 0.7,
            "examples_relevance": 0.6,
            "structure_completeness": 0.8,
            "clarity_score": 0.7
        }
    
    def _extract_input_data(self, data: Any) -> tuple:
        """Извлечение topic, research_data и metadata из входных данных"""
        if isinstance(data, dict):
            topic = data.get("topic", "").strip()
            research_data = data.get("research_data", {})
            structured_results = data.get("structured_results", {})
            
            # Если research_data пустой, используем прямые поля
            if not research_data:
                research_data = {
                    "summary": data.get("summary", ""),
                    "key_points": data.get("key_points", []),
                    "sources": data.get("sources", [])
                }
            
            metadata = data.get("metadata", {})
            
        elif hasattr(data, 'topic'):
            topic = str(data.topic).strip()
            research_data = getattr(data, 'research_data', {})
            structured_results = getattr(data, 'structured_results', {})
            metadata = getattr(data, 'metadata', {})
        else:
            topic = str(data).strip()
            research_data = {}
            structured_results = {}
            metadata = {}
        
        return topic, research_data, metadata
    
    async def _generate_main_content(self, topic: str, research_data: Dict[str, Any], 
                                   audience: str, style: str) -> str:
        """Генерация основного содержания объяснения"""
        summary = research_data.get("summary", "")
        key_points = research_data.get("key_points", [])
        
        # Адаптируем язык под аудиторию
        if audience == "beginner":
            prefix = f"Давайте простыми словами разберем, что такое {topic}. "
            explanation_style = "используя понятные аналогии и избегая сложной терминологии"
        elif audience == "expert":
            prefix = f"Рассмотрим ключевые аспекты {topic} с точки зрения современных подходов. "
            explanation_style = "с акцентом на технические детали и специфику"
        else:  # general
            prefix = f"{topic} - это важная тема, которую стоит понять. "
            explanation_style = "сбалансированно, доступно для широкой аудитории"
        
        # Формируем основное содержание
        content_parts = [prefix]
        
        # Добавляем информацию из summary
        if summary:
            # Упрощаем и адаптируем summary
            adapted_summary = self._adapt_summary_for_explanation(summary, audience)
            content_parts.append(adapted_summary)
        
        # Добавляем разбор ключевых точек
        if key_points:
            content_parts.append("\n\nОсновные аспекты:")
            for i, point in enumerate(key_points[:4], 1):  # Максимум 4 точки
                explained_point = self._explain_key_point(point, audience, style)
                content_parts.append(f"{i}. {explained_point}")
        
        # Добавляем заключение в зависимости от стиля
        if style == "educational":
            conclusion = f"\n\nПонимание {topic} помогает лучше ориентироваться в современных технологиях и применениях этой области."
        elif style == "technical":
            conclusion = f"\n\nТехническая реализация {topic} требует внимательного изучения всех описанных аспектов."
        else:  # simple
            conclusion = f"\n\nТаким образом, {topic} представляет собой интересную и полезную область знаний."
        
        content_parts.append(conclusion)
        
        main_content = "".join(content_parts)
        
        # Ограничиваем длину
        max_length = self.config.custom_params.get("max_length", 2000)
        if len(main_content) > max_length:
            main_content = main_content[:max_length].rsplit(' ', 1)[0] + "..."
        
        return main_content
    
    def _adapt_summary_for_explanation(self, summary: str, audience: str) -> str:
        """Адаптация summary для объяснения"""
        # Убираем технические детали для начинающих
        if audience == "beginner":
            # Заменяем сложные термины
            summary = re.sub(r'(?:комплексный|системный|интегрированный)', 'важный', summary, flags=re.IGNORECASE)
            summary = re.sub(r'(?:методология|подход|концепция)', 'идея', summary, flags=re.IGNORECASE)
        
        # Для экспертов сохраняем технический язык
        elif audience == "expert":
            summary = re.sub(r'(?:важный|основной|ключевой)', 'фундаментальный', summary, flags=re.IGNORECASE)
        
        return summary
    
    def _explain_key_point(self, point: str, audience: str, style: str) -> str:
        """Объяснение отдельной ключевой точки"""
        # Базовые объяснения для разных аудиторий
        if audience == "beginner":
            return f"{point}. Это означает, что на практике мы видим конкретные результаты и применения."
        elif audience == "expert":
            return f"{point}. Это имеет прямое влияние на архитектуру и implementation стратегии."
        else:  # general
            return f"{point}. Этот аспект важен для понимания общей картины."
    
    async def _generate_examples(self, topic: str, research_data: Dict[str, Any], 
                               audience: str) -> List[str]:
        """Генерация примеров"""
        examples = []
        
        # Извлекаем информацию для примеров
        sources = research_data.get("sources", [])
        key_points = research_data.get("key_points", [])
        
        # Базовые примеры в зависимости от темы
        if "технологии" in topic.lower() or "technology" in topic.lower():
            examples = [
                f"Применение {topic} в повседневной жизни: умные устройства, автоматизация процессов",
                f"{topic} в бизнесе: повышение эффективности, оптимизация ресурсов",
                f"Образовательные примеры: изучение {topic} через практические проекты"
            ]
        elif "наука" in topic.lower() or "science" in topic.lower():
            examples = [
                f"Научные исследования в области {topic}: лабораторные эксперименты и наблюдения",
                f"Практическое применение научных знаний о {topic} в промышленности",
                f"Исторические открытия: как развивались представления о {topic}"
            ]
        else:
            # Общие примеры
            examples = [
                f"Реальный случай использования {topic} в современной практике",
                f"Как {topic} помогает решать повседневные задачи",
                f"Интересный факт о {topic}, который показывает ее важность"
            ]
        
        # Адаптируем примеры под аудиторию
        if audience == "beginner":
            examples = [f"Представьте, что {ex.lower().replace('применение ', '')}" for ex in examples[:2]]
        elif audience == "expert":
            if len(examples) > 2:
                examples.extend([
                    f"Продвинутый пример: техническая реализация {topic} вdistributed системах",
                    f"Кейс study: крупномасштабное внедрение {topic} в enterprise среде"
                ])
        
        return examples[:4]  # Максимум 4 примера
    
    async def _generate_analogies(self, topic: str, research_data: Dict[str, Any], 
                                audience: str) -> List[str]:
        """Генерация аналогий"""
        analogies = []
        
        # Базовые аналогии для разных типов тем
        if "система" in topic.lower() or "system" in topic.lower():
            analogies = [
                f"Как автомобиль, {topic} состоит из взаимосвязанных частей, работающих вместе",
                f"Подобно оркестру, {topic} требует гармоничной работы всех компонентов"
            ]
        elif "процесс" in topic.lower() or "process" in topic.lower():
            analogies = [
                f"{topic} похож на рецепт: нужно следовать шагам и использовать правильные ингредиенты",
                f"Как строительство дома, {topic} требует планирования и последовательности действий"
            ]
        elif "данные" in topic.lower() or "data" in topic.lower():
            analogies = [
                f"{topic} - это как библиотека: информация организована и доступна для использования",
                f"Подобно базовому дневнику, {topic} хранит важную информацию в структурированном виде"
            ]
        else:
            # Универсальные аналогии
            analogies = [
                f"Как изучение нового языка, {topic} требует практики и постепенного освоения",
                f"{topic} можно сравнить с путешествием: открываем новое и учимся применять на практике"
            ]
        
        # Адаптируем под аудиторию
        if audience == "beginner":
            analogies = [f"{an}. Это помогает понять основную идею." for an in analogies[:2]]
        
        return analogies
    
    async def _extract_key_concepts(self, research_data: Dict[str, Any]) -> List[str]:
        """Извлечение ключевых концепций"""
        concepts = []
        
        # Из key_points
        key_points = research_data.get("key_points", [])
        for point in key_points:
            # Извлекаем существительные и термины
            words = re.findall(r'\b[А-Яа-я]{3,}\b', point)
            concepts.extend([word for word in words if len(word) > 4])
        
        # Из summary
        summary = research_data.get("summary", "")
        summary_words = re.findall(r'\b[А-Я][а-я]{4,}\b', summary)
        concepts.extend(summary_words)
        
        # Убираем дубликаты и общие слова
        common_words = {"также", "которые", "поскольку", "поэтому", "благодаря", "Проанализированы", "Выделены"}
        unique_concepts = []
        for concept in concepts:
            if concept not in unique_concepts and concept not in common_words:
                unique_concepts.append(concept)
        
        # Ограничиваем количество
        return unique_concepts[:8]
    
    async def _create_explanation_structure(self, topic: str, content: str, 
                                          examples: List[str]) -> Dict[str, str]:
        """Создание структуры объяснения"""
        return {
            "introduction": f"Введение в тему {topic}",
            "main_content": "Основное содержание с разбором ключевых аспектов",
            "examples": "Практические примеры для понимания",
            "conclusion": f"Заключение: важность понимания {topic}",
            "flow": f"Интро → Основы → Примеры → Итоги"
        }
    
    def _determine_difficulty_level(self, research_data: Dict[str, Any], audience: str) -> str:
        """Определение уровня сложности"""
        base_difficulty = {
            "beginner": "beginner",
            "general": "intermediate", 
            "expert": "advanced"
        }.get(audience, "intermediate")
        
        # Анализируем сложность текста
        summary = research_data.get("summary", "")
        
        # Если есть сложные термины, повышаем сложность
        complex_terms = ["методология", "архитектура", "интеграция", "оптимизация"]
        has_complex_terms = any(term.lower() in summary.lower() for term in complex_terms)
        
        if has_complex_terms and audience != "beginner":
            return "advanced"
        elif has_complex_terms:
            return "intermediate"
        
        return base_difficulty
    
    def _estimate_reading_time(self, content: str) -> int:
        """Оценка времени чтения в минутах"""
        # Средняя скорость чтения - 200 слов в минуту
        # Средняя длина слова в русском - 6 символов
        word_count = len(content) / 6
        return max(1, int(word_count / 200))
