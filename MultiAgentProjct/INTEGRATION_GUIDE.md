# 🧠 Интеграция с реальными нейросетями - Полноправный запуск системы

## 🎯 Обзор

Текущая система использует мок-данные для демонстрации архитектуры. Для получения реальных результатов необходимо интегрировать внешние API нейросетей.

## 📋 План интеграции

### 🔥 Критически необходимые компоненты

#### 1. **ResearchAgent - Поиск информации**
**Что нужно:** Google Search API / SerpApi / Bing Search API
**Текущий статус:** Мок-данные
**Интеграция:**
```python
# Заменить _mock_internet_search() на:
import requests
from googleapiclient.discovery import build

class RealResearchAgent(ResearchAgent):
    def __init__(self):
        super().__init__()
        self.search_api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    async def _real_internet_search(self, query: str):
        service = build("customsearch", "v1", developerKey=self.search_api_key)
        result = service.cse().list(q=query, cx=self.search_engine_id).execute()
        return self._process_search_results(result)
```

**Стоимость:** ~$5-20/месяц за 1000-10000 запросов

---

#### 2. **ExplanationAgent & SynthesisAgent - Текстовая генерация**
**Что нужно:** OpenAI GPT-4 / Claude 3 / Anthropic API
**Текущий статус:** Мок-данные
**Интеграция:**
```python
# Заменить _mock_explanation() на:
import openai

class RealExplanationAgent(ExplanationAgent):
    def __init__(self):
        super().__init__()
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    async def _real_generate_explanation(self, research_data):
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты - эксперт по объяснению сложных тем"},
                {"role": "user", "content": self._create_prompt(research_data)}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
```

**Стоимость:** ~$20-100/месяц в зависимости от объема

---

#### 3. **ImageGeneratorAgent - Генерация изображений**
**Что нужно:** DALL-E 3 / Midjourney API / Stable Diffusion
**Текущий статус:** Мок-изображения с PIL
**Интеграция:**
```python
# Заменить _mock_generate_images() на:
import openai

class RealImageGeneratorAgent(ImageGeneratorAgent):
    def __init__(self):
        super().__init__()
        openai.api_key = os.getenv("OPENAI_API_KEY")
    
    async def _real_generate_images(self, slide_number, title, content, slide_type):
        prompts = self._create_image_prompts(title, content, slide_type)
        images = []
        
        for prompt in prompts[:2]:  # Максимум 2 изображения на слайд
            response = await openai.Image.acreate(
                prompt=prompt,
                n=1,
                size="1024x1024",
                model="dall-e-3"
            )
            
            image_url = response['data'][0]['url']
            image_path = await self._download_image(image_url, slide_number, prompt)
            
            images.append({
                "path": image_path,
                "prompt": prompt,
                "type": slide_type
            })
        
        return images
```

**Стоимость:** ~$30-150/месяц

---

#### 4. **AudioAgent - Синтез речи**
**Что нужно:** ElevenLabs API / Google TTS / Azure Speech
**Текущий статус:** Мок-аудио с numpy
**Интеграция:**
```python
# Заменить _mock_generate_audio() на:
import requests
from elevenlabs import generate, save

class RealAudioAgent(AudioAgent):
    def __init__(self):
        super().__init__()
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = "rachel"  # Natural female voice
    
    async def _real_generate_audio(self, segment_number, text):
        audio = generate(
            text=text,
            voice=self.voice_id,
            api_key=self.elevenlabs_api_key
        )
        
        filename = f"audio_segment_{segment_number:03d}.mp3"
        filepath = self.output_dir / filename
        save(audio, filepath)
        
        return {
            "filename": filename,
            "path": str(filepath),
            "duration_seconds": len(text) * 0.08  # Приблизительно
        }
```

**Стоимость:** ~$10-50/месяц

---

#### 5. **VideoAgent - Сборка видео**
**Что нужно:** FFmpeg / RunwayML / Synthesia
**Текущий статус:** Мок-видео
**Интеграция:**
```python
# Заменить _real_generate_video() на:
import subprocess
from moviepy.editor import *

class RealVideoAgent(VideoAgent):
    def __init__(self):
        super().__init__()
        self.ffmpeg_path = "/usr/local/bin/ffmpeg"  # Путь к FFmpeg
    
    async def _real_assemble_video(self, video_segments, audio_file):
        clips = []
        
        for segment in video_segments:
            # Создаем клип из изображения
            image_clip = ImageFileClip(segment["image_path"])
            image_clip = image_clip.set_duration(segment["duration"])
            image_clip = image_clip.resize((1920, 1080))
            clips.append(image_clip)
        
        # Соединяем все клипы
        video = concatenate_videoclips(clips)
        
        # Добавляем аудио
        audio = AudioFileClip(audio_file["path"])
        video = video.set_audio(audio)
        
        # Сохраняем финальное видео
        filename = f"presentation_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = self.output_dir / filename
        
        video.write_videofile(
            str(filepath),
            fps=30,
            codec='h264',
            audio_codec='aac'
        )
        
        return {
            "filename": filename,
            "path": str(filepath),
            "duration_seconds": video.duration
        }
```

**Стоимость:** FFmpeg бесплатно, либо ~$20-100/месяц за cloud решение

---

## 🛠️ Требуемые изменения в коде

### 1. **Конфигурация окружения**
```bash
# .env файл
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
ELEVENLABS_API_KEY=your-elevenlabs-api-key
MIDJOURNEY_API_KEY=your-midjourney-key
```

### 2. **Установка зависимостей**
```bash
# requirements.txt добавить:
openai>=1.0.0
google-api-python-client>=2.0.0
elevenlabs>=0.2.0
moviepy>=1.0.3
requests>=2.28.0
pillow>=9.0.0
ffmpeg-python>=0.2.0
```

### 3. **Активация реальных API**
В каждом агенте заменить флаг `use_mock_generation` на `False`:

```python
# В __init__ каждого агента
custom_params={
    "use_mock_generation": False  # Использовать реальные API
}
```

---

## 💰 Оценка стоимости

### Минимальная конфигурация (~$50/месяц):
- **OpenAI GPT-3.5**: $20/месяц
- **Google Search**: $5/месяц (1000 запросов)
- **DALL-E 3**: $20/месяц (100 изображений)
- **ElevenLabs**: $5/месяц (10,000 символов)

### Оптимальная конфигурация (~$200/месяц):
- **OpenAI GPT-4**: $100/месяц
- **Google Search**: $20/месяц (10,000 запросов)
- **DALL-E 3**: $60/месяц (500 изображений)
- **ElevenLabs**: $20/месяц (100,000 символов)

### Профессиональная конфигурация (~$500/месяц):
- **OpenAI GPT-4 + Claude 3**: $200/месяц
- **DALL-E 3 + Midjourney**: $150/месяц
- **Premium TTS**: $100/месяц
- **Cloud видео обработка**: $50/месяц

---

## 🚀 Пошаговый план внедрения

### Шаг 1: Настройка окружения (1 день)
1. Получить API ключи
2. Настроить .env файл
3. Установить зависимости

### Шаг 2: Интеграция текстовых API (2 дня)
1. Подключить OpenAI к ExplanationAgent
2. Подключить Search API к ResearchAgent
3. Тестирование и отладка

### Шаг 3: Интеграция медиа API (3 дня)
1. Подключить DALL-E к ImageGeneratorAgent
2. Подключить ElevenLabs к AudioAgent
3. Настроить FFmpeg для VideoAgent

### Шаг 4: Комплексное тестирование (2 дня)
1. Запуск полного workflow
2. Оптимизация параметров
3. Тестирование обработки ошибок

### Шаг 5: Мониторинг и оптимизация (1 день)
1. Настройка логирования API вызовов
2. Мониторинг расхода
3. Оптимизация промптов

---

## 🎯 Ожидаемые результаты

После интеграции система будет способна:

1. **Исследовать настоящие источники** из интернета
2. **Генерировать качественный текст** с помощью GPT-4
3. **Создавать уникальные изображения** через DALL-E 3
4. **Синтезировать естественную речь** через ElevenLabs
5. **Собирать профессиональное видео** с синхронизацией

**Качество output:** Промышленный уровень готовых презентаций

**Время выполнения:** 5-10 минут на полную презентацию

**Стоимость:** $1-5 за одну презентацию в зависимости от сложности

---

## ⚠️ Критические важные моменты

### 1. **Обработка ошибок API**
- Реинкорпорировать правила мониторинга для API ошибок
- Настроить retry механизмы
- Обработать лимиты api

### 2. **Оптимизация промптов**
- Создать эффективные промпты для каждого типа контента
- Тестировать и улучшать качество генерации
- Адаптировать под разные темы

### 3. **Контроль качества**
- Настроить дополнительную валидацию контента
- Проверять генерируемые изображения на качество
- Контролировать аудио на разборчивость

### 4. **Производительность**
- Оптимизировать размер изображений
- Кэшировать результаты поиска
- Параллелить запросы к API

---

## 🔄 Альтернативные варианты

### Бюджетный вариант (~$20/месяц):
- **Текст:** Вместо GPT-4 использовать локальные модели (Llama, Ollama)
- **Изображения:** Вместо DALL-E использовать Stable Diffusion локально
- **Поиск:** Бесплатные DuckDuckGo API
- **Аудио:** Бесплатный Google TTS

### Открытое решение (бесплатно):
- **Llama 3:** Локальная LLM модель
- **Stable Diffusion:** Локальная генерация изображений
- **Whisper:** Локальный speech-to-text (если нужно)
- **FFmpeg:** Бесплатная обработка видео

**Требования:** Мощный компьютер с GPU (16GB+ VRAM)

---

**🎯 Для запуска с настоящими нейросетями нужно внести изменения в 5 агентов, настроить API ключи и установить зависимости. Примерная стоимость интеграции: $50-500/месяц в зависимости от выбранного уровня качества.**

Готовы приступить к интеграции с реальными API?
