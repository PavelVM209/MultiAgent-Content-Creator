"""
PresentationAgent - агент для создания презентаций на 1 минуту (4-5 слайдов)
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .base import BaseAgent
from models.agents import ValidationResult, AgentConfig


class PresentationAgent(BaseAgent):
    """
    Агент для создания презентаций
    
    Задачи:
    - Создание структуры презентации (4-5 слайдов)
    - Формирование контента для каждого слайда
    - Оптимизация под 1 минуту демонстрации
    - Подготовка текста для спикера
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_name="PresentationAgent",
                version="1.0.0",
                timeout=90,
                max_retries=3,
                custom_params={
                    "target_duration": 60,  # 1 минута в секундах
                    "slide_count": 5,
                    "include_speaker_notes": True,
                    "presentation_style": "professional",
                    "optimize_for_speed": True
                }
            )
        super().__init__(config)
    
    async def validate_input(self, data: Any) -> ValidationResult:
        """Валидация входных данных"""
        issues = []
        
        if isinstance(data, dict):
            # Проверяем наличие данных от предыдущих агентов
            required_sources = ["synthesis_data", "research_data"]
            missing_sources = [source for source in required_sources if source not in data]
            
            if missing_sources:
                issues.append(f"Отсутствуют данные от: {', '.join(missing_sources)}")
            
            # Проверяем качество synthesis данных
            if "synthesis_data" in data:
                synthesis = data["synthesis_data"]
                if not isinstance(synthesis, dict) or not synthesis.get("synthesized_content"):
                    issues.append("Synthesis данные некорректны")
            
            # Проверяем наличие темы
            topic = data.get("topic") or (data.get("synthesis_data", {}).get("topic"))
            if not topic:
                issues.append("Отсутствует тема для презентации")
            
        else:
            issues.append("Входные данные должны быть словарем с synthesis данными")
        
        score = 1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.3)
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Убедитесь что данные содержат результаты от SynthesisAgent",
                "Проверьте наличие synthesized_content для создания презентации"
            ] if issues else [],
            confidence=0.8 if len(issues) == 0 else 0.4
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Основная обработка - создание презентации"""
        self.logger.info("Starting presentation generation")
        
        try:
            # Извлекаем данные
            synthesis_data = validated_data.get("synthesis_data", {})
            research_data = validated_data.get("research_data", {})
            
            # Извлекаем основную информацию
            topic = synthesis_data.get("topic") or research_data.get("topic", "")
            synthesized_content = synthesis_data.get("synthesized_content", "")
            key_insights = synthesis_data.get("key_insights", [])
            recommendations = synthesis_data.get("recommendations", [])
            executive_summary = synthesis_data.get("executive_summary", "")
            
            # Создаем структуру презентации
            presentation_structure = await self._create_presentation_structure(
                topic, synthesized_content, key_insights, recommendations
            )
            
            # Генерируем слайды
            slides = await self._generate_slides(
                presentation_structure, synthesis_data, research_data
            )
            
            # Создаем заметки для спикера
            speaker_notes = await self._generate_speaker_notes(slides, topic)
            
            # Рассчитываем тайминг
            timing_analysis = await self._calculate_presentation_timing(slides)
            
            # Создаем метаданные презентации
            presentation_metadata = await self._create_presentation_metadata(
                slides, timing_analysis, topic
            )
            
            result_data = {
                "topic": topic,
                "presentation_structure": presentation_structure,
                "slides": slides,
                "speaker_notes": speaker_notes,
                "timing_analysis": timing_analysis,
                "metadata": presentation_metadata,
                "delivery_instructions": {
                    "total_duration": timing_analysis["total_duration"],
                    "slides_to_show": len(slides),
                    "speaking_pace": "medium-fast",
                    "key_moments": await self._identify_key_moments(slides)
                }
            }
            
            self.logger.info(f"Presentation generated for '{topic}' with {len(slides)} slides")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error during presentation generation: {str(e)}")
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
        
        required_fields = ["topic", "presentation_structure", "slides", "speaker_notes", "timing_analysis"]
        missing_fields = [field for field in required_fields if field not in result]
        
        issues = []
        
        if missing_fields:
            issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        
        # Проверяем количество слайдов
        slides = result.get("slides", [])
        slide_count = len(slides)
        if slide_count < 4:
            issues.append("Слишком мало слайдов (минимум 4)")
        elif slide_count > 5:
            issues.append("Слишком много слайдов (максимум 5)")
        
        # Проверяем длительность
        timing = result.get("timing_analysis", {})
        total_duration = timing.get("total_duration", 0)
        target_duration = self.config.custom_params.get("target_duration", 60)
        
        if abs(total_duration - target_duration) > 15:  # допуск ±15 секунд
            issues.append(f"Длительность презентации ({total_duration}с) выходит за пределы цели ({target_duration}с ±15с)")
        
        # Проверяем качество слайдов
        slide_issues = await self._validate_slides_content(slides)
        issues.extend(slide_issues)
        
        score = min(1.0, max(0.0, 1.0 - len(issues) * 0.15))
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Оптимизируйте количество и содержание слайдов",
                "Скорректируйте тайминг для соответствия целевой длительности"
            ] if issues else [],
            confidence=0.8
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "overall": 0.8,
            "content_relevance": 0.75,
            "timing_optimization": 0.8,
            "slide_quality": 0.7,
            "speaker_notes_completeness": 0.75
        }
    
    async def _create_presentation_structure(self, topic: str, synthesized_content: str, 
                                           key_insights: List[str], recommendations: List[str]) -> Dict[str, Any]:
        """Создание структуры презентации"""
        return {
            "title_slide": {
                "title": topic,
                "subtitle": "Комплексный анализ и выводы",
                "type": "title"
            },
            "introduction_slide": {
                "title": "Введение",
                "focus": "Краткий обзор темы и целей",
                "type": "introduction",
                "estimated_duration": 10
            },
            "main_content_slides": [
                {
                    "number": 3,
                    "title": "Ключевые аспекты",
                    "focus": "Основные результаты и выводы",
                    "type": "content",
                    "estimated_duration": 20
                },
                {
                    "number": 4,
                    "title": "Инсайты и паттерны",
                    "focus": "Важные наблюдения и закономерности",
                    "type": "insights",
                    "estimated_duration": 15
                }
            ],
            "conclusion_slide": {
                "title": "Заключение и рекомендации",
                "focus": "Итоги и практические применения",
                "type": "conclusion",
                "estimated_duration": 15
            }
        }
    
    async def _generate_slides(self, structure: Dict[str, Any], 
                             synthesis_data: Dict[str, Any], research_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Генерация слайдов"""
        slides = []
        topic = synthesis_data.get("topic", "")
        
        # Slide 1: Титульный
        slides.append({
            "number": 1,
            "type": "title",
            "title": topic,
            "subtitle": "Комплексный анализ и выводы",
            "content": {
                "main_text": topic,
                "visual_elements": ["title_background"],
                "minimal_text": True
            },
            "estimated_duration": 5,
            "speaker_notes": "Приветствие аудитории и анонс темы презентации"
        })
        
        # Slide 2: Введение
        executive_summary = synthesis_data.get("executive_summary", "")
        slides.append({
            "number": 2,
            "type": "introduction",
            "title": "Введение",
            "content": {
                "main_text": self._truncate_text(executive_summary, 150) if executive_summary else f"Краткий обзор темы {topic}",
                "bullet_points": [
                    "Комплексный анализ",
                    "Синтез данных",
                    "Практические выводы"
                ],
                "visual_elements": ["intro_graphic"]
            },
            "estimated_duration": 10,
            "speaker_notes": "Представление структуры презентации и основных целей"
        })
        
        # Slide 3: Ключевые аспекты
        synthesized_content = synthesis_data.get("synthesized_content", "")
        main_content = self._extract_key_content(synthesized_content)
        slides.append({
            "number": 3,
            "type": "content",
            "title": "Ключевые аспекты",
            "content": {
                "main_text": main_content[:100] + "..." if len(main_content) > 100 else main_content,
                "bullet_points": self._create_bullet_points_from_content(synthesized_content),
                "visual_elements": ["content_diagram"]
            },
            "estimated_duration": 20,
            "speaker_notes": "Разбор основных аспектов темы с акцентом на важнейших моментах"
        })
        
        # Slide 4: Инсайты и паттерны
        key_insights = synthesis_data.get("key_insights", [])
        patterns = synthesis_data.get("patterns", [])
        slides.append({
            "number": 4,
            "type": "insights",
            "title": "Инсайты и паттерны",
            "content": {
                "main_text": "Ключевые выводы:",
                "bullet_points": key_insights[:4],  # Максимум 4 инсайта
                "patterns": patterns[:3] if patterns else [],
                "visual_elements": ["insights_chart"]
            },
            "estimated_duration": 15,
            "speaker_notes": "Подчеркнуть наиболее важные инсайты и их практическую значимость"
        })
        
        # Slide 5: Заключение
        recommendations = synthesis_data.get("recommendations", [])
        slides.append({
            "number": 5,
            "type": "conclusion",
            "title": "Заключение и рекомендации",
            "content": {
                "main_text": f"Комплексный анализ темы '{topic}' завершен",
                "bullet_points": recommendations[:3],  # Максимум 3 рекомендации
                "visual_elements": ["conclusion_graphic"]
            },
            "estimated_duration": 10,
            "speaker_notes": "Завершение презентации, ответы на вопросы, обсуждение"
        })
        
        return slides
    
    async def _generate_speaker_notes(self, slides: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """Создание заметок для спикера"""
        speaker_notes = {
            "overall_notes": {
                "opening": f"Добрый день! Сегодня я представлю краткий анализ темы '{topic}'.",
                "closing": "Спасибо за внимание！ Готов ответить на ваши вопросы.",
                "transitions": {
                    "1_to_2": "Перейдем к обзору основных целей.",
                    "2_to_3": "Теперь рассмотрим ключевые аспекты подробнее.",
                    "3_to_4": "Что важно отметить из этого анализа?",
                    "4_to_5": "Какие практические выводы мы можем сделать?"
                }
            },
            "slide_notes": {}
        }
        
        for slide in slides:
            slide_number = slide["number"]
            slide_notes = slide.get("speaker_notes", "")
            
            # Добавляем детали для каждого слайда
            detailed_notes = slide_notes
            
            if slide["type"] == "title":
                detailed_notes += " Улыбка, уверенный тон, зрительный контакт."
            elif slide["type"] == "introduction":
                detailed_notes += " Четко структурируем ожидания аудитории."
            elif slide["type"] == "content":
                detailed_notes += " Подчеркнуть 2-3 ключевых момента."
            elif slide["type"] == "insights":
                detailed_notes += " Сделать паузу на самом важном инсайте."
            elif slide["type"] == "conclusion":
                detailed_notes += " Энергичное завершение, призыв к действию."
            
            speaker_notes["slide_notes"][str(slide_number)] = detailed_notes
        
        return speaker_notes
    
    async def _calculate_presentation_timing(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Расчет тайминга презентации"""
        total_duration = sum(slide.get("estimated_duration", 0) for slide in slides)
        target_duration = self.config.custom_params.get("target_duration", 60)
        
        # Анализ соответствия цели
        timing_difference = total_duration - target_duration
        adjustment_needed = abs(timing_difference) > 10
        
        return {
            "total_duration": total_duration,
            "target_duration": target_duration,
            "timing_difference": timing_difference,
            "adjustment_needed": adjustment_needed,
            "recommended_pace": "fast" if total_duration > target_duration + 10 else "normal",
            "slide_timings": {
                f"slide_{slide['number']}": slide.get("estimated_duration", 0) 
                for slide in slides
            }
        }
    
    async def _create_presentation_metadata(self, slides: List[Dict[str, Any]], 
                                          timing: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Создание метаданных презентации"""
        return {
            "title": f"Презентация: {topic}",
            "created_at": datetime.utcnow().isoformat(),
            "slide_count": len(slides),
            "total_duration": timing["total_duration"],
            "presentation_style": self.config.custom_params.get("presentation_style", "professional"),
            "target_audience": "general",
            "language": "ru",
            "format": "1minute_presentation",
            "technical_requirements": {
                "projector": True,
                "speakers": False,
                "internet": False
            }
        }
    
    async def _identify_key_moments(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Определение ключевых моментов презентации"""
        key_moments = []
        
        cumulative_time = 0
        for slide in slides:
            slide_duration = slide.get("estimated_duration", 0)
            cumulative_time += slide_duration
            
            if slide["type"] == "introduction":
                key_moments.append({
                    "time": cumulative_time,
                    "moment": "Основная информация представлена",
                    "action": "Установить зрительный контакт"
                })
            elif slide["type"] == "insights":
                key_moments.append({
                    "time": cumulative_time,
                    "moment": "Ключевые инсайты",
                    "action": "Сделать паузу для усвоения"
                })
            elif slide["type"] == "conclusion":
                key_moments.append({
                    "time": cumulative_time,
                    "moment": "Завершение",
                    "action": "Призыв к вопросам"
                })
        
        return key_moments
    
    async def _validate_slides_content(self, slides: List[Dict[str, Any]]) -> List[str]:
        """Валидация контента слайдов"""
        issues = []
        
        for i, slide in enumerate(slides):
            slide_number = slide.get("number", i + 1)
            content = slide.get("content", {})
            
            # Проверяем наличие заголовка
            if not content.get("title") and not slide.get("title"):
                issues.append(f"Слайд {slide_number}: отсутствует заголовок")
            
            # Проверяем длину текста
            main_text = content.get("main_text", "")
            if len(main_text) > 200:
                issues.append(f"Слайд {slide_number}: текст слишком длинный")
            
            # Проверяем общую структуру
            required_content_types = ["title", "content main_text"]
            if not content.get("main_text") and slide["type"] != "title":
                issues.append(f"Слайд {slide_number}: отсутствует основной текст")
        
        return issues
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Обрезка текста с сохранением целостности"""
        if len(text) <= max_length:
            return text
        
        return text[:max_length].rsplit(' ', 1)[0] + "..."
    
    def _extract_key_content(self, synthesized_content: str) -> str:
        """Извлечение ключевого контента"""
        if not synthesized_content:
            return ""
        
        # Ищем первое наиболее содержательное предложение
        sentences = synthesized_content.split('. ')
        for sentence in sentences:
            if len(sentence) > 50 and "таким образом" not in sentence.lower():
                return sentence.strip()
        
        # Если не нашли, возвращаем начало
        return synthesized_content[:200].strip()
    
    def _create_bullet_points_from_content(self, content: str) -> List[str]:
        """Создание буллитов из контента"""
        if not content:
            return ["Ключевые аспекты анализа", "Основные выводы", "Практические применения"]
        
        # Простое разделение на предложения
        sentences = content.split('. ')
        bullet_points = []
        
        for sentence in sentences[:4]:  # Максимум 4 буллита
            sentence = sentence.strip()
            if len(sentence) > 20:
                # Убираем лишние детали
                if "таким образом" in sentence.lower():
                    continue
                bullet_points.append(sentence)
        
        # Если буллитов мало, добавляем стандартные
        if len(bullet_points) < 2:
            bullet_points.extend([
                "Комплексный подход к анализу",
                "Практическая значимость результатов"
            ])
        
        return bullet_points[:4]
