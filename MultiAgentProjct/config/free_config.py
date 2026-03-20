"""
Конфигурация для бесплатной версии мультиагентной системы
"""

from src.models.agents import AgentConfig
from typing import Dict, Any


# ResearchAgent - бесплатный поиск через DuckDuckGo
FREE_RESEARCH_CONFIG = AgentConfig(
    agent_name="ResearchAgent",
    version="1.0.0-free",
    timeout=60,
    max_retries=2,
    custom_params={
        "max_results": 8,
        "search_depth": "basic",
        "include_sources": True,
        "language": "ru",
        "use_free_search": True,
        "search_provider": "duckduckgo"
    }
)

# ExplanationAgent - бесплатные LLM через Ollama
FREE_EXPLANATION_CONFIG = AgentConfig(
    agent_name="ExplanationAgent",
    version="1.0.0-free",
    timeout=120,
    max_retries=2,
    custom_params={
        "use_local_llm": True,
        "llm_provider": "ollama",
        "model_name": "llama3:8b",
        "temperature": 0.7,
        "max_tokens": 1000,
        "ollama_url": "http://localhost:11434",
        "fallback_to_template": True
    }
)

# SynthesisAgent - бесплатные LLM через Ollama
FREE_SYNTHESIS_CONFIG = AgentConfig(
    agent_name="SynthesisAgent",
    version="1.0.0-free",
    timeout=120,
    max_retries=2,
    custom_params={
        "use_local_llm": True,
        "llm_provider": "ollama",
        "model_name": "llama3:8b",
        "temperature": 0.6,
        "max_tokens": 1500,
        "ollama_url": "http://localhost:11434",
        "synthesis_approach": "comprehensive"
    }
)

# PresentationAgent - базовая функциональность
FREE_PRESENTATION_CONFIG = AgentConfig(
    agent_name="PresentationAgent", 
    version="1.0.0-free",
    timeout=60,
    max_retries=2,
    custom_params={
        "slide_count": 4,
        "target_duration": 60,
        "presentation_style": "educational",
        "include_transitions": True,
        "optimized_for_video": True
    }
)

# ImageGeneratorAgent - локальные модели
FREE_IMAGE_CONFIG = AgentConfig(
    agent_name="ImageGeneratorAgent",
    version="1.0.0-free", 
    timeout=180,
    max_retries=1,
    custom_params={
        "use_local_models": True,
        "model_provider": "stable_diffusion",
        "model_name": "runwayml/stable-diffusion-v1-5",
        "image_size": (512, 512),
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
        "fallback_to_pil": True,
        "max_images_per_slide": 2
    }
)

# AudioAgent - gTTS бесплатно
FREE_AUDIO_CONFIG = AgentConfig(
    agent_name="AudioAgent",
    version="1.0.0-free",
    timeout=90,
    max_retries=2,
    custom_params={
        "use_free_tts": True,
        "tts_provider": "gtts",
        "language": "ru",
        "slow_speed": False,
        "max_segment_length": 5000,
        "optimize_duration": True
    }
)

# VideoAgent - FFmpeg бесплатно
FREE_VIDEO_CONFIG = AgentConfig(
    agent_name="VideoAgent",
    version="1.0.0-free",
    timeout=240,
    max_retries=1,
    custom_params={
        "use_ffmpeg": True,
        "ffmpeg_path": "ffmpeg",
        "output_format": "mp4",
        "video_codec": "libx264",
        "audio_codec": "aac",
        "frame_rate": 30,
        "resolution": "1024x768",
        "optimize_for_web": True
    }
)

# Общая конфигурация системы
FREE_SYSTEM_CONFIG = {
    "version": "1.0.0-free",
    "mode": "free",
    "description": "Бесплатная версия мультиагентной системы",
    
    # Параметры качества
    "quality_settings": {
        "target_quality": 0.7,
        "min_acceptable_quality": 0.5,
        "enable_auto_retry": True,
        "max_retry_attempts": 2
    },
    
    # Настройки производительности
    "performance": {
        "max_concurrent_agents": 3,
        "timeout_multiplier": 1.5,
        "enable_caching": True,
        "cache_duration": 3600
    },
    
    # Fallback стратегии
    "fallback_strategies": {
        "research": ["duckduckgo", "mock"],
        "explanation": ["ollama", "template"], 
        "synthesis": ["ollama", "template"],
        "images": ["stable_diffusion", "pil"],
        "audio": ["gtts", "template"],
        "video": ["ffmpeg", "mock"]
    },
    
    # Пути к_OUTOUT
    "output_paths": {
        "base_dir": "output",
        "images": "output/images",
        "audio": "output/audio", 
        "video": "output/video",
        "temp": "output/temp"
    },
    
    # Системные требования
    "system_requirements": {
        "min_ram_gb": 8,
        "min_disk_gb": 10,
        "optional_gpu_gb": 6,
        "required_software": ["python", "ffmpeg"],
        "optional_software": ["ollama"]
    }
}

# Словарь конфигураций всех агентов
FREE_AGENT_CONFIGS = {
    "research": FREE_RESEARCH_CONFIG,
    "explanation": FREE_EXPLANATION_CONFIG,
    "synthesis": FREE_SYNTHESIS_CONFIG,
    "presentation": FREE_PRESENTATION_CONFIG,
    "image_generator": FREE_IMAGE_CONFIG,
    "audio": FREE_AUDIO_CONFIG,
    "video": FREE_VIDEO_CONFIG
}


def get_free_agent_config(agent_name: str) -> AgentConfig:
    """Получить конфигурацию для агента в бесплатной версии"""
    return FREE_AGENT_CONFIGS.get(agent_name)


def get_free_system_config() -> Dict[str, Any]:
    """Получить системную конфигурацию для бесплатной версии"""
    return FREE_SYSTEM_CONFIG.copy()


def is_free_mode() -> bool:
    """Проверить что система работает в бесплатном режиме"""
    return True


def get_free_mode_features() -> Dict[str, bool]:
    """Получить список доступных функций в бесплатном режиме"""
    return {
        "real_web_search": True,       # DuckDuckGo
        "local_llm": True,            # Ollama
        "image_generation": True,     # Stable Diffusion (опционально)
        "text_to_speech": True,       # gTTS
        "video_assembly": True,       # FFmpeg
        "high_quality_images": False,  # Только 512x512
        "high_quality_audio": False,   # Базовый TTS
        "real_time_processing": False, # Медленнее
        "parallel_processing": False,  # Последовательно
        "cloud_storage": False,       # Только локально
        "advanced_analysis": False    # Базовая аналитика
    }


def get_free_mode_limitations() -> Dict[str, str]:
    """Получить список ограничений бесплатной версии"""
    return {
        "search_results": "Максимум 8 результатов поиска",
        "image_resolution": "Максимальное разрешение 512x512",
        "image_generation": "Требует GPU с 6GB+ VRAM",
        "llm_quality": "Качество текста ~70% от GPT-4",
        "audio_quality": "Базовый синтез речи",
        "processing_speed": "Обработка на 30-50% медленнее",
        "parallel_processing": "Последовательная обработка агентов",
        "storage": "Только локальное сохранение",
        "support": "Без технической поддержки"
    }


def validate_free_environment() -> Dict[str, Any]:
    """Проверить готовность среды для бесплатной версии"""
    import subprocess
    import sys
    
    results = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "recommendations": []
    }
    
    # Проверка Python
    if sys.version_info < (3, 8):
        results["valid"] = False
        results["issues"].append("Требуется Python 3.8 или выше")
    
    # Проверка FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    except:
        results["warnings"].append("FFmpeg не найден - видео сборка недоступна")
        results["recommendations"].append("Установите FFmpeg: brew install ffmpeg")
    
    # Проверка Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            results["warnings"].append("Ollama недоступен - будет использована шаблонизация")
            results["recommendations"].append("Установите и запустите Ollama для лучшего качества текста")
    except:
        results["warnings"].append("Ollama недоступен - будет использована шаблонизация")
        results["recommendations"].append("Установите и запустите Ollama для лучшего качества текста")
    
    # Проверка GPU для изображений
    try:
        import torch
        if not torch.cuda.is_available():
            results["warnings"].append("GPU недоступен - генерация изображений будет медленной")
            results["recommendations"].append("Для быстрой генерации изображений установите CUDA")
    except:
        results["warnings"].append("PyTorch не установлен - генерация изображений недоступна")
        results["recommendations"].append("Установите PyTorch: pip install torch torchvision")
    
    return results
