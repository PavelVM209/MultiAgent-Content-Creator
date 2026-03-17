"""
AudioAgent - агент для создания аудиофайлов на базе презентации
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from .base import BaseAgent
from models.agents import ValidationResult, AgentConfig


class AudioAgent(BaseAgent):
    """
    Агент для генерации аудиофайлов на основе презентации
    
    Задачи:
    - Создание аудиодорожки для презентации
    - Генерация голосового сопровождения для слайдов
    - Синтез речи из текста слайдов
    - Создание временных меток синхронизации
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_name="AudioAgent",
                version="1.0.0",
                timeout=180,
                max_retries=3,
                custom_params={
                    "voice_model": "natural_male",
                    "speech_rate": "normal",
                    "audio_format": "mp3",
                    "sample_rate": 22050,
                    "output_dir": "output/audio",
                    "max_audio_length": 300,  # 5 минут максимум
                    "use_mock_generation": True  # Пока используем мок generation
                }
            )
        super().__init__(config)
        self.output_dir = Path(self.config.custom_params.get("output_dir", "output/audio"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_input(self, data: Any) -> ValidationResult:
        """Валидация входных данных"""
        issues = []
        
        if isinstance(data, dict):
            # Проверяем наличие данных от PresentationAgent
            has_presentation = "presentation_data" in data or "slides" in data
            has_images = "image_data" in data or "generated_images" in data
            
            if not has_presentation:
                issues.append("Отсутствуют данные от PresentationAgent")
            
            # Проверяем качество слайдов
            if has_presentation:
                slides = data.get("slides", data.get("presentation_data", {}).get("slides", []))
                if not slides:
                    issues.append("Отсутствуют слайды для генерации аудио")
                elif len(slides) > 20:
                    issues.append("Слишком много слайдов (максимум 20)")
                else:
                    # Проверяем что у слайдов есть контент
                    for i, slide in enumerate(slides):
                        content = slide.get("content", "")
                        if len(content.strip()) < 10:
                            issues.append(f"Слайд {i+1} содержит недостаточно текста для озвучки")
            
            # Проверяем общую длительность презентации
            if has_presentation:
                timing = data.get("presentation_data", {}).get("timing_analysis", {})
                total_duration = timing.get("total_duration_seconds", 0)
                if total_duration > self.config.custom_params.get("max_audio_length", 300):
                    issues.append(f"Презентация слишком длинная ({total_duration}с)")
            
        else:
            issues.append("Входные данные должны быть словарем с данными презентации")
        
        # Проверяем доступность выходной директории
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if not os.access(self.output_dir, os.W_OK):
                issues.append("Нет прав на запись в выходную директорию")
        except Exception as e:
            issues.append(f"Ошибка создания выходной директории: {str(e)}")
        
        score = 1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.15)
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Убедитесь что данные содержат слайды с текстовым контентом",
                "Проверьте доступность выходной директории",
                "Ограничьте количество слайдов и общую длительность"
            ] if issues else [],
            confidence=0.9 if len(issues) == 0 else 0.6
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Основная обработка - генерация аудио"""
        self.logger.info("Starting audio generation")
        
        try:
            # Извлекаем данные
            presentation_data = validated_data.get("presentation_data", {})
            image_data = validated_data.get("image_data", {})
            
            # Получаем слайды
            slides = presentation_data.get("slides", [])
            if not slides:
                raise ValueError("No slides found for audio generation")
            
            # Подготавливаем текст для аудио
            audio_script = await self._prepare_audio_script(slides)
            
            # Генерируем аудиофайлы для каждого сегмента
            audio_segments = await self._generate_audio_segments(audio_script)
            
            # Собираем финальный аудиофайл
            final_audio = await self._assemble_final_audio(audio_segments, slides)
            
            # Создаем временную разметку
            timing_markers = await self._create_timing_markers(audio_segments, slides)
            
            # Создаем метаданные аудио
            audio_metadata = await self._create_audio_metadata(final_audio, timing_markers)
            
            result_data = {
                "audio_file": final_audio,
                "audio_segments": audio_segments,
                "timing_markers": timing_markers,
                "audio_metadata": audio_metadata,
                "audio_script": audio_script,
                "generation_summary": {
                    "total_slides": len(slides),
                    "total_segments": len(audio_segments),
                    "total_duration_minutes": audio_metadata.get("duration_minutes", 0),
                    "output_file": final_audio.get("filename", ""),
                    "generation_time": datetime.utcnow().isoformat()
                },
                "presentation_data": presentation_data,
                "image_data": image_data
            }
            
            self.logger.info(f"Generated audio with {len(audio_segments)} segments for {len(slides)} slides")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error during audio generation: {str(e)}")
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
        
        required_fields = ["audio_file", "audio_segments", "timing_markers", "audio_metadata"]
        missing_fields = [field for field in required_fields if field not in result]
        
        issues = []
        
        if missing_fields:
            issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        
        # Проверяем качество аудиофайлов
        audio_file = result.get("audio_file", {})
        if not audio_file.get("path"):
            issues.append("Отсутствует путь к финальному аудиофайлу")
        
        audio_segments = result.get("audio_segments", [])
        if len(audio_segments) == 0:
            issues.append("Не сгенерировано ни одного аудиосегмента")
        
        # Проверяем существование файлов
        audio_file_path = audio_file.get("path", "")
        if audio_file_path and not os.path.exists(audio_file_path):
            issues.append(f"Файл аудио не найден: {audio_file_path}")
        
        for segment in audio_segments:
            segment_path = segment.get("path", "")
            if segment_path and not os.path.exists(segment_path):
                issues.append(f"Файл аудиосегмента не найден: {segment_path}")
        
        # Проверяем временную разметку
        timing_markers = result.get("timing_markers", [])
        if len(timing_markers) == 0:
            issues.append("Отсутствует временная разметка")
        
        score = min(1.0, max(0.0, 1.0 - len(issues) * 0.15))
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Проверьте что все аудиофайлы успешно сгенерированы",
                "Убедитесь что файлы существуют и доступны",
                "Проверьте временную разметку аудио"
            ] if issues else [],
            confidence=0.8
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "overall": 0.75,
            "audio_generation_success": 0.8,
            "file_existence": 0.9,
            "timing_accuracy": 0.8,
            "metadata_completeness": 0.7
        }
    
    async def _prepare_audio_script(self, slides: List[Dict]) -> List[Dict]:
        """Подготовка сценария для аудио"""
        script = []
        
        for i, slide in enumerate(slides):
            slide_number = slide.get("number", i + 1)
            title = slide.get("title", f"Слайд {slide_number}")
            content = slide.get("content", "")
            
            # Очищаем и форматируем текст для озвучки
            cleaned_content = self._clean_text_for_speech(content)
            
            # Добавляем приветствие для первого слайда
            if slide_number == 1:
                greeting = "Здравствуйте! Сегодня мы рассмотрим тему: "
                script.append({
                    "type": "intro",
                    "slide_number": 0,
                    "text": greeting + title,
                    "duration_estimate": len((greeting + title).split()) * 0.5,  # ~0.5с на слово
                    "pause_before": 0,
                    "pause_after": 1.0
                })
            
            # Добавляем основной текст слайда
            script.append({
                "type": "slide_content",
                "slide_number": slide_number,
                "text": f"Слайд {slide_number}. {title}. " + cleaned_content,
                "duration_estimate": len(cleaned_content.split()) * 0.5,
                "pause_before": 0.5,
                "pause_after": 1.0
            })
            
            # Добавляем переходы между слайдами
            if slide_number < len(slides):
                transition = self._get_transition_text(slide_number, slides)
                if transition:
                    script.append({
                        "type": "transition",
                        "slide_number": slide_number,
                        "text": transition,
                        "duration_estimate": len(transition.split()) * 0.5,
                        "pause_before": 0.3,
                        "pause_after": 0.5
                    })
        
        # Добавляем заключение
        conclusion = self._get_conclusion_text(slides)
        script.append({
            "type": "conclusion",
            "slide_number": len(slides),
            "text": conclusion,
            "duration_estimate": len(conclusion.split()) * 0.5,
            "pause_before": 1.0,
            "pause_after": 0
        })
        
        return script
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Очистка текста для синтеза речи"""
        # Удаляем markdown разметку
        import re
        
        # Убираем ссылки в квадратных скобках
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Убираем остальные скобки
        text = re.sub(r'\[[^\]]+\]', '', text)
        
        # Убираем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Заменяем сложные символы
        replacements = {
            '&': ' и ',
            '%': ' процентов',
            '$': ' долларов ',
            '€': ' евро ',
            '©': ' копирайт ',
            '®': ' registered ',
            '™': ' trademark '
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _get_transition_text(self, current_slide: int, slides: List[Dict]) -> str:
        """Получить текст перехода между слайдами"""
        transitions = [
            "Перейдем к следующему слайду.",
            "Давайте рассмотрим следующий аспект.",
            "Теперь обсудим следующую тему.",
            "Следующий слайд покажет нам...",
            "Переходим к следующему вопросу."
        ]
        
        return transitions[current_slide % len(transitions)]
    
    def _get_conclusion_text(self, slides: List[Dict]) -> str:
        """Получить текст заключения"""
        return "Спасибо за внимание! Надеюсь, эта презентация была для вас полезной."
    
    async def _generate_audio_segments(self, audio_script: List[Dict]) -> List[Dict]:
        """Генерация аудиосегментов для сценария"""
        segments = []
        
        for i, segment in enumerate(audio_script):
            segment_number = i + 1
            text = segment.get("text", "")
            
            if not text.strip():
                continue
            
            # Генерируем аудио для сегмента
            if self.config.custom_params.get("use_mock_generation", True):
                audio_data = await self._mock_generate_audio(segment_number, text)
            else:
                audio_data = await self._real_generate_audio(segment_number, text)
            
            segments.append({
                "segment_number": segment_number,
                "type": segment.get("type"),
                "slide_number": segment.get("slide_number"),
                "text": text,
                "audio_file": audio_data,
                "duration_estimate": segment.get("duration_estimate", 0),
                "pause_before": segment.get("pause_before", 0),
                "pause_after": segment.get("pause_after", 0),
                "generated_at": datetime.utcnow().isoformat()
            })
        
        return segments
    
    async def _mock_generate_audio(self, segment_number: int, text: str) -> Dict:
        """Мок генерация аудио для демонстрации"""
        filename = f"audio_segment_{segment_number:03d}.mp3"
        filepath = self.output_dir / filename
        
        # Создаем пустой MP3 файл как заглушку
        try:
            # Генерируем простой синусоидальный сигнал как заглушку
            import numpy as np
            
            sample_rate = self.config.custom_params.get("sample_rate", 22050)
            duration = max(1.0, len(text.split()) * 0.5)  # Минимум 1 секунда
            
            # Создаем простой аудиосигнал
            t = np.linspace(0, duration, int(sample_rate * duration))
            frequency = 440  # Нота A4
            audio_signal = 0.3 * np.sin(2 * np.pi * frequency * t)
            
            # Конвертируем в байты (упрощенно)
            audio_bytes = (audio_signal * 32767).astype(np.int16).tobytes()
            
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_AUDIO_DATA" + audio_bytes[:1000])  # Ограничиваем размер
            
        except ImportError:
            # Если numpy недоступен, создаем пустой файл
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_AUDIO_DATA")
        except Exception as e:
            self.logger.warning(f"Could not create mock audio {filepath}: {str(e)}")
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_AUDIO_DATA")
        
        return {
            "filename": filename,
            "path": str(filepath),
            "format": self.config.custom_params.get("audio_format", "mp3"),
            "sample_rate": self.config.custom_params.get("sample_rate", 22050),
            "duration_seconds": duration if 'duration' in locals() else 1.0,
            "file_size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "generation_method": "mock"
        }
    
    async def _real_generate_audio(self, segment_number: int, text: str) -> Dict:
        """Реальная генерация аудио через TTS API (заглушка)"""
        # Здесь будет интеграция с реальными TTS API
        # Google TTS, Azure TTS, ElevenLabs и т.д.
        self.logger.info("Real audio generation not implemented, using mock")
        return await self._mock_generate_audio(segment_number, text)
    
    async def _assemble_final_audio(self, audio_segments: List[Dict], slides: List[Dict]) -> Dict:
        """Сборка финального аудиофайла"""
        filename = f"presentation_audio_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = self.output_dir / filename
        
        try:
            # В реальной реализации здесь была бы сборка аудио сегментов
            # Пока просто копируем первый сегмент как заглушку
            
            if audio_segments:
                first_segment_path = audio_segments[0]["audio_file"]["path"]
                if os.path.exists(first_segment_path):
                    with open(first_segment_path, 'rb') as src, open(filepath, 'wb') as dst:
                        dst.write(src.read())
                else:
                    # Создаем пустой файл
                    with open(filepath, 'wb') as f:
                        f.write(b"MOCK_FINAL_AUDIO")
            else:
                with open(filepath, 'wb') as f:
                    f.write(b"MOCK_FINAL_AUDIO")
                    
        except Exception as e:
            self.logger.warning(f"Could not assemble final audio: {str(e)}")
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_FINAL_AUDIO")
        
        # Рассчитываем общую длительность
        total_duration = sum(segment.get("duration_estimate", 0) for segment in audio_segments)
        
        return {
            "filename": filename,
            "path": str(filepath),
            "format": self.config.custom_params.get("audio_format", "mp3"),
            "duration_seconds": total_duration,
            "duration_minutes": round(total_duration / 60, 2),
            "file_size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "segments_count": len(audio_segments),
            "slides_count": len(slides),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _create_timing_markers(self, audio_segments: List[Dict], slides: List[Dict]) -> List[Dict]:
        """Создание временных меток для синхронизации"""
        markers = []
        current_time = 0.0
        
        for segment in audio_segments:
            current_time += segment.get("pause_before", 0)
            
            markers.append({
                "time_seconds": current_time,
                "slide_number": segment.get("slide_number"),
                "segment_type": segment.get("type"),
                "text": segment.get("text", "")[:100] + "..." if len(segment.get("text", "")) > 100 else segment.get("text", ""),
                "duration_seconds": segment.get("duration_estimate", 0)
            })
            
            current_time += segment.get("duration_estimate", 0)
            current_time += segment.get("pause_after", 0)
        
        return markers
    
    async def _create_audio_metadata(self, final_audio: Dict, timing_markers: List[Dict]) -> Dict[str, Any]:
        """Создание метаданных аудио"""
        return {
            "title": "Presentation Audio",
            "duration_seconds": final_audio.get("duration_seconds", 0),
            "duration_minutes": final_audio.get("duration_minutes", 0),
            "file_format": final_audio.get("format", "mp3"),
            "sample_rate": self.config.custom_params.get("sample_rate", 22050),
            "voice_model": self.config.custom_params.get("voice_model", "natural_male"),
            "speech_rate": self.config.custom_params.get("speech_rate", "normal"),
            "markers_count": len(timing_markers),
            "file_size_mb": round(final_audio.get("file_size_bytes", 0) / (1024 * 1024), 2),
            "created_at": datetime.utcnow().isoformat(),
            "output_directory": str(self.output_dir)
        }
