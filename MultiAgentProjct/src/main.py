"""
Основной файл приложения MultiAgent Content Creator
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from typing import Dict, Any

from models.agents import ResearchInput, AgentResult, ValidationResult
from agents.base import BaseAgent


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestAgent(BaseAgent):
    """Тестовый агент для демонстрации базового функционала"""
    
    async def validate_input(self, data: Any) -> Any:
        """Валидация входных данных"""
        if isinstance(data, ResearchInput):
            if len(data.topic.strip()) < 1:
                return self._create_validation_result(
                    False, 
                    0.0, 
                    ["Topic cannot be empty"]
                )
            if len(data.topic) > 200:
                return self._create_validation_result(
                    False,
                    0.0,
                    ["Topic too long (max 200 characters)"]
                )
            
            return self._create_validation_result(True, 1.0)
        
        return self._create_validation_result(
            False, 
            0.0, 
            ["Expected ResearchInput"]
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Обработка данных"""
        if isinstance(validated_data, ResearchInput):
            # Имитация обработки
            await asyncio.sleep(0.1)
            
            return {
                "topic": validated_data.topic,
                "search_results": [
                    {"title": f"Result about {validated_data.topic}", "url": "example.com"},
                    {"title": f"More info on {validated_data.topic}", "url": "example.org"}
                ],
                "summary": f"Research completed for {validated_data.topic}",
                "key_points": [f"Point 1 about {validated_data.topic}", "Point 2"],
                "sources": ["example.com", "example.org"],
                "confidence_score": 0.85
            }
        
        raise ValueError("Expected validated ResearchInput")
    
    async def validate_output(self, result: Any) -> Any:
        """Валидация выходных данных"""
        if isinstance(result, dict) and "topic" in result:
            required_fields = ["topic", "search_results", "summary", "key_points"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                return self._create_validation_result(
                    False,
                    0.0,
                    [f"Missing fields: {missing_fields}"]
                )
            
            return self._create_validation_result(True, 0.9)
        
        return self._create_validation_result(
            False,
            0.0,
            ["Expected dictionary with 'topic' field"]
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "relevance": 0.7,
            "completeness": 0.8,
            "accuracy": 0.75
        }
    
    def _create_validation_result(self, valid: bool, score: float, issues: list = None):
        """Создание результата валидации"""
        return ValidationResult(
            valid=valid,
            score=score,
            issues=issues or []
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle менеджер приложения"""
    logger.info("Starting MultiAgent Content Creator")
    yield
    logger.info("Shutting down MultiAgent Content Creator")


# Создание FastAPI приложения
app = FastAPI(
    title="MultiAgent Content Creator",
    description="Мультиагентная система для создания образовательного видеоконтента",
    version="0.1.0",
    lifespan=lifespan
)

# Глобальные переменные
test_agent = TestAgent()


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "MultiAgent Content Creator API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья системы"""
    agent_health = await test_agent.health_check()
    
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z",
        "agents": {
            "test_agent": agent_health
        }
    }


@app.post("/test-agent", response_model=Dict[str, Any])
async def test_agent_endpoint(input_data: ResearchInput):
    """
    Тестовый эндпоинт для проверки базового агента
    
    Args:
        input_data: Входные данные для тестового агента
        
    Returns:
        Dict[str, Any]: Результат выполнения агента
    """
    try:
        result = await test_agent.execute(input_data)
        
        return {
            "success": result.success,
            "data": result.data,
            "processing_time": result.processing_time,
            "quality_score": result.quality_score,
            "execution_id": result.execution_id,
            "error": result.error.dict() if result.error else None
        }
        
    except Exception as e:
        logger.error(f"Error in test agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent-metrics")
async def get_agent_metrics():
    """Получить метрики агента"""
    metrics = test_agent.get_metrics()
    
    return {
        "agent_name": metrics.agent_name,
        "total_executions": metrics.total_executions,
        "success_rate": metrics.success_rate,
        "average_processing_time": metrics.average_processing_time,
        "average_quality_score": metrics.average_quality_score,
        "error_types": metrics.error_types
    }


@app.post("/reset-metrics")
async def reset_metrics():
    """Сбросить метрики агента"""
    test_agent.reset_metrics()
    
    return {"message": "Metrics reset successfully"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
