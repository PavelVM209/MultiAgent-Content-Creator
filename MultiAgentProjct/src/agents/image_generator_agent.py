"""
ImageGeneratorAgent - агент для генерации изображений для слайдов
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import base64
from pathlib import Path

from .base import BaseAgent
from models.agents import ValidationResult, AgentConfig


class ImageGeneratorAgent(BaseAgent):
    """
    Агент для генерации изображений на основе синтезированных данных
    
    Задачи:
    - Генерация изображений для каждого слайда презентации
    - Создание визуального контента на основе текста
    - Сохранение изображений в системную папку
    - Интеграция с PresentationAgent для обогащения слайдов
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_name="ImageGeneratorAgent",
                version="1.0.0",
                timeout=120,
                max_retries=3,
                custom_params={
                    "image_style": "professional",
                    "image_size": "1024x768",
                    "image_format": "png",
                    "output_dir": "output/images",
                    "max_images_per_slide": 2,
                    "use_mock_generation": True  # Пока используем мок generation
                }
            )
        super().__init__(config)
        self.output_dir = Path(self.config.custom_params.get("output_dir", "output/images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_input(self, data: Any) -> ValidationResult:
        """Валидация входных данных"""
        issues = []
        
        if isinstance(data, dict):
            # Проверяем наличие данных от PresentationAgent
            has_synthesis = "synthesis_data" in data
            has_presentation = "presentation_data" in data or "slides" in data
            
            if not has_synthesis and not has_presentation:
                issues.append("Отсутствуют данные от PresentationAgent или SynthesisAgent")
            
            # Проверяем качество слайдов
            if has_presentation:
                slides = data.get("slides", data.get("presentation_data", {}).get("slides", []))
                if not slides:
                    issues.append("Отсутствуют слайды для генерации изображений")
                elif len(slides) > 10:
                    issues.append("Слишком много слайдов (максимум 10)")
            
        else:
            issues.append("Входные данные должны быть словарем с данными презентации")
        
        # Проверяем доступность выходной директории
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            if not os.access(self.output_dir, os.W_OK):
                issues.append("Нет прав на запись в выходную директорию")
        except Exception as e:
            issues.append(f"Ошибка создания выходной директории: {str(e)}")
        
        score = 1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.2)
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Убедитесь что данные содержат слайды презентации",
                "Проверьте доступность выходной директории",
                "Проверьте что количество слайдов не превышает 10"
            ] if issues else [],
            confidence=0.9 if len(issues) == 0 else 0.6
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Основная обработка - генерация изображений"""
        self.logger.info("Starting image generation")
        
        try:
            # Извлекаем данные
            synthesis_data = validated_data.get("synthesis_data", {})
            presentation_data = validated_data.get("presentation_data", {})
            
            # Получаем слайды
            slides = presentation_data.get("slides", [])
            if not slides:
                raise ValueError("No slides found for image generation")
            
            # Генерируем изображения для каждого слайда
            generated_images = await self._generate_images_for_slides(slides, synthesis_data)
            
            # Создаем метаинформацию об изображениях
            image_metadata = await self._create_image_metadata(generated_images)
            
            # Обновляем слайды с путями к изображениям
            updated_slides = await self._update_slides_with_images(slides, generated_images)
            
            result_data = {
                "generated_images": generated_images,
                "image_metadata": image_metadata,
                "updated_slides": updated_slides,
                "output_directory": str(self.output_dir),
                "generation_summary": {
                    "total_slides": len(slides),
                    "total_images": len(generated_images),
                    "images_per_slide": [len(imgs) for imgs in [img.get("images", []) for img in generated_images]],
                    "generation_time": datetime.utcnow().isoformat()
                },
                "synthesis_data": synthesis_data,
                "presentation_data": presentation_data
            }
            
            self.logger.info(f"Generated {len(generated_images)} image sets for {len(slides)} slides")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error during image generation: {str(e)}")
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
        
        required_fields = ["generated_images", "image_metadata", "updated_slides"]
        missing_fields = [field for field in required_fields if field not in result]
        
        issues = []
        
        if missing_fields:
            issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        
        # Проверяем качество сгенерированных изображений
        generated_images = result.get("generated_images", [])
        if len(generated_images) == 0:
            issues.append("Не сгенерировано ни одного изображения")
        
        updated_slides = result.get("updated_slides", [])
        if len(updated_slides) == 0:
            issues.append("Отсутствуют обновленные слайды")
        
        # Проверяем что каждому слайду соответствуют изображения
        if generated_images and updated_slides:
            if len(generated_images) != len(updated_slides):
                issues.append("Количество наборов изображений не совпадает с количеством слайдов")
        
        # Проверяем существование файлов изображений
        for image_set in generated_images:
            images = image_set.get("images", [])
            for image_info in images:
                image_path = image_info.get("path", "")
                if image_path and not os.path.exists(image_path):
                    issues.append(f"Файл изображения не найден: {image_path}")
        
        score = min(1.0, max(0.0, 1.0 - len(issues) * 0.15))
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=[
                "Проверьте что все изображения успешно сгенерированы",
                "Убедитесь что файлы изображений существуют",
                "Проверьте соответствие между слайдами и изображениями"
            ] if issues else [],
            confidence=0.8
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "overall": 0.75,
            "image_generation_success": 0.8,
            "file_existence": 0.9,
            "slide_integration": 0.7,
            "metadata_completeness": 0.8
        }
    
    async def _generate_images_for_slides(self, slides: List[Dict], synthesis_data: Dict) -> List[Dict]:
        """Генерация изображений для каждого слайда"""
        generated_images = []
        
        for i, slide in enumerate(slides):
            slide_number = slide.get("number", i + 1)
            slide_title = slide.get("title", f"Слайд {slide_number}")
            slide_content = slide.get("content", "")
            
            # Определяем тип слайда и соответствующую стратегию генерации
            slide_type = self._classify_slide_type(slide_title, slide_content)
            
            # Генерируем изображения для слайда
            slide_images = await self._generate_slide_images(
                slide_number, slide_title, slide_content, slide_type, synthesis_data
            )
            
            generated_images.append({
                "slide_number": slide_number,
                "slide_title": slide_title,
                "slide_type": slide_type,
                "images": slide_images,
                "generation_time": datetime.utcnow().isoformat()
            })
        
        return generated_images
    
    def _classify_slide_type(self, title: str, content: str) -> str:
        """Классификация типа слайда для выбора стратегии генерации"""
        title_lower = title.lower()
        content_lower = content.lower()
        
        if any(word in title_lower for word in ["введение", "intro", "начало", "обзор"]):
            return "intro"
        elif any(word in title_lower for word in ["заключение", "вывод", "summary", "итог"]):
            return "conclusion"
        elif any(word in title_lower for word in ["данные", "график", "chart", "статистика"]):
            return "data"
        elif any(word in title_lower for word in ["процесс", "схема", "process", "workflow"]):
            return "process"
        elif any(word in title_lower for word in ["инсайт", "insight", "открытие", "идея"]):
            return "insight"
        else:
            return "general"
    
    async def _generate_slide_images(self, slide_number: int, title: str, content: str, 
                                   slide_type: str, synthesis_data: Dict) -> List[Dict]:
        """Генерация изображений для конкретного слайда"""
        images = []
        
        if self.config.custom_params.get("use_mock_generation", True):
            # Мок генерация изображений
            images = await self._mock_generate_images(slide_number, title, slide_type)
        else:
            # Реальная генерация через API (заглушка для будущего)
            images = await self._real_generate_images(slide_number, title, content, slide_type)
        
        return images
    
    async def _mock_generate_images(self, slide_number: int, title: str, slide_type: str) -> List[Dict]:
        """Мок генерация изображений для демонстрации"""
        images = []
        
        # Создаем простые изображения-заглушки
        image_configs = {
            "intro": ["title_image", "concept_diagram"],
            "conclusion": ["summary_graphic", "future_outlook"],
            "data": ["data_chart", "statistics_visual"],
            "process": ["workflow_diagram", "process_flow"],
            "insight": ["breakthrough_visual", "innovation_graphic"],
            "general": ["concept_image", "supporting_graphic"]
        }
        
        config_types = image_configs.get(slide_type, image_configs["general"])
        
        for i, image_type in enumerate(config_types):
            filename = f"slide_{slide_number}_{image_type}_{i+1}.png"
            filepath = self.output_dir / filename
            
            # Создаем простое изображение-заглушку (в реальности здесь был бы API вызов)
            await self._create_mock_image(filepath, title, image_type)
            
            images.append({
                "filename": filename,
                "path": str(filepath),
                "image_type": image_type,
                "description": f"{image_type.replace('_', ' ').title()} for slide: {title}",
                "generated_at": datetime.utcnow().isoformat()
            })
        
        return images
    
    async def _create_mock_image(self, filepath: Path, title: str, image_type: str):
        """Создание мок изображения"""
        try:
            # Создаем простое текстовое изображение как заглушку
            from PIL import Image, ImageDraw, ImageFont
            
            # Параметры изображения
            width, height = 1024, 768
            background_color = self._get_color_for_type(image_type)
            
            # Создаем изображение
            image = Image.new('RGB', (width, height), background_color)
            draw = ImageDraw.Draw(image)
            
            # Добавляем заголовок
            try:
                # Пытаемся использовать системный шрифт
                font_title = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
                font_text = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            except:
                # Если системный шрифт недоступен, используем шрифт по умолчанию
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()
            
            # Рисуем заголовок
            title_text = f"Slide: {title[:50]}{'...' if len(title) > 50 else ''}"
            title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            title_x = (width - title_width) // 2
            title_y = 100
            
            draw.text((title_x, title_y), title_text, fill="white", font=font_title)
            
            # Рисуем тип изображения
            type_text = f"Type: {image_type.replace('_', ' ').title()}"
            type_bbox = draw.textbbox((0, 0), type_text, font=font_text)
            type_width = type_bbox[2] - type_bbox[0]
            type_height = type_bbox[3] - type_bbox[1]
            
            type_x = (width - type_width) // 2
            type_y = 300
            
            draw.text((type_x, type_y), type_text, fill="white", font=font_text)
            
            # Добавляем современный элемент дизайна
            self._add_design_element(draw, width, height)
            
            # Сохраняем изображение
            image.save(filepath, "PNG")
            
        except ImportError:
            # Если PIL недоступен, создаем пустой файл
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_IMAGE_DATA")
        except Exception as e:
            self.logger.warning(f"Could not create mock image {filepath}: {str(e)}")
            # Создаем пустой файл как запасной вариант
            with open(filepath, 'wb') as f:
                f.write(b"MOCK_IMAGE_DATA")
    
    def _get_color_for_type(self, image_type: str) -> str:
        """Получить цвет для типа изображения"""
        colors = {
            "title_image": "#2E86AB",
            "concept_diagram": "#A23B72",
            "summary_graphic": "#F18F01",
            "future_outlook": "#C73E1D",
            "data_chart": "#4CAF50",
            "statistics_visual": "#2196F3",
            "workflow_diagram": "#FF9800",
            "process_flow": "#9C27B0",
            "breakthrough_visual": "#E91E63",
            "innovation_graphic": "#00BCD4",
            "concept_image": "#607D8B",
            "supporting_graphic": "#795548"
        }
        return colors.get(image_type, "#37474F")
    
    def _add_design_element(self, draw, width: int, height: int):
        """Добавить современный элемент дизайна"""
        # Добавляем простую геометрическую фигуру
        import random
        
        # Рисуем несколько кругов для современного вида
        for _ in range(5):
            x = random.randint(50, width - 50)
            y = random.randint(400, height - 50)
            radius = random.randint(20, 60)
            
            # Полупрозрачные круги
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                        fill="white", outline="white", width=2)
    
    async def _real_generate_images(self, slide_number: int, title: str, content: str, 
                                  slide_type: str) -> List[Dict]:
        """Реальная генерация изображений через API (заглушка)"""
        # Здесь будет интеграция с реальными API генерации изображений
        # DALL-E, Midjourney, Stable Diffusion и т.д.
        self.logger.info("Real image generation not implemented, using mock")
        return await self._mock_generate_images(slide_number, title, slide_type)
    
    async def _create_image_metadata(self, generated_images: List[Dict]) -> Dict[str, Any]:
        """Создание метаинформации об изображениях"""
        total_files = 0
        total_size = 0
        image_types = {}
        
        for slide_images in generated_images:
            images = slide_images.get("images", [])
            for image_info in images:
                total_files += 1
                image_path = image_info.get("path", "")
                
                # Проверяем размер файла
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    total_size += file_size
                
                # Собираем статистику по типам
                image_type = image_info.get("image_type", "unknown")
                image_types[image_type] = image_types.get(image_type, 0) + 1
        
        return {
            "total_images": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "image_types_distribution": image_types,
            "average_image_size_kb": round(total_size / total_files / 1024, 2) if total_files > 0 else 0,
            "output_directory": str(self.output_dir),
            "supported_formats": ["PNG", "JPEG"],
            "generation_method": "mock" if self.config.custom_params.get("use_mock_generation") else "real"
        }
    
    async def _update_slides_with_images(self, slides: List[Dict], generated_images: List[Dict]) -> List[Dict]:
        """Обновление слайдов с путями к изображениям"""
        updated_slides = []
        
        for i, slide in enumerate(slides):
            updated_slide = slide.copy()
            
            # Находим соответствующие изображения
            slide_number = slide.get("number", i + 1)
            slide_images = None
            
            for image_set in generated_images:
                if image_set.get("slide_number") == slide_number:
                    slide_images = image_set.get("images", [])
                    break
            
            # Добавляем изображения в слайд
            if slide_images:
                updated_slide["images"] = slide_images
                updated_slide["has_images"] = True
                
                # Обновляем контент с информацией об изображениях
                content = slide.get("content", "")
                image_info = f"\n\n[Изображения: {len(slide_images)} шт.]\n"
                for img in slide_images:
                    image_info += f"- {img.get('description', 'Изображение')}\n"
                
                updated_slide["content"] = content + image_info
            else:
                updated_slide["images"] = []
                updated_slide["has_images"] = False
            
            updated_slides.append(updated_slide)
        
        return updated_slides
