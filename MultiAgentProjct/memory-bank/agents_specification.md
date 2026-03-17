# Спецификация агентов MultiAgent Content Creator

## Общие стандарты для всех агентов

### Базовый интерфейс
Все агенты должны наследоваться от `BaseAgent` и имплементировать:
```python
class BaseAgent(ABC):
    @abstractmethod
    async def validate_input(self, data: Any) -> ValidationResult
    
    @abstractmethod
    async def process_data(self, validated_data: Any) -> ProcessResult
    
    @abstractmethod
    async def validate_output(self, result: ProcessResult) -> ValidationResult
    
    @abstractmethod
    def get_quality_thresholds(self) -> Dict[str, float]
    
    @abstractmethod
    def get_timeout_config(self) -> TimeoutConfig
```

### Стандартные модели данных
```python
class AgentResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[AgentError] = None
    metadata: Dict[str, Any] = {}
    processing_time: float
    quality_score: Optional[float] = None

class AgentError(BaseModel):
    agent_name: str
    error_type: str
    message: str
    retry_count: int = 0
    can_retry: bool = True
    timestamp: datetime

class ValidationResult(BaseModel):
    valid: bool
    score: float
    issues: List[str] = []
    suggestions: List[str] = []
```

---

## ЭТАП 1: АГЕНТЫ ИССЛЕДОВАНИЯ

### ResearchAgent - Агент поиска информации

**Назначение:** Поиск релевантной информации о понятии в интернете

**Входные данные:**
```python
class ResearchInput(BaseModel):
    topic: str                     # Понятие для исследования
    language: str = "ru"          # Язык поиска
    max_results: int = 10         # Максимальное количество результатов
    search_depth: str = "basic"   # basic/advanced/comprehensive
```

**Выходные данные:**
```python
class ResearchResult(BaseModel):
    topic: str
    search_results: List[SearchResult]
    Summary: str                   # Краткое суммарное описание
    key_points: List[str]         # Ключевые моменты
    sources: List[str]           # Источники информации
    confidence_score: float       # Уверенность в результатах
    processing_metadata: Dict
```

**Процесс работы:**
1. Валидация входного запроса
2. Формирование поисковых запросов
3. Выполнение поиска через Google Search API
4. Скрапинг и извлечение контента
5. Фильтрация и ранжирование результатов
6. Формирование структурированного вывода

**Критерии качества:**
- Релевантность результатов: ≥ 70%
- Количество источников: ≥ 3
- Покрытие темы: ≥ 60%
- Достоверность источников: ≥ 70%

**Конфигурация:**
```python
RESEARCH_CONFIG = {
    "max_search_queries": 5,
    "content_extraction_timeout": 30,
    "min_source_reliability": 0.6,
    "cache_ttl": 3600,
    "retry_attempts": 3
}
```

**API интеграции:**
- Google Search API
- BeautifulSoup4 для веб-скрапинга
- Redis для кэширования результатов

---

### ExplanationAgent - Агент генерации объяснений

**Назначение:** Создание расширенного объяснения понятия с примерами

**Входные данные:**
```python
class ExplanationInput(BaseModel):
    topic: str
    research_data: ResearchResult
    target_audience: str = "general"  # general/student/expert
    explanation_style: str = "educational"  # simple/detailed/technical
    include_examples: bool = True
    language: str = "ru"
```

**Выходные данные:**
```python
class ExplanationResult(BaseModel):
    topic: str
    explanation: str              # Основное объяснение
    examples: List[str]          # Практические примеры
    analogies: List[str]         # Аналогии для понимания
    key_concepts: List[str]      # Ключевые концепции
    difficulty_level: str        # beginner/intermediate/advanced
    estimated_reading_time: int   # В минуты
    clarity_score: float         # Оценка понятности
```

**Процесс работы:**
1. Анализ research данных
2. Выбор стратегии объяснения на основе аудитории
3. Генерация основного объяснения через GPT-4
4. Создание практических примеров
5. Формирование аналогий
6. Оценка понятности и сложности

**Промпты:**
```python
SYSTEM_PROMPT = """
Ты эксперт-педагог с многолетним опытом объяснения сложных концепций.
Твоя задача - создать понятное, структурированное объяснение понятия.
Используй простой язык, но не упрощай научную сущность.
Включай релевантные примеры и аналогии.
"""

EXPLANATION_PROMPT_TEMPLATE = """
Объясни понятие "{topic}" для {audience} в стиле {style}.
Основываясь на следующих исследовательских данных:
{research_data}

Требования:
1. Четкая структура (определение, детали, примеры)
2. Практические примеры из реальной жизни
3. Аналогии для упрощения понимания
4. Длина объяснения: 300-500 слов
5. Язык: {language}
"""
```

**Критерии качества:**
- Понятность объяснения: ≥ 80%
- Актуальность примеров: ≥ 75%
- Структура текста: ≥ 85%
- Соответствие аудитории: ≥ 80%

---

### SynthesisAgent - Агент синтеза информации

**Назначение:** Объединение результатов research и explanation в финальное описание

**Входные данные:**
```python
class SynthesisInput(BaseModel):
    topic: str
    research_result: ResearchResult
    explanation_result: ExplanationResult
    synthesis_type: str = "comprehensive"  # brief/comprehensive/detailed
    target_format: str = "structured"       # structured/narrative/bulleted
```

**Выходные данные:**
```python
class SynthesisResult(BaseModel):
    topic: str
    final_description: str        # Финальное описание
    key_insights: List[str]       # Ключевые инсайты
    practical_applications: List[str]  # Практическое применение
    related_concepts: List[str]   # Связанные концепции
    summary_points: List[str]     # Основные тезисы
    coherence_score: float        # Оценка связности
    completeness_score: float     # Оценка полноты
```

**Процесс работы:**
1. Сравнение и анализ всех источников данных
2. Идентификация противоречий и дубликатов
3. Создание единой нарративной линии
4. Выделение ключевых моментов
5. Формирование практических применений
6. Оценка связности и полноты

**Стратегии синтеза:**
```python
SYNTHESIS_STRATEGIES = {
    "comprehensive": {
        "merge_all_sources": True,
        "prioritize_explanation": False,
        "include_examples": True,
        "add_context": True
    },
    "brief": {
        "merge_all_sources": True,
        "prioritize_explanation": True,
        "include_examples": False,
        "add_context": False
    },
    "detailed": {
        "merge_all_sources": True,
        "prioritize_explanation": False,
        "include_examples": True,
        "add_context": True,
        "expand_details": True
    }
}
```

**Критерии качества:**
- Связность текста: ≥ 85%
- Полнота покрытия: ≥ 80%
- Отсутствие дубликатов: ≥ 90%
- Логическая структура: ≥ 85%

---

## ЭТАП 2: АГЕНТЫ ПРЕЗЕНТАЦИИ

### PresentationAgent - Агент создания презентации

**Назначение:** Создание презентации на 1 минуту с 4-5 слайдами

**Входные данные:**
```python
class PresentationInput(BaseModel):
    topic: str
    synthesis_result: SynthesisResult
    target_duration: int = 60      # Секунды
    max_slides: int = 5
    min_slides: int = 4
    presentation_style: str = "educational"  # educational/professional/casual
```

**Выходные данные:**
```python
class PresentationResult(BaseModel):
    topic: str
    slides: List[Slide]
    total_duration: int           # Секунды
    slide_timings: List[int]      # Время на каждый слайд
    narrative_flow: str           # Описание нарратива
    visual_suggestions: List[str] # Рекомендации по визуализации
    structure_score: float        # Оценка структуры
```

```python
class Slide(BaseModel):
    slide_number: int
    title: str
    content: str                 # Текст слайда
    speaker_notes: str           # Заметки спикера
    duration_estimate: int       # Секунды
    visual_type: str            # image/chart/diagram/text
    visual_description: str     # Описание желаемой визуализации
```

**Процесс работы:**
1. Анализ объема и сложности контента
2. Разделение на логические блоки для слайдов
3. Создание структуры (введение, основная часть, заключение)
4. Расчет времени на каждый слайд
5. Формирование рекомендаций по визуализации
6. Проверка общего времени (60 секунд)

**Структура презентации:**
```python
PRESENTATION_STRUCTURE = {
    "slide_1": "Введение - определение и актуальность темы",
    "slide_2": "Основные концепции и принципы",
    "slide_3": "Практические примеры и применение",
    "slide_4": "Ключевые выводы и перспективы",
    "slide_5": "Заключение и призыв к действию (опционально)"
}
```

**Критерии качества:**
- Соответствие времени: ±5 секунд от 60
- Логическая последовательность: ≥ 85%
- Баланс текста/визуализации: ≥ 80%
- Ясность структуры: ≥ 85%

---

### ImageGeneratorAgent - Агент генерации изображений

**Назначение:** Генерация изображений для слайдов презентации

**Входные данные:**
```python
class ImageGenerationInput(BaseModel):
    slides: List[Slide]
    image_style: str = "educational_clean"  # educational_clean/modern/minimalist
    color_scheme: str = "professional"      # professional/vibrant/monochrome
    consistency_level: str = "high"        # low/medium/high
```

**Выходные данные:**
```python
class ImageGenerationResult(BaseModel):
    generated_images: List[GeneratedImage]
    style_consistency_score: float
    relevance_scores: List[float]
    total_generation_time: float
```

```python
class GeneratedImage(BaseModel):
    slide_number: int
    image_url: str
    prompt_used: str
    generation_metadata: Dict[str, Any]
    relevance_score: float
    style_compliance: float
```

**Процесс работы:**
1. Анализ каждого слайда для определения визуальных потребностей
2. Генерация промптов для DALL-E 3
3. Пакетная генерация изображений
4. Проверка релевантности и стиля
5. Регенерация при необходимости
6. Формирование финального набора

**Промпты для генерации:**
```python
PROMPT_TEMPLATES = {
    "concept_diagram": "Create a clean, educational diagram showing {concept} with clear labels and professional colors. Minimalist style, white background.",
    "process_flow": "Illustrate the process of {process} as a step-by-step flow chart. Educational style, blue and gray color scheme.",
    "example_visual": "Create a simple, clear visual representation of {example} for educational purposes. Clean lines, professional appearance.",
    "abstract_concept": "Design an abstract visualization of {concept} using geometric shapes and gradients. Educational, modern style."
}
```

**Критерии качества:**
- Релевантность содержанию: ≥ 75%
- Соответствие стилю: ≥ 80%
- Консистентность между слайдами: ≥ 70%
- Визуальная ясность: ≥ 85%

---

## ЭТАП 3: АГЕНТЫ МЕДИА

### AudioAgent - Агент генерации аудио

**Назначение:** Создание аудиофайла с голосовым сопровождением презентации

**Входные данные:**
```python
class AudioInput(BaseModel):
    presentation_result: PresentationResult
    voice_settings: VoiceSettings
    audio_format: str = "mp3"
    sample_rate: int = 44100
```

```python
class VoiceSettings(BaseModel):
    voice_id: str = "rachel"           # ElevenLabs voice ID
    model: str = "eleven_monolingual_v1"
    stability: float = 0.75
    similarity_boost: float = 0.75
    style: str = "educational"         # educational/conversational/professional
    speed: float = 1.0                # 0.8 - 1.2
```

**Выходные данные:**
```python
class AudioResult(BaseModel):
    audio_file_url: str
    duration: float                    # Секунды
    text_synchronized: bool
    voice_quality_score: float
    pronunciation_score: float
    synchronization_metadata: Dict
```

**Процесс работы:**
1. Создание скрипта из презентации
2. Оптимизация текста для речи
3. Генерация аудио через ElevenLabs
4. Проверка качества и произношения
5. Синхронизация с таймингами слайдов
6. Финальная обработка аудио

**Скрипт генерация:**
```python
def generate_speech_script(presentation: PresentationResult) -> str:
    script = f"Здравствуйте! Сегодня мы поговорим о {presentation.topic}. "
    
    for slide in presentation.slides:
        script += f"\n\n{slide.content} "
        script += f"{slide.speaker_notes} "
    
    return optimize_for_speech(script)  # Удаление сложных конструкций
```

**Критерии качества:**
- Качество голоса: ≥ 75%
- Произношение и интонация: ≥ 80%
- Синхронизация с презентацией: ≥ 90%
- Понятность речи: ≥ 85%

---

### VideoAgent - Агент генерации видео

**Назначение:** Создание финального видеоролика с изображениями и голосом

**Входные данные:**
```python
class VideoInput(BaseModel):
    presentation_result: PresentationResult
    image_generation_result: ImageGenerationResult
    audio_result: AudioResult
    video_settings: VideoSettings
```

```python
class VideoSettings(BaseModel):
    resolution: str = "1080p"          # 720p/1080p/4k
    fps: int = 30
    transition_style: str = "fade"      # fade/slide/zoom
    background_music: bool = False
    subtitle_style: str = "clean"       # clean/modern/bold
```

**Выходные данные:**
```python
class VideoResult(BaseModel):
    video_url: str
    duration: float                    # Секунды
    file_size: int                     # MB
    quality_score: float
    synchronization_score: float
    rendering_metadata: Dict[str, Any]
```

**Процесс работы:**
1. Подготовка медиа-ресурсов (изображения, аудио)
2. Создание временной шкалы видео
3. Наложение изображений с переходами
4. Синхронизация аудио с визуализацией
5. Добавление субтитров (опционально)
6. Финальная сборка и оптимизация

**Структура видео:**
```python
VIDEO_TIMELINE = {
    "intro": 5,        # seconds
    "slide_1": 12,
    "slide_2": 12,
    "slide_3": 12,
    "slide_4": 12,
    "slide_5": 12,
    "outro": 5
}
```

**Технические требования:**
- Формат: MP4 (H.264)
- Аудио: AAC, 44.1kHz
- Субтитры: SRT (опционально)
- Максимальный размер: 50MB

**Критерии качества:**
- Синхронизация аудио/видео: ≥ 80%
- Визуальное качество: ≥ 75%
- Общая производительность: ≥ 80%
- Размер файла: ≤ 50MB

---

## ОБЩИЕ КОНФИГУРАЦИОННЫЕ ПАРАМЕТРЫ

### Пороговые качества
```python
QUALITY_THRESHOLDS = {
    "research": 0.70,
    "explanation": 0.80,
    "synthesis": 0.80,
    "presentation": 0.85,
    "image_generation": 0.75,
    "audio": 0.75,
    "video": 0.80
}
```

### Таймауты
```python
TIMEOUTS = {
    "research": 30,
    "explanation": 45,
    "synthesis":
