# 🆓 Бесплатная интеграция с нейросетями - Полный запуск без затрат

## 🎯 Обзор

Максимально бесплатный вариант с локальными и бесплатными API нейросетей. Качество будет ниже платных аналогов, но полностью функциональная система.

## 📋 План бесплатной интеграции

### 1. **ResearchAgent - Бесплатный поиск**
**Решение:** DuckDuckGo Instant Answer API + Web scraping
**Стоимость:** Абсолютно бесплатно
**Качество:** Хороший для базовых тем

```python
# Заменить _mock_internet_search() на:
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json

class FreeResearchAgent(ResearchAgent):
    def __init__(self):
        super().__init__()
        self.ddg_url = "https://api.duckduckgo.com/"
    
    async def _free_duckduckgo_search(self, query: str):
        """Бесплатный поиск через DuckDuckGo"""
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1,
            'skip_disambig': 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.ddg_url, params=params) as response:
                data = await response.json()
                
                results = []
                # Извлекаем результаты из ответа DDG
                if 'Results' in data:
                    for result in data['Results'][:5]:
                        results.append({
                            'title': result.get('Text', ''),
                            'url': result.get('FirstURL', ''),
                            'snippet': result.get('Text', '')
                        })
                
                return results
    
    async def _free_web_scraping(self, urls: list):
        """Парсинг контента с сайтов"""
        content_data = []
        
        for url in urls[:3]:  # Максимум 3 сайта
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.content_type.startswith('text/html'):
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Извлекаем текст из параграфов
                            paragraphs = soup.find_all('p')
                            content = ' '.join([p.get_text() for p in paragraphs[:5]])
                            
                            content_data.append({
                                'url': url,
                                'content': content[:1000],  # Ограничиваем размер
                                'title': soup.title.string if soup.title else ''
                            })
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue
                
        return content_data
    
    async def _free_internet_search(self, query: str):
        """Объединенный бесплатный поиск"""
        # 1. Поиск через DuckDuckGo
        search_results = await self._free_duckduckgo_search(query)
        
        # 2. Парсинг контента с топ сайтов
        urls = [result.get('url') for result in search_results if result.get('url')]
        scraped_content = await self._free_web_scraping(urls)
        
        # 3. Формируем результат
        return {
            'search_results': search_results,
            'scraped_content': scraped_content,
            'query': query,
            'total_sources': len(search_results) + len(scraped_content)
        }
```

---

### 2. **ExplanationAgent & SynthesisAgent - Локальные LLM**
**Решение:** Ollama + Llama 3 (или GPT4All)
**Стоимость:** Бесплатно, нужно 8GB+ RAM
**Качество:** Средний-good уровень

```python
# Сначала установка Ollama:
# curl -fsSL https://ollama.ai/install.sh | sh
# ollama pull llama3:8b  # 8GB модель

# Заменить _mock_explanation() на:
import requests
import json

class FreeExplanationAgent(ExplanationAgent):
    def __init__(self):
        super().__init__()
        self.ollama_url = "http://localhost:11434/api/generate"
        
    async def _check_ollama_available(self):
        """Проверяем доступность Ollama"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _ollama_generate(self, prompt: str, model="llama3:8b"):
        """Генерация через локальную Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1000
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                return None
        except Exception as e:
            print(f"Ollama error: {e}")
            return None
    
    async def _free_generate_explanation(self, research_data):
        """Бесплатная генерация объяснения"""
        # Проверяем доступность Ollama
        if not await self._check_ollama_available():
            # Fallback на простую шаблонизацию
            return self._simple_template_explanation(research_data)
        
        # Создаем промпт
        prompt = f"""
        Объясни простыми словами тему: "{research_data.get('topic', '')}"
        
        Исследовательские данные:
        {json.dumps(research_data.get('research_results', {}), indent=2, ensure_ascii=False)}
        
        Требования:
        1. Объясни как для начинающих
        2. Приведи 2-3 примера из жизни
        3. Выдели ключевые понятия
        4. Используй простой язык
        
        Ответ:
        """
        
        # Генерируем через Ollama
        explanation = await self._ollama_generate(prompt)
        
        if explanation:
            return explanation
        else:
            # Fallback на шаблоны
            return self._simple_template_explanation(research_data)
    
    def _simple_template_explanation(self, research_data):
        """Простое объяснение на основе шаблонов"""
        topic = research_data.get('topic', 'неизвестная тема')
        
        return f"""
        # Объяснение темы: {topic}
        
        ## Что это такое?
        {topic} - это важная область, которая изучает современные подходы к решению сложных задач.
        
        ## Основные понятия:
        • Концепт 1 - базовый элемент системы
        • Концепт 2 - метод анализа
        • Концепт 3 - практическое применение
        
        ## Примеры из жизни:
        1. В повседневной жизни мы сталкиваемся с {topic}
        2. Профессионалы используют {topic} для оптимизации процессов
        3. Будущее развития связано с {topic}
        
        ## Почему это важно?
        Понимание {topic} помогает принимать более обоснованные решения и видеть новые возможности.
        """
```

---

### 3. **ImageGeneratorAgent - Бесплатная генерация изображений**
**Решение:** Stable Diffusion Web UI / Civitai модели
**Стоимость:** Бесплатно, нужно GPU с 6GB+ VRAM
**Качество:** Средний уровень

```python
# Вариант 1: Stable Diffusion Web UI (if locally installed)
# Вариант 2: HuggingFace Diffusers (проще но медленнее)

from diffusers import StableDiffusionPipeline
import torch
from PIL import Image
import gc

class FreeImageGeneratorAgent(ImageGeneratorAgent):
    def __init__(self):
        super().__init__()
        self.model_loaded = False
        self.pipeline = None
        
    def _load_stable_diffusion(self):
        """Загрузка модели (делается один раз)"""
        try:
            # Используем небольшую модель для экономии памяти
            model_id = "runwayml/stable-diffusion-v1-5"
            
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                safety_checker=None,
                requires_safety_checker=False
            )
            
            if torch.cuda.is_available():
                self.pipeline = self.pipeline.to("cuda")
                
            self.model_loaded = True
            print("Stable Diffusion model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model_loaded = False
    
    async def _generate_with_stable_diffusion(self, prompt: str, slide_number: int, image_type: str):
        """Генерация через локальную Stable Diffusion"""
        if not self.model_loaded:
            self._load_stable_diffusion()
        
        if not self.model_loaded:
            return await self._fallback_image_generation(slide_number, image_type)
        
        try:
            # Генерируем изображение
            image = self.pipeline(
                prompt=prompt,
                num_inference_steps=20,  # Быстрее генерация
                guidance_scale=7.5,
                height=512,
                width=512
            ).images[0]
            
            # Сохраняем
            filename = f"slide_{slide_number:02d}_{image_type}_sd.png"
            filepath = self.output_dir / filename
            
            image.save(filepath)
            
            # Очищаем память
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            return {
                "filename": filename,
                "path": str(filepath),
                "prompt": prompt,
                "model": "stable-diffusion-v1-5",
                "width": 512,
                "height": 512
            }
            
        except Exception as e:
            print(f"Stable Diffusion error: {e}")
            return await self._fallback_image_generation(slide_number, image_type)
    
    async def _fallback_image_generation(self, slide_number: int, image_type: str):
        """Fallback генерация через PIL ( текущий метод)"""
        return await self._mock_generate_slide_image(slide_number, image_type)
    
    async def _free_generate_images(self, slide_number, title, content, slide_type):
        """Бесплатная генерация изображений"""
        # Создаем промпты
        prompts = self._create_image_prompts(title, content, slide_type)
        images = []
        
        for i, prompt in enumerate(prompts[:2]):  # Максимум 2 изображения
            try:
                # Генерируем через Stable Diffusion
                image_data = await self._generate_with_stable_diffusion(
                    prompt, slide_number, f"{slide_type}_{i+1}"
                )
                
                if image_data:
                    images.append(image_data)
                    
            except Exception as e:
                print(f"Error generating image {i}: {e}")
                # Fallback на PIL
                fallback = await self._fallback_image_generation(slide_number, f"{slide_type}_{i+1}")
                images.append(fallback)
        
        return images
```

---

### 4. **AudioAgent - Бесплатный синтез речи**
**Решение:** Mozilla TTS / gTTS (Google Translate TTS)
**Стоимость:** Абсолютно бесплатно
**Качество:** Базовый синтез речи

```python
# Вариант 1: gTTS (просто и надежно)
# pip install gtts

from gtts import gTTS
import pygame
import io

class FreeAudioAgent(AudioAgent):
    def __init__(self):
        super().__init__()
        # Инициализируем pygame для воспроизведения (если нужно)
        pygame.mixer.init()
        
    async def _generate_with_gtts(self, text: str, segment_number: int, lang='ru'):
        """Генерация через Google TTS"""
        try:
            # Создаем TTS объект
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # Сохраняем в файл
            filename = f"audio_segment_{segment_number:03d}_gtts.mp3"
            filepath = self.output_dir / filename
            
            tts.save(str(filepath))
            
            # Получаем длительность (приблизительно)
            duration_seconds = len(text.split()) * 0.5  # ~0.5с на слово
            
            return {
                "filename": filename,
                "path": str(filepath),
                "duration_seconds": duration_seconds,
                "model": "google-tts",
                "language": lang,
                "text_length": len(text)
            }
            
        except Exception as e:
            print(f"gTTS error: {e}")
            return await self._fallback_audio_generation(segment_number, text)
    
    async def _fallback_audio_generation(self, segment_number: int, text: str):
        """Fallback на текущий метод"""
        return await self._mock_generate_audio(segment_number, text)
    
    async def _free_generate_audio(self, segment_number, text):
        """Бесплатная генерация аудио"""
        # Разбиваем длинный текст на части
        max_length = 5000  # gTTS ограничение
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        # Генерируем через gTTS
        return await self._generate_with_gtts(text, segment_number, 'ru')
```

---

### 5. **VideoAgent - Бесплатная сборка видео**
**Решение:** FFmpeg + MoviePy (уже есть)
**Стоимость:** Абсолютно бесплатно
**Качество:** Хороший уровень

```python
# Только нужно убедиться что FFmpeg установлен
# brew install ffmpeg (Mac)
# apt install ffmpeg (Linux)

class FreeVideoAgent(VideoAgent):
    def __init__(self):
        super().__init__()
        self.ffmpeg_path = None
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Проверяем доступность FFmpeg"""
        import subprocess
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.ffmpeg_path = 'ffmpeg'
                print("FFmpeg available")
            else:
                print("FFmpeg not found, please install: brew install ffmpeg or apt install ffmpeg")
        except Exception as e:
            print(f"FFmpeg check failed: {e}")
    
    async def _free_assemble_video(self, video_segments, audio_file):
        """Бесплатная сборка видео через FFmpeg"""
        if not self.ffmpeg_path:
            return await self._mock_assemble_final_video(video_segments, audio_file)
        
        try:
            # Создаем список файлов для конкатенации
            concat_list = []
            
            for i, segment in enumerate(video_segments):
                # Создаем временный видеофайл из изображения
                temp_video = self.output_dir / f"temp_video_{i:03d}.mp4"
                
                # Конвертируем изображение в видео
                cmd = [
                    self.ffmpeg_path,
                    '-loop', '1',
                    '-i', segment['image_path'],
                    '-t', str(segment.get('duration', 5)),
                    '-r', '30',
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-y',
                    str(temp_video)
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                concat_list.append(str(temp_video))
            
            # Создаем файл списка для FFmpeg
            concat_file = self.output_dir / "concat_list.txt"
            with open(concat_file, 'w') as f:
                for video_file in concat_list:
                    f.write(f"file '{video_file}'\n")
            
            # Собираем финальное видео
            final_filename = f"presentation_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            final_filepath = self.output_dir / final_filename
            
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-i', audio_file['path'],
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                '-y',
                str(final_filepath)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Очищаем временные файлы
            for temp_file in concat_list:
                temp_file.unlink(missing_ok=True)
            concat_file.unlink(missing_ok=True)
            
            # Получаем длительность
            total_duration = sum(seg.get('duration', 0) for seg in video_segments)
            
            return {
                "filename": final_filename,
                "path": str(final_filepath),
                "duration_seconds": total_duration,
                "file_size_bytes": final_filepath.stat().st_size if final_filepath.exists() else 0,
                "codec": "h264",
                "resolution": "1024x768"
            }
            
        except Exception as e:
            print(f"FFmpeg assembly error: {e}")
            return await self._mock_assemble_final_video(video_segments, audio_file)
```

---

## 🛠️ **Пошаговая установка бесплатного стека**

### **Шаг 1: Системные требования (15 минут)**
```bash
# Минимальные требования:
# - RAM: 8GB+ (для Ollama)
# - VRAM: 6GB+ (для Stable Diffusion, опционально)
# - Диск: 20GB+ свободного места

# Проверяем:
python --version  # Python 3.8+
ffmpeg -version   # Должен быть установлен
```

### **Шаг 2: Установка FFmpeg (5 минут)**
```bash
# macOS:
brew install ffmpeg

# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# Windows:
# Скачать с https://ffmpeg.org/download.html и добавить в PATH
```

### **Шаг 3: Установка Ollama (10 минут)**
```bash
# Linux/macOS:
curl -fsSL https://ollama.ai/install.sh | sh

# Запускаем Ollama:
ollama serve  # В одном терминале

# Устанавливаем модель (8GB):
ollama pull llama3:8b

# Проверяем:
ollama list
```

### **Шаг 4
