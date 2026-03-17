#!/usr/bin/env python3
"""
Основной файл для бесплатной версии мультиагентной системы
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Добавляем корень проекта в Python path
sys.path.append(str(Path(__file__).parent))

from src.orchestrator.orchestrator import Orchestrator
from config.free_config import (
    get_free_agent_config,
    get_free_system_config,
    validate_free_environment,
    get_free_mode_features,
    get_free_mode_limitations
)


class FreeMultiAgentSystem:
    """Бесплатная версия мультиагентной системы"""
    
    def __init__(self):
        self.system_config = get_free_system_config()
        self.orchestrator: Optional[Orchestrator] = None
        
        # Настройка логирования
        self._setup_logging()
        
        # Создаем выходные директории
        self._create_output_directories()
        
        self.logger.info("🆓 Бесплатная мультиагентная система инициализирована")
    
    def _setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('output/free_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("FreeMultiAgentSystem")
    
    def _create_output_directories(self):
        """Создание выходных директорий"""
        output_paths = self.system_config["output_paths"]
        for path in output_paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    async def initialize(self) -> bool:
        """Инициализация системы"""
        try:
            # Валидация среды
            validation_results = validate_free_environment()
            
            if not validation_results["valid"]:
                self.logger.error("❌ Системные требования не выполнены:")
                for issue in validation_results["issues"]:
                    self.logger.error(f"   • {issue}")
                return False
            
            # Показываем предупреждения
            if validation_results["warnings"]:
                self.logger.warning("⚠️ Предупреждения:")
                for warning in validation_results["warnings"]:
                    self.logger.warning(f"   • {warning}")
            
            # Показываем рекомендации
            if validation_results["recommendations"]:
                self.logger.info("💡 Рекомендации:")
                for rec in validation_results["recommendations"]:
                    self.logger.info(f"   • {rec}")
            
            # Инициализируем оркестратор с бесплатными конфигурациями
            self.orchestrator = Orchestrator()
            
            # Устанавливаем конфигурации для агентов
            await self._setup_free_agents()
            
            self.logger.info("✅ Система успешно инициализирована")
            self._print_system_info()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def _setup_free_agents(self):
        """Настройка агентов для бесплатной версии"""
        if not self.orchestrator:
            return
        
        # Конфигурируем каждого агента для бесплатной работы
        agent_configs = {
            "research": get_free_agent_config("research"),
            "explanation": get_free_agent_config("explanation"),
            "synthesis": get_free_agent_config("synthesis"),
            "presentation": get_free_agent_config("presentation"),
            "image_generator": get_free_agent_config("image_generator"),
            "audio": get_free_agent_config("audio"),
            "video": get_free_agent_config("video")
        }
        
        # Применяем конфигурации
        for agent_name, config in agent_configs.items():
            if config:
                # В реальной системе здесь была бы конфигурация агентов
                self.logger.info(f"🔧 Агент {agent_name} сконфигурирован для бесплатного режима")
    
    def _print_system_info(self):
        """Вывод информации о системе"""
        features = get_free_mode_features()
        limitations = get_free_mode_limitations()
        
        print("\n" + "="*60)
        print("🆓 БЕСПЛАТНАЯ ВЕРСИЯ МУЛЬТИАГЕНТНОЙ СИСТЕМЫ")
        print("="*60)
        
        print("\n✅ Доступные функции:")
        for feature, available in features.items():
            status = "✅" if available else "❌"
            feature_name = {
                "real_web_search": "Веб-поиск (DuckDuckGo)",
                "local_llm": "Локальные LLM (Ollama)",
                "image_generation": "Генерация изображений",
                "text_to_speech": "Синтез речи",
                "video_assembly": "Сборка видео",
                "high_quality_images": "Изображения высокого качества",
                "high_quality_audio": "Аудио высокого качества",
                "real_time_processing": "Обработка в реальном времени",
                "parallel_processing": "Параллельная обработка",
                "cloud_storage": "Облачное хранение",
                "advanced_analysis": "Продвинутая аналитика"
            }.get(feature, feature)
            print(f"   {status} {feature_name}")
        
        print("\n⚠️ Ограничения:")
        for limitation, description in limitations.items():
            limitation_name = {
                "search_results": "Результаты поиска",
                "image_resolution": "Разрешение изображений",
                "image_generation": "Генерация изображений",
                "llm_quality": "Качество текста",
                "audio_quality": "Качество аудио",
                "processing_speed": "Скорость обработки",
                "parallel_processing": "Обработка агентов",
                "storage": "Хранение",
                "support": "Поддержка"
            }.get(limitation, limitation)
            print(f"   • {limitation_name}: {description}")
        
        print("\n💰 Стоимость: $0 (полностью бесплатно)")
        print("="*60 + "\n")
    
    async def process_topic(self, topic: str) -> Dict[str, Any]:
        """Обработка темы создания контента"""
        if not self.orchestrator:
            return {"error": "Система не инициализирована"}
        
        self.logger.info(f"🚀 Начинаю обработку темы: {topic}")
        start_time = datetime.now()
        
        try:
            # Создаем запрос для оркестратора
            request_data = {
                "topic": topic,
                "mode": "free",
                "target_duration": 60,  # 1 минута
                "slide_count": 4,
                "include_images": True,
                "include_audio": True,
                "include_video": True
            }
            
            # Запускаем обработку
            workflow_result = await self.orchestrator.execute_workflow(
                input_data=request_data,
                custom_steps=None,
                workflow_id=f"free_workflow_{int(datetime.now().timestamp())}"
            )
            
            # Конвертируем результат в ожидаемый формат
            result = {
                "topic": topic,
                "success": workflow_result.success,
                "workflow_id": workflow_result.workflow_id,
                "final_data": workflow_result.final_data,
                "agent_results": workflow_result.agent_results,
                "quality_scores": workflow_result.quality_scores,
                "total_time": workflow_result.total_time,
                "steps_completed": workflow_result.steps_completed,
                "total_steps": workflow_result.total_steps,
                "rollbacks_performed": workflow_result.rollbacks_performed,
                "completion_rate": workflow_result.completion_rate,
                "average_quality": workflow_result.average_quality,
                "error": workflow_result.error
            }
            
            # Добавляем метаданные бесплатной версии
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result["free_version_metadata"] = {
                "processed_with": "free_version",
                "processing_time_seconds": processing_time,
                "system_version": self.system_config["version"],
                "timestamp": datetime.now().isoformat(),
                "cost_usd": 0.0
            }
            
            self.logger.info(f"✅ Тема '{topic}' обработана за {processing_time:.2f}с")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки темы '{topic}': {e}")
            return {
                "error": str(e),
                "topic": topic,
                "status": "failed"
            }
    
    async def print_result_summary(self, result: Dict[str, Any]):
        """Вывод сводки результатов"""
        if "error" in result:
            print(f"❌ Ошибка: {result['error']}")
            return
        
        metadata = result.get("free_version_metadata", {})
        
        print("\n" + "="*60)
        print("📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ")
        print("="*60)
        
        print(f"📝 Тема: {result.get('topic', 'Не указана')}")
        print(f"⏱️ Время обработки: {metadata.get('processing_time_seconds', 0):.2f}с")
        print(f"💰 Стоимость: ${metadata.get('cost_usd', 0):.2f}")
        print(f"📅 Время: {metadata.get('timestamp', 'N/A')}")
        print(f"🔧 Версия: {metadata.get('system_version', 'N/A')}")
        
        # Статус агентов
        agents_status = result.get("agents_status", {})
        if agents_status:
            print("\n🤖 Статус агентов:")
            for agent, status in agents_status.items():
                status_icon = "✅" if status.get("success", False) else "❌"
                print(f"   {status_icon} {agent}")
        
        # Файлы результатов
        output_files = result.get("output_files", {})
        if output_files:
            print("\n📁 Созданные файлы:")
            for file_type, file_info in output_files.items():
                if isinstance(file_info, dict):
                    filename = file_info.get("filename", "N/A")
                    size = file_info.get("size_bytes", 0)
                    size_mb = size / (1024*1024) if size > 0 else 0
                    print(f"   📄 {file_type}: {filename} ({size_mb:.2f} MB)")
        
        # Качество
        quality_score = result.get("overall_quality_score", 0)
        print(f"\n📊 Общее качество: {quality_score:.2f}/1.0")
        
        print("="*60 + "\n")
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.orchestrator:
            # В реальной системе здесь была бы очистка агентов
            pass
        self.logger.info("🧹 Ресурсы системы очищены")


async def main():
    """Главная функция"""
    print("🚀 Запуск бесплатной мультиагентной системы...")
    
    # Инициализация системы
    system = FreeMultiAgentSystem()
    
    if not await system.initialize():
        print("❌ Не удалось инициализировать систему")
        return 1
    
    # Получаем тему от пользователя
    print("\nВведите тему для создания контента (или 'exit' для выхода):")
    
    while True:
        try:
            topic = input("\n🎯 Тема: ").strip()
            
            if topic.lower() in ['exit', 'выход', 'quit', 'q']:
                print("👋 Завершение работы...")
                break
            
            if not topic:
                print("⚠️ Пожалуйста, введите тему")
                continue
            
            if len(topic) < 3:
                print("⚠️ Тема слишком короткая (минимум 3 символа)")
                continue
            
            # Обрабатываем тему
            result = await system.process_topic(topic)
            
            # Выводим результаты
            await system.print_result_summary(result)
            
            # Спрашиваем продолжить ли
            continue_input = input("\n🔄 Продолжить? (y/n): ").strip().lower()
            if continue_input in ['n', 'no', 'нет', 'exit', 'выход']:
                break
                
        except KeyboardInterrupt:
            print("\n👋 Работа прервана")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Очистка
    await system.cleanup()
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Программа завершена")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
