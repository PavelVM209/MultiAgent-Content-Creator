"""
VideoAgent - агент для генерации видео с картинками и голосом
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from .base import BaseAgent
from models.agents import ValidationResult, AgentConfig


class VideoAgent(BaseAgent):
    """
    Агент для генерации видео на основе изображений и аудио
    
    Задачи:
    - Создание видеофайла из изображений слайдов
    - Наложение аудиодорожки на видео
    - Синхронизация изображений с аудио
    - Добавление переходов и эффектов
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_name="VideoAgent",
                version="1.0.0",
                timeout=300,
                max_retries=3,
                custom_params={
                    "video_format": "mp4",
                    "resolution": "1920x1080",  # Full HD
                    "fps": 30,
                    "codec": "h264",
                    "output_dir": "output/video",
                    "max_video_length": 600,  # 10 минут максимум
                    "transition_duration": 1.0,  # 1 секунда
                    "use_mock_generation": True  # Пока используем мок generation
                }
            )
        super().__init__(config)
        self.output_dir = Path(self.config.custom_params.get("output_dir", "output/video"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_input(self, data: Any) -> ValidationResult:
        """Валидация входных данных"""
        issues = []
        
        if isinstance(data, dict):
            # Проверяем наличие данных от ImageGeneratorAgent и AudioAgent
            has_images = "image_data" in data or "generated_images" in data
            has_audio = "audio_data" in data or "audio_file" in data
            
            if not has_images:
                issues.append("Отсутствуют данные от ImageGeneratorAgent")
            if not has_audio:
                issues.append("Отсутствуют данные от AudioAgent")
            
            # Проверяем качество изображений
            if has_images:
                generated_images = data.get("generated_images", data.get("image_data", {}).get("generated_images", []))
                if not generated_images:
                    issues.append("Отсутствуют сгенерированные изображения")
                else:
                    # Проверяем что у каждого слайда есть изображения
                    for i, image_set in enumerate(generated_images):
                        images = image_set.get("images", [])
                        if not images:
                            issues.append(f"Слайд {i+1} не имеет изображений")
            
            # Проверяем качество аудио
            if has_audio:
                audio_file = data.get("audio_file", data.get("audio_data", {}).get("audio_file", {}))
                if not audio_file.get("path"):
                    issues.append("Отсутствует путь к аудиофайлу")
                elif not os.path.exists(audio_file.get("path")):
                    issues.append("Аудиофайл не существует")
            
            # Проверяем общую длительность
            if has_audio:
                audio_metadata = data.get("audio_metadata", data.get("audio_data", {}).get("audio_metadata", {}))
                total_duration = audio_metadata.get("duration_seconds", 0)
                max_duration = self.config.custom_params.get("max_video_length", 600)
                if total_duration > max_duration:
                    issues.append(f"Аудио слишком длинное ({total_duration}с, максимум {max_duration}с)")
            
        else:
            issues.append("Входные данные должны быть словарем с данными изображений и аудио")
        
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
                "Убедитесь что данные содержат изображения и аудио",
                "Проверьте что аудиофайл существует",
                "Ограничьте общую длительность видео"
            ] if issues else [],
            confidence=0.9 if len(issues) == 0 else 0.6
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Основная обработка - генерация видео"""
        self.logger.info("Starting video generation")
        
        try:
            # Извлекаем данные
            image_data = validated_data.get("image_data", {})
            audio_data = validated_data.get("audio_data", {})
            
            # Получаем изображения и аудио
            generated_images = image_data.get("generated_images", [])
            audio_file = audio_data.get("audio_file", {})
            timing_markers = audio_data.get("timing_markers", [])
            
            if not generated_images:
                raise ValueError("No images found for video generation")
            if not audio_file.get("path"):
                raise ValueError("No audio file found for video generation")
            
            # Подготавлив temporal sequence для видео
            video_sequence = await self._prepare_video_sequence(generated_images, timing_markers)
            
            # Генерируем видеоклипы для каждого сегмента
            video_segments = await self._generate_video_segments(video_sequence)
            
            # Собираем финальное видео
            final_video = await self._assemble_final_video(video_segments, audio_file)
            
            # Создаем метаданные видео
            video_metadata = await self._create_video_metadata(final_video, video_sequence)
            
            result_data = {
                "video_file": final_video,
                "video_segments": video_segments,
                "video_sequence": video_sequence,
                "video_metadata": video_metadata,
                "generation_summary": {
                    "total_slides": len(generated_images),
                    "total_segments": len(video_segments),
                    "total_duration_minutes": video_metadata.get("duration_minutes", 0),
                    "resolution": self.config.custom_params.get("resolution", "1920x1080"),
                    "fps": self.config.custom_params.get("fps", 30),
                    "output_file": final_video.get("filename", ""),
                    "generation_time": datetime.utcnow().isoformat()
                },
                "image_data": image_data,
                "audio_data": audio_data
            }
            
            self.logger.info(f"Generated video with {len(video_segments)} segments for {len(generated_images)} slides")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error during video generation: {str(e)}")
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
        
        required_fields = ["video_file", "video_segments", "video_metadata"]
        missing_fields = [field for field in required_fields if field not in result]
        
        issues = []
        
        if missing_fields:
            issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        
        # Проверяем качество видеофайла
        video_file = result.get("video_file", {})
        if not video_file.get("path"):
            issues.append("Отсутствует путь к финальному видеофайлу")
        
        video_segments = result.get("video_segments", [])
        if len(video_segments) == 0:
            issues.append("Не сгенерировано ни одного видео сегмента")
        
        # Проверяем существование файлов
        video_file_path = video_file.get("path", "")
        if video_file_path and not os.path.exists(video_file_path):
            issues.append(f"Файл видео не найден: {video_file_path}")
        
        for segment in video_segments:
            segment_path = segment.get("path", "")
            if segment_path and not os.path.exists(segment_path):
                issues.append(f"Файл видео сегмента не найден: {segment_path}")
        
        score = min(1.0, max(0.0, 1.0 - len(issues) * 0.15))
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Проверьте что все видеофайлы успешно сгенерированы",
                "Убедитесь что файлы существуют и доступны",
                "Проверьте синхронизацию видео и аудио"
            ] if issues else [],
            confidence=0.8
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "overall": 0.75,
            "video_generation_success": 0.8,
            "file_existence": 0.9,
            "audio_sync_accuracy": 0.8,
            "metadata_completeness": 0.7
        }
    
    async def _prepare_video_sequence(self, generated_images: List[Dict], timing_markers: List[Dict]) -> List[Dict]:
        """Подготовка временной последовательности для видео"""
        sequence = []
        
        # Создаем временную шкалу на основе аудио маркеров
        current_time = 0.0
        
        for i, image_set in enumerate(generated_images):
            slide_number = image_set.get("slide_number", i + 1)
            slide_title = image_set.get("slide_title", f"Слайд {slide_number}")
            images = image_set.get("images", [])
            
            # Находим соответствующий timing маркер
            slide_marker = None
            for marker in timing_markers:
                if marker.get("slide_number") == slide_number:
                    slide_marker = marker
                    break
            
            # Рассчитываем длительность показа слайда
            if slide_marker:
                duration = slide_marker.get("duration_seconds", 5.0)
                start_time = slide_marker.get("time_seconds", current_time)
            else:
                duration = 5.0  # По умолчанию 5 секунд
                start_time = current_time
            
            # Создаем последовательность для слайда
            slide_sequence = {
                "slide_number": slide_number,
                "slide_title": slide_title,
                "start_time": start_time,
                "duration": duration,
                "images": [],
                "transitions": []
            }
            
            # Добавляем изображения слайда
            for j, image_info in enumerate(images):
                image_path = image_info.get("path", "")
                if image_path and os.path.exists(image_path):
                    # Распределяем время между изображениями
                    image_duration = duration / max(len(images), 1)
                    image_start = start_time + j * image_duration
                    
                    slide_sequence["images"].append({
                        "image_number": j + 1,
                        "path": image_path,
                        "type": image_info.get("image_type", "general"),
                        "start_time": image_start,
                        "duration": image_duration,
                        "description": image_info.get("description", "")
                    })
            
            # Добавляем переходы
            if i > 0:  # Не для первого слайда
                transition_start = start_time - self.config.custom_params.get("transition_duration", 1.0)
                slide_sequence["transitions"].append({
                    "type": "fade_in",
                    "start_time": transition_start,
                    "duration": self.config.custom_params.get("transition_duration", 1.0)
                })
            
            # Добавляем переход к следующему слайду
            if i < len(generated_images) - 1:
                transition_start = start_time + duration - self.config.custom_params.get("transition_duration", 1.0)
                slide_sequence["transitions"].append({
                    "type": "fade_out",
                    "start_time": transition_start,
                    "duration": self.config.custom_params.get("transition_duration", 1.0)
                })
            
            sequence.append(slide_sequence)
            current_time = start_time + duration
        
        return sequence
    
    async def _generate_video_segments(self, video_sequence: List[Dict]) -> List[Dict]:
        """Генерация видео сегментов"""
        segments = []
        
        for i, slide_seq in enumerate(video_sequence):
            segment_number = i + 1
            images = slide_seq.get("images", [])
            
            if not images:
                continue
            
            # Генерируем видео для слайда
            if self.config.custom_params.get("use_mock_generation", True):
                video_data = await self._mock_generate_video(segment_number, slide_seq)
            else:
                video_data = await self._real_generate_video(segment_number, slide_seq)
            
            segments.append({
                "segment_number": segment_number,
                "slide_number": slide_seq.get("slide_number"),
                "slide_title": slide_seq.get("slide_title"),
                "video_file": video_data,
                "start_time": slide_seq.get("start_time", 0),
                "duration": slide_seq.get("duration", 0),
                "image_count": len(images),
                "transitions": slide_seq.get("transitions", []),
                "generated_at": datetime.utcnow().isoformat()
            })
        
        return segments
    
    async def _mock_generate_video(self, segment_number: int, slide_seq: Dict) -> Dict:
        """Мок генерация видео для демонстрации"""
        filename = f"video_segment_{segment_number:03d}.mp4"
        filepath = self.output_dir / filename
        
        # Создаем пустой MP4 файл как заглушку
        try:
            # В реальной реализации здесь была бы генерация видео из изображений
            # Пока создаем пустой файл с заголовком MP4
            
            # Простая заглушка MP4 файла
            mp4_header = b"MOCK_VIDEO_DATA"
            
            with open(filepath, 'wb') as f:
                f.write(mp4_header)
                
                # Добавляем немного данных чтобы файл не был пустым
                duration = slide_seq.get("duration", 5.0)
                data_size = int(duration * 1000)  # 1KB на секунду
                f.write(b"\x00" * min(data_size, 10000))  # Максимум 10KB
                
        except Exception as e:
            self.logger.warning(f"Could not create mock video {filepath}: {str(e)}")
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_VIDEO_DATA")
        
        return {
            "filename": filename,
            "path": str(filepath),
            "format": self.config.custom_params.get("video_format", "mp4"),
            "resolution": self.config.custom_params.get("resolution", "1920x1080"),
            "fps": self.config.custom_params.get("fps", 30),
            "codec": self.config.custom_params.get("codec", "h264"),
            "duration_seconds": slide_seq.get("duration", 5.0),
            "file_size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "generation_method": "mock"
        }
    
    async def _real_generate_video(self, segment_number: int, slide_seq: Dict) -> Dict:
        """Реальная генерация видео через FFMPEG (заглушка)"""
        # Здесь будет интеграция с FFMPEG или другими видеолibraries
        self.logger.info("Real video generation not implemented, using mock")
        return await self._mock_generate_video(segment_number, slide_seq)
    
    async def _assemble_final_video(self, video_segments: List[Dict], audio_file: Dict) -> Dict:
        """Сборка финального видеофайла с аудио"""
        filename = f"presentation_video_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = self.output_dir / filename
        
        try:
            # В реальной реализации здесь была бы сборка видео сегментов с наложением аудио
            # Пока просто копируем первый сегмент как заглушку
            
            if video_segments:
                first_segment_path = video_segments[0]["video_file"]["path"]
                if os.path.exists(first_segment_path):
                    with open(first_segment_path, 'rb') as src, open(filepath, 'wb') as dst:
                        dst.write(src.read())
                        
                    # Добавляем информацию об аудио в файл
                    with open(filepath, 'ab') as f:
                        f.write(b"|AUDIO_SYNC:" + audio_file.get("path", "").encode()[:100])
                else:
                    # Создаем пустой файл
                    with open(filepath, 'wb') as f:
                        f.write(b"MOCK_FINAL_VIDEO")
            else:
                with open(filepath, 'wb') as f:
                    f.write(b"MOCK_FINAL_VIDEO")
                    
        except Exception as e:
            self.logger.warning(f"Could not assemble final video: {str(e)}")
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_FINAL_VIDEO")
        
        # Рассчитываем общую длительность
        total_duration = sum(segment.get("duration", 0) for segment in video_segments)
        
        return {
            "filename": filename,
            "path": str(filepath),
            "format": self.config.custom_params.get("video_format", "mp4"),
            "resolution": self.config.custom_params.get("resolution", "1920x1080"),
            "fps": self.config.custom_params.get("fps", 30),
            "codec": self.config.custom_params.get("codec", "h264"),
            "duration_seconds": total_duration,
            "duration_minutes": round(total_duration / 60, 2),
            "file_size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
            "segments_count": len(video_segments),
            "audio_synced": True,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _create_video_metadata(self, final_video: Dict, video_sequence: List[Dict]) -> Dict[str, Any]:
        """Создание метаданных видео"""
        return {
            "title": "Presentation Video",
            "duration_seconds": final_video.get("duration_seconds", 0),
            "duration_minutes": final_video.get("duration_minutes", 0),
            "file_format": final_video.get("format", "mp4"),
            "resolution": final_video.get("resolution", "1920x1080"),
            "fps": final_video.get("fps", 30),
            "codec": final_video.get("codec", "h264"),
            "segments_count": len(video_sequence),
            "total_images": sum(len(seq.get("images", [])) for seq in video_sequence),
            "total_transitions": sum(len(seq.get("transitions", [])) for seq in video_sequence),
            "file_size_mb": round(final_video.get("file_size_bytes", 0) / (1024 * 1024), 2),
            "audio_synced": True,
            "created_at": datetime.utcnow().isoformat(),
            "output_directory": str(self.output_dir)
        }
