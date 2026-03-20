"""Ollama клиент для генерации текста"""

import requests
import json
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Клиент для взаимодействия с Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.timeout = 30
        self.default_model = "llama3:8b"
        self._available = None
    
    def is_available(self) -> bool:
        """Проверяет доступность Ollama"""
        if self._available is not None:
            return self._available
            
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            self._available = response.status_code == 200
            if self._available:
                logger.info("Ollama доступен")
            else:
                logger.warning(f"Ollama вернул статус {response.status_code}")
            return self._available
        except Exception as e:
            logger.warning(f"Ollama недоступен: {e}")
            self._available = False
            return False
    
    def get_models(self) -> List[str]:
        """Получает список доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"Доступные модели Ollama: {models}")
                return models
            else:
                logger.error(f"Ошибка получения моделей: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении моделей: {e}")
            return []
    
    def generate(self, prompt: str, model: str = None, **kwargs) -> Optional[str]:
        """Генерирует текст"""
        if not self.is_available():
            logger.warning("Ollama недоступен, невозможно сгенерировать текст")
            return None
        
        if model is None:
            model = self.default_model
        
        # Проверяем что модель доступна
        available_models = self.get_models()
        if model not in available_models:
            logger.warning(f"Модель {model} недоступна, доступные: {available_models}")
            # Если запрошенная модель недоступна, используем первую доступную
            if available_models:
                model = available_models[0]
                logger.info(f"Используем доступную модель: {model}")
            else:
                return None
        
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "top_p": kwargs.get("top_p", 0.9),
                    "num_predict": kwargs.get("max_tokens", 1000),
                    "stop": kwargs.get("stop", None)
                }
            }
            
            logger.debug(f"Запрос к Ollama: модель={model}, промпт={prompt[:100]}...")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "")
                
                if generated_text:
                    logger.info(f"Успешно сгенерирован текст ({len(generated_text)} символов)")
                    return generated_text
                else:
                    logger.warning("Получен пустой ответ от Ollama")
                    return None
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Таймаут запроса к Ollama ({self.timeout}с)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка подключения к Ollama")
            self._available = False  # Сбрасываем кэш доступности
            return None
        except Exception as e:
            logger.error(f"Ошибка при генерации текста: {e}")
            return None
    
    def generate_structured(self, prompt: str, schema: Dict[str, Any], model: str = None) -> Optional[Dict[str, Any]]:
        """Генерирует структурированный ответ"""
        # Добавляем инструкции для структурированного вывода
        structured_prompt = f"""
{prompt}

Ответь в формате JSON со следующей структурой:
{json.dumps(schema, indent=2, ensure_ascii=False)}

Твой ответ должен быть только валидным JSON без дополнительного текста.
"""
        
        response_text = self.generate(structured_prompt, model=model)
        if not response_text:
            return None
        
        try:
            # Пытаемся извлечь JSON из ответа
            # Ищем начало JSON объекта
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.error("В ответе не найден JSON")
                return None
            
            json_text = response_text[start_idx:end_idx]
            result = json.loads(json_text)
            
            logger.info("Успешно сгенерирован структурированный ответ")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}")
            logger.debug(f"Текст ответа: {response_text}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            
            if response.status_code == 200:
                version_data = response.json()
                models = self.get_models()
                
                return {
                    "status": "healthy",
                    "version": version_data.get("version", "unknown"),
                    "models": models,
                    "default_model": self.default_model,
                    "model_available": self.default_model in models
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def reset_availability_cache(self):
        """Сбрасывает кэш доступности"""
        self._available = None
        logger.debug("Кэш доступности Ollama сброшен")
