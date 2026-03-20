#!/usr/bin/env python3
"""
Комплексный тест полного workflow с всеми 7 агентами
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корень проекта в Python path
sys.path.append(str(Path(__file__).parent))

from src.orchestrator.orchestrator import Orchestrator, AgentStep
from src.agents import (
    ResearchAgent, 
    ExplanationAgent, 
    SynthesisAgent, 
    PresentationAgent,
    ImageGeneratorAgent,
    AudioAgent,
    VideoAgent
)


async def test_individual_agents():
    """Тест каждого агента индивидуально"""
    print("🧪 Тестирование отдельных агентов")
    print("=" * 60)
    
    # Тестовые данные
    test_topic = "Искусственный интеллект в современной медицине"
    
    agents = [
        ("ResearchAgent", ResearchAgent()),
        ("ExplanationAgent", ExplanationAgent()),
        ("SynthesisAgent", SynthesisAgent()),
        ("PresentationAgent", PresentationAgent()),
        ("ImageGeneratorAgent", ImageGeneratorAgent()),
        ("AudioAgent", AudioAgent()),
        ("VideoAgent", VideoAgent())
    ]
    
    results = {}
    
    for agent_name, agent in agents:
        try:
            print(f"🔍 Тестирование {agent_name}")
            
            # Подготавливаем тестовые данные для каждого агента
            if agent_name == "ResearchAgent":
                test_data = {"topic": test_topic}
            elif agent_name == "ExplanationAgent":
                # Макет данных от ResearchAgent
                test_data = {
                    "topic": test_topic,
                    "research_data": {
                        "summary": "ИИ в медицине - это революционная технология",
                        "key_points": ["Диагностика", "Лечение", "Прогнозирование"],
                        "sources": ["source1.com", "source2.com"],
                        "structured_results": {
                            "domains": {"wikipedia.org": 2, "researchgate.net": 1},
                            "content_types": {"article": 3},
                            "total_results": 3,
                            "average_relevance": 0.75,
                            "topic_coverage": {
                                "theoretical": 0.6,
                                "practical": 0.4,
                                "historical": 0.2,
                                "future": 0.8
                            }
                        }
                    },
                    # Добавляем structured_results и в корень для совместимости
                    "structured_results": {
                        "domains": {"wikipedia.org": 2, "researchgate.net": 1},
                        "content_types": {"article": 3},
                        "total_results": 3,
                        "average_relevance": 0.75,
                        "topic_coverage": {
                            "theoretical": 0.6,
                            "practical": 0.4,
                            "historical": 0.2,
                            "future": 0.8
                        }
                    }
                }
            elif agent_name == "SynthesisAgent":
                # Макет данных от предыдущих агентов
                test_data = {
                    "topic": test_topic,
                    "research_data": {
                        "topic": test_topic,  # Добавляем topic для валидации
                        "summary": "ИИ в медицине",
                        "key_points": ["Точка 1", "Точка 2"],
                        "sources": ["source1.com", "source2.com"],
                        "confidence_score": 0.8,
                        "structured_results": {
                            "domains": {"wikipedia.org": 2, "researchgate.net": 1},
                            "content_types": {"article": 3},
                            "total_results": 3,
                            "average_relevance": 0.75,
                            "topic_coverage": {
                                "theoretical": 0.6,
                                "practical": 0.4,
                                "historical": 0.2,
                                "future": 0.8
                            }
                        }
                    },
                    "explanation_data": {
                        "topic": test_topic,  # Добавляем topic для валидации
                        "content": "Подробное объяснение темы ИИ в медицине",
                        "key_concepts": ["Нейросети", "Машинное обучение"],
                        "examples": ["Пример 1", "Пример 2"],
                        "difficulty_level": "intermediate"
                    }
                }
            elif agent_name == "PresentationAgent":
                # Макет данных от SynthesisAgent
                test_data = {
                    "topic": test_topic,
                    "synthesis_data": {
                        "topic": test_topic,  # Добавляем topic
                        "synthesized_content": "Синтезированная информация о ИИ в медицине",
                        "key_insights": ["Инсайт 1", "Инсайт 2"],
                        "executive_summary": "Комплексный анализ ИИ в медицине",
                        "recommendations": ["Рекомендация 1", "Рекомендация 2"],
                        "patterns": ["Паттерн 1", "Паттерн 2"]
                    },
                    "research_data": {
                        "summary": "Исследование ИИ в медицине",
                        "key_points": ["Точка 1", "Точка 2"]
                    }
                }
            elif agent_name == "ImageGeneratorAgent":
                # Макет данных от PresentationAgent
                test_data = {
                    "presentation_data": {
                        "slides": [
                            {"number": 1, "title": "Введение", "content": "Содержание слайда 1"},
                            {"number": 2, "title": "Основная часть", "content": "Содержание слайда 2"}
                        ]
                    },
                    "synthesis_data": {
                        "synthesized_content": "Синтезированный контент"
                    }
                }
            elif agent_name == "AudioAgent":
                # Макет данных от PresentationAgent
                test_data = {
                    "presentation_data": {
                        "slides": [
                            {"number": 1, "title": "Слайд 1", "content": "Текст для озвучки слайда 1"},
                            {"number": 2, "title": "Слайд 2", "content": "Текст для озвучки слайда 2"}
                        ],
                        "timing_analysis": {
                            "total_duration_seconds": 120
                        }
                    },
                    "image_data": {}  # Необязательный
                }
            elif agent_name == "VideoAgent":
                # Создаем тестовый аудиофайл если его нет
                test_audio_path = "output/audio/test_video_audio.mp3"
                Path(test_audio_path).parent.mkdir(parents=True, exist_ok=True)
                if not Path(test_audio_path).exists():
                    # Создаем пустой файл для теста
                    with open(test_audio_path, 'wb') as f:
                        f.write(b'fake audio data')
                
                # Макет данных от ImageGeneratorAgent и AudioAgent
                test_data = {
                    "image_data": {
                        "generated_images": [
                            {
                                "slide_number": 1,
                                "slide_title": "Слайд 1",
                                "images": [
                                    {"path": "output/images/slide_1_title_image.png", "image_type": "title_image", "description": "Заголовочное изображение"}
                                ]
                            }
                        ]
                    },
                    "audio_data": {
                        "audio_file": {
                            "path": test_audio_path
                        },
                        "timing_markers": [
                            {"slide_number": 1, "time_seconds": 0, "duration_seconds": 10}
                        ],
                        "audio_metadata": {
                            "duration_seconds": 60
                        }
                    }
                }
            
            # Выполняем агент
            result = await agent.execute(test_data)
            
            if result.success:
                print(f"✅ {agent_name} успешно выполнен")
                
                # Собираем статистику
                if agent_name == "ResearchAgent":
                    results[agent_name] = {
                        "sources_found": len(result.data.get("sources", [])),
                        "key_points": len(result.data.get("key_points", [])),
                        "confidence": result.metadata.get("confidence", 0)
                    }
                elif agent_name == "ExplanationAgent":
                    content = result.data.get("content", "")
                    results[agent_name] = {
                        "content_length": len(content),
                        "examples": len(result.data.get("examples", [])),
                        "key_concepts": len(result.data.get("key_concepts", []))
                    }
                elif agent_name == "SynthesisAgent":
                    results[agent_name] = {
                        "connections": len(result.data.get("connections", [])),
                        "patterns": len(result.data.get("patterns", [])),
                        "insights": len(result.data.get("key_insights", []))
                    }
                elif agent_name == "PresentationAgent":
                    slides = result.data.get("slides", [])
                    results[agent_name] = {
                        "slides_count": len(slides),
                        "total_duration": result.data.get("timing_analysis", {}).get("total_duration_seconds", 0)
                    }
                elif agent_name == "ImageGeneratorAgent":
                    generated_images = result.data.get("generated_images", [])
                    results[agent_name] = {
                        "image_sets": len(generated_images),
                        "total_images": sum(len(img_set.get("images", [])) for img_set in generated_images)
                    }
                elif agent_name == "AudioAgent":
                    audio_segments = result.data.get("audio_segments", [])
                    results[agent_name] = {
                        "segments_count": len(audio_segments),
                        "duration_minutes": result.data.get("audio_metadata", {}).get("duration_minutes", 0)
                    }
                elif agent_name == "VideoAgent":
                    video_segments = result.data.get("video_segments", [])
                    results[agent_name] = {
                        "segments_count": len(video_segments),
                        "duration_minutes": result.data.get("video_metadata", {}).get("duration_minutes", 0)
                    }
            else:
                print(f"❌ {agent_name} завершился с ошибкой: {result.error.message if result.error else 'Unknown error'}")
                results[agent_name] = {"error": str(result.error.message if result.error else 'Unknown error')}
                
        except Exception as e:
            print(f"❌ {agent_name} - исключение: {str(e)}")
            results[agent_name] = {"exception": str(e)}
    
    print("\n📊 Результаты тестирования агентов:")
    for agent_name, result in results.items():
        print(f"  {agent_name}: {result}")
    
    print("\n" + "=" * 60)
    return results


async def test_full_workflow():
    """Тест полного workflow с оркестратором"""
    print("🚀 Тестирование полного workflow")
    print("=" * 60)
    
    try:
        # Создаем оркестратор
        orchestrator = Orchestrator()
        
        # Регистрируем всех агентов
        agents_config = [
            (AgentStep.RESEARCH, ResearchAgent()),
            (AgentStep.EXPLANATION, ExplanationAgent()),
            (AgentStep.SYNTHESIS, SynthesisAgent()),
            (AgentStep.PRESENTATION, PresentationAgent()),
            (AgentStep.IMAGE_GENERATION, ImageGeneratorAgent()),
            (AgentStep.AUDIO_GENERATION, AudioAgent()),
            (AgentStep.VIDEO_GENERATION, VideoAgent())
        ]
        
        for step, agent in agents_config:
            orchestrator.register_agent(step, agent)
        
        print("✅ Все агенты зарегистрированы в оркестраторе")
        
        # Выполняем workflow
        workflow_input = {
            "topic": "Искусственный интеллект в современной медицине",
            "requirements": "Создать полную презентацию с изображениями, аудио и видео",
            "target_duration_minutes": 5
        }
        
        print("🔄 Запуск полного workflow...")
        result = await orchestrator.execute_workflow(workflow_input)
        
        # Анализируем результаты
        print("\n📊 Результаты выполнения workflow:")
        print(f"   Успешность: {'✅' if result.success else '❌'}")
        print(f"   Шагов выполнено: {result.steps_completed}/{result.total_steps}")
        print(f"   Общее время: {result.total_time:.2f}с")
        print(f"   Откатов: {result.rollbacks_performed}")
        
        if result.average_quality is not None:
            print(f"   Среднее качество: {result.average_quality:.3f}")
        
        print("\n💾 Созданные файлы:")
        
        # Проверяем созданные файлы
        output_dirs = [
            "output/images",
            "output/audio", 
            "output/video"
        ]
        
        for output_dir in output_dirs:
            if os.path.exists(output_dir):
                files = list(Path(output_dir).glob("*"))
                print(f"   {output_dir}: {len(files)} файлов")
                for file in files[:3]:  # Показываем первые 3 файла
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"     - {file.name} ({size_mb:.2f} MB)")
                if len(files) > 3:
                    print(f"     ... и еще {len(files) - 3} файлов")
        
        if result.success and result.agent_results:
            print("\n📈 Качество по шагам:")
            for step_name, step_result in result.agent_results.items():
                if hasattr(step_result, 'quality_score') and step_result.quality_score is not None:
                    print(f"   {step_name}: {step_result.quality_score:.3f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при выполнении workflow: {str(e)}")
        return None


async def main():
    """Главная функция тестирования"""
    print("🎯 Начало комплексного тестирования мультиагентной системы")
    print("=" * 80)
    
    # Создаем выходные директории
    for output_dir in ["output/images", "output/audio", "output/video"]:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Тестируем отдельных агентов
    individual_results = await test_individual_agents()
    
    print("\n" + "=" * 80)
    
    # Тестируем полный workflow
    workflow_result = await test_full_workflow()
    
    print("\n" + "=" * 80)
    print("🏆 Итоговые результаты:")
    
    # Считаем успешные тесты
    successful_agents = sum(1 for result in individual_results.values() if "error" not in result and "exception" not in result)
    total_agents = len(individual_results)
    
    print(f"   Индивидуальные тесты: {successful_agents}/{total_agents} успешно")
    
    if workflow_result:
        print(f"   Полный workflow: {'✅ УСПЕХ' if workflow_result.success else '❌ НЕУДАЧА'}")
    else:
        print("   Полный workflow: ❌ НЕ ВЫПОЛНЕН")
    
    # Общий результат
    overall_success = successful_agents == total_agents and workflow_result and workflow_result.success
    
    if overall_success:
        print("\n🎉 ВСЕ ТЕСТЫ УСПЕШНЫ! Мультиагентная система работает корректно!")
    else:
        print("\n⚠️  Некоторые тесты не прошли. Проверьте логи выше.")
    
    return overall_success


if __name__ == "__main__":
    # Запускаем тесты
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
