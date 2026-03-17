# Правила разработки мультиагентных систем

## Фундаментальные принципы

### 1. Стандартизация интерфейсов
ВСЕ агенты ДОЛЖНЫ имплементировать базовый интерфейс `BaseAgent`:
```python
class BaseAgent:
    def __init__(self, config: AgentConfig)
    def validate_input(self, data: Any) -> bool
    def process(self, data: Any) -> AgentResult
    def validate_output(self, result: AgentResult) -> bool
    def get_quality_metrics(self) -> QualityMetrics
```

### 2. Формат данных
- **Входные данные**: Pydantic модели с валидацией
- **Выходные данные**: Стандартизированный формат `AgentResult`
- **Ошибка**: Всегда возвращать объект ошибки, не исключения
- **Логирование**: Структурированные логи с уровнем агента

### 3. Цепочка выполнения: Понятие → Видео

#### Этап 1: Исследование понятия
```
Пользовательский ввод → ResearchAgent → ExplanationAgent → SynthesisAgent
```
- **ResearchAgent**: Поиск в интернете, возвращает сырые данные
- **ExplanationAgent**: Генерирует объяснение с примерами на базе LLM
- **SynthesisAgent**: Объединяет результаты, создает финальное описание
- **Quality Check**: Полнота, точность, понятность

#### Этап 2: Презентация
```
Описание → PresentationAgent → ImageGeneratorAgent
```
- **PresentationAgent**: Структура презентации (1 мин, 4-5 слайдов)
- **ImageGeneratorAgent**: Генерирует изображения для слайдов
- **Quality Check**: Длительность, логика, визуальное качество

#### Этап 3: Аудио
```
Презентация → AudioAgent
```
- **AudioAgent**: Создает аудиофайл на базе презентации
- **Quality Check**: Синхронизация, качество голоса, ясность

#### Этап 4: Видео
```
Презентация + Аудио → VideoAgent
```
- **VideoAgent**: Создает видео с изображениями и голосом
- **Quality Check**: Синхронизация видео/аудио, общее качество

## Архитектурные правила

### 1. Оркестратор
- **Единая точка управления**: Все вызовы agентов через оркестратор
- **Сохранение состояния**: Каждый шаг сохраняется в Redis/базу данных
- **Логирование решений**: Записывать все решения о возвратах
- **Механизм отката**: Возможность вернуться на любой предыдущий этап

### 2. Управление ошибками
```python
class AgentError:
    agent_name: str
    error_type: ErrorType
    message: str
    retry_count: int
    can_retry: bool
```

### 3. Качество и метрики
Для каждого агента определить:
```python
class QualityMetrics:
    success_rate: float
    processing_time: float
    quality_score: float
    error_rate: float
    user_satisfaction: float
```

## Правила разработки

### 1. Создание нового агента
1. **Наследоваться от BaseAgent**
2. **Определить Pydantic модели для input/output**
3. **Реализовать валидацию данных**
4. **Добавить метрики качества**
5. **Написать unit тесты**
6. **Обновить документацию**

### 2. Интеграция внешних API
1. **Использовать async/await**
2. **Реализовать retry логику**
3. **Кэширование результатов**
4. **Обработка API лимитов**
5. **Мониторинг состояния**

### 3. Тестирование
```python
# Каждый агент должен иметь:
- Unit тесты для всех методов
- Integration тесты с внешними API
- End-to-end тесты workflow
- Performance тесты
- Error scenario тесты
```

## Контроль качества

### 1. Автоматическая валидация
```python
class QualityValidator:
    def validate_research(self, data: ResearchResult) -> ValidationResult
    def validate_explanation(self, text: str) -> ValidationResult
    def validate_presentation(self, slides: List[Slide]) -> ValidationResult
    def validate_audio(self, audio: AudioData) -> ValidationResult
    def validate_video(self, video: VideoData) -> ValidationResult
```

### 2. Пороговые значения для отката
- **Research**: < 70% релевантности → повторить поиск
- **Explanation**: < 80% понятности → regenerate
- **Presentation**: ≠ 1 минута → перегенерировать
- **Audio**: < 75% качества → regenerate
- **Video**: < 80% синхронизации → regenerate

### 3. Возврат на доработку
Оркестратор может:
- Вернуться на предыдущий этап
- Изменить параметры агента
- Запустить альтернативного агента
- Прервать выполнение и запросить помощь

## Мониторинг и логирование

### 1. Структурированные логи
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "agent_name": "ResearchAgent",
  "task_id": "uuid",
  "action": "process",
  "input_size": 100,
  "output_size": 500,
  "processing_time": 2.5,
  "quality_score": 0.85,
  "errors": []
}
```

### 2. Метрики производительности
- Время выполнения каждого агента
- Частота ошибок по типам
- Успешность полного workflow
- Использование внешних API
- Потребление ресурсов

## Конфигурация

### 1. Environment variables
```bash
# API Keys
GOOGLE_SEARCH_API_KEY=
OPENAI_API_KEY=
DALLE_API_KEY=
ELEVENLABS_API_KEY=
RUNWAY_API_KEY=

# Infrastructure
REDIS_URL=
DATABASE_URL=
LOG_LEVEL=
MAX_CONCURRENT_TASKS=
```

### 2. Agent configuration
```python
AGENT_CONFIG = {
    "research": {
        "max_results": 10,
        "timeout": 30,
        "retry_count": 3
    },
    "explanation": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000
    }
}
```

## Безопасность

### 1. API ключи
- Хранить в environment variables
- Ротация ключей
- Мониторинг использования
- Ограничение доступа

### 2. Валидация входных данных
- Проверка на инъекции
- Ограничение размера данных
- Фильтрация контента
- Проверка форматов

## Развёртывание

### 1. Docker контейнеры
Каждый агент в отдельном контейнере:
```dockerfile
FROM python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["python", "src/agents/research_agent.py"]
```

### 2. Масштабирование
- Горизонтальное масштабирование агентов
- Load balancing
- Auto-scaling по нагрузке
- Health checks

Эти правила обеспечат согласованность, надежность и масштабируемость мультиагентной системы.
