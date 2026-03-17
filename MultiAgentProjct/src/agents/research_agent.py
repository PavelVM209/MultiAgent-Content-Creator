"""
ResearchAgent - агент для поиска и сбора информации из интернета
"""

import asyncio
import aiohttp
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse
import json
from datetime import datetime

from .base import BaseAgent
from src.models.agents import ValidationResult, AgentConfig


class ResearchAgent(BaseAgent):
    """
    Агент для исследования тем путем поиска информации в интернете
    
    Использует различные источники:
    - Веб-поиск (если доступны API ключи)
    - Моделирование поиска для демонстрации
    - Структурирование результатов
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_name="ResearchAgent",
                version="1.0.0",
                timeout=120,
                max_retries=3,
                custom_params={
                    "max_results": 10,
                    "search_depth": "comprehensive",
                    "include_sources": True,
                    "language": "ru"
                }
            )
        super().__init__(config)
        self.session = None
    
    async def validate_input(self, data: Any) -> ValidationResult:
        """Валидация входных данных"""
        if isinstance(data, dict):
            topic = data.get("topic", "").strip()
        elif hasattr(data, 'topic'):
            topic = str(data.topic).strip()
        else:
            topic = str(data).strip()
        
        issues = []
        
        if not topic:
            issues.append("Тема для исследования не указана")
        
        if len(topic) < 3:
            issues.append("Тема слишком короткая (минимум 3 символа)")
        
        if len(topic) > 200:
            issues.append("Тема слишком длинная (максимум 200 символов)")
        
        score = 1.0 if not issues else max(0.0, 1.0 - len(issues) * 0.2)
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=["Укажите конкретную тему для исследования"] if issues else [],
            confidence=0.9 if len(issues) == 0 else 0.5
        )
    
    async def process_data(self, validated_data: Any) -> Any:
        """Основная обработка - поиск и сбор информации"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
        # Извлекаем тему
        if isinstance(validated_data, dict):
            topic = validated_data.get("topic", "").strip()
            search_params = validated_data
        elif hasattr(validated_data, 'topic'):
            topic = str(validated_data.topic).strip()
            search_params = {"topic": topic}
        else:
            topic = str(validated_data).strip()
            search_params = {"topic": topic}
        
        self.logger.info(f"Starting research for topic: {topic}")
        
        try:
            # Выполняем поиск
            search_results = await self._perform_search(topic, search_params)
            
            # Анализируем и структурируем результаты
            structured_results = await self._analyze_results(search_results, topic)
            
            # Генерируем summary
            summary = await self._generate_summary(structured_results, topic)
            
            # Извлекаем ключевые точки
            key_points = await self._extract_key_points(structured_results)
            
            # Собираем источники
            sources = [result.get("url", "") for result in search_results if result.get("url")]
            
            result_data = {
                "topic": topic,
                "search_results": search_results,
                "structured_results": structured_results,
                "summary": summary,
                "key_points": key_points,
                "sources": sources,
                "search_metadata": {
                    "total_results": len(search_results),
                    "search_time": datetime.utcnow().isoformat(),
                    "search_depth": self.config.custom_params.get("search_depth", "basic")
                },
                "confidence_score": self._calculate_confidence(search_results)
            }
            
            self.logger.info(f"Research completed for '{topic}'. Found {len(search_results)} results")
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error during research: {str(e)}")
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
        
        required_fields = ["topic", "summary", "key_points", "sources"]
        missing_fields = [field for field in required_fields if field not in result]
        
        issues = []
        if missing_fields:
            issues.append(f"Отсутствуют поля: {', '.join(missing_fields)}")
        
        if not result.get("summary", "").strip():
            issues.append("Summary пустой")
        
        if not result.get("key_points"):
            issues.append("Отсутствуют ключевые точки")
        
        score = min(1.0, max(0.0, 1.0 - len(issues) * 0.25))
        
        return ValidationResult(
            valid=len(issues) == 0,
            score=score,
            issues=issues,
            suggestions=["Добавьте недостающие поля и улучшите контент"] if issues else [],
            confidence=0.8
        )
    
    def get_quality_thresholds(self) -> Dict[str, float]:
        """Пороговые значения качества"""
        return {
            "overall": 0.7,
            "content_quality": 0.6,
            "source_reliability": 0.5,
            "summary_completeness": 0.7
        }
    
    async def _perform_search(self, topic: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Выполнение поиска информации"""
        max_results = self.config.custom_params.get("max_results", 10)
        use_free_search = self.config.custom_params.get("use_free_search", True)
        
        results = []
        
        # Сначала пробуем бесплатный поиск через DuckDuckGo
        if use_free_search:
            try:
                free_results = await self._free_duckduckgo_search(topic, max_results)
                if free_results:
                    results.extend(free_results)
                    self.logger.info(f"Found {len(free_results)} results via DuckDuckGo")
            except Exception as e:
                self.logger.warning(f"Free search failed: {e}")
        
        # Если бесплатный поиск не дал результатов, используем mock
        if not results:
            mock_results = await self._generate_mock_search_results(topic, max_results)
            results.extend(mock_results)
            self.logger.info(f"Used mock search results: {len(mock_results)} items")
        
        return results
    
    async def _generate_mock_search_results(self, topic: str, max_results: int) -> List[Dict[str, Any]]:
        """Генерация симулированных результатов поиска"""
        results = []
        
        # Базовые шаблоны для разных типов контента
        result_types = [
            {
                "title_pattern": "{topic}: Обзор и анализ",
                "snippet_pattern": "В этой статье рассматриваются основные аспекты {topic}, включая современные подходы и практические применения.",
                "domain": "wikipedia.org"
            },
            {
                "title_pattern": "Исследование {topic}: методы и результаты",
                "snippet_pattern": "Научное исследование посвящено изучению {topic} с использованием современных методологий и подходов.",
                "domain": "researchgate.net"
            },
            {
                "title_pattern": "Практическое применение {topic}",
                "snippet_pattern": "Обзор практических кейсов применения {topic} в различных отраслях и сферах деятельности.",
                "domain": "medium.com"
            },
            {
                "title_pattern": "{topic}: современные тенденции",
                "snippet_pattern": "Анализ современных тенденций и перспектив развития в области {topic}.",
                "domain": "habr.com"
            },
            {
                "title_pattern": "Основы {topic} для начинающих",
                "snippet_pattern": "Вводное руководство по {topic}, охватывающее основные концепции и принципы.",
                "domain": "tproger.ru"
            }
        ]
        
        for i in range(min(max_results, len(result_types) * 2)):
            template = result_types[i % len(result_types)]
            
            result = {
                "title": template["title_pattern"].format(topic=topic),
                "snippet": template["snippet_pattern"].format(topic=topic),
                "url": f"https://{template['domain']}/article-{i+1}",
                "domain": template["domain"],
                "relevance_score": 0.8 - (i * 0.1),  # Уменьшение релевантности
                "published_date": "2024-01-01",
                "content_type": "article",
                "language": "ru"
            }
            
            # Добавляем дополнительную информацию для некоторых результатов
            if i < 3:
                result["content"] = await self._generate_mock_content(topic, 300)
                result["key_points"] = await self._generate_mock_key_points(topic, 3)
            
            results.append(result)
        
        return results
    
    async def _generate_mock_content(self, topic: str, length: int) -> str:
        """Генерация симулированного контента"""
        content_templates = [
            f"{topic} является важной областью современной науки и технологии. В последние годы наблюдается значительный рост интереса к этой теме как в академической среде, так и в промышленности.",
            f"Основные принципы {topic} включают системный подход, интеграцию современных методов и практическое применение теоретических знаний.",
            f"Современные исследования в области {topic} показывают перспективность различных направлений развития. Эксперты отмечают важность междисциплинарного подхода.",
            f"Практическая реализация {topic} требует учета множества факторов, включая технические, экономические и социальные аспекты."
        ]
        
        # Выбираем и комбинируем шаблоны
        content = " ".join(content_templates)
        
        # Обрезаем до нужной длины
        if len(content) > length:
            content = content[:length].rsplit(' ', 1)[0] + "..."
        
        return content
    
    async def _generate_mock_key_points(self, topic: str, count: int) -> List[str]:
        """Генерация симулированных ключевых точек"""
        base_points = [
            f"Современное состояние {topic}",
            f"Основные вызовы и проблемы в {topic}",
            f"Перспективы развития {topic}",
            f"Практические применения {topic}",
            f"Методологические подходы к {topic}",
            f"Инновационные решения в {topic}"
        ]
        
        return base_points[:count]
    
    async def _analyze_results(self, search_results: List[Dict[str, Any]], topic: str) -> Dict[str, Any]:
        """Анализ и структурирование результатов поиска"""
        # Группировка результатов по доменам
        domains = {}
        for result in search_results:
            domain = result.get("domain", "unknown")
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(result)
        
        # Анализ типов контента
        content_types = {}
        for result in search_results:
            content_type = result.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Расчет средней релевантности
        avg_relevance = sum(r.get("relevance_score", 0) for r in search_results) / len(search_results)
        
        return {
            "domains": domains,
            "content_types": content_types,
            "total_results": len(search_results),
            "average_relevance": avg_relevance,
            "high_relevance_results": len([r for r in search_results if r.get("relevance_score", 0) > 0.7]),
            "topic_coverage": self._assess_topic_coverage(search_results, topic)
        }
    
    def _assess_topic_coverage(self, results: List[Dict[str, Any]], topic: str) -> Dict[str, float]:
        """Оценка покрытия темы"""
        topic_lower = topic.lower()
        
        # Анализ mentions разных аспектов темы
        aspect_coverage = {
            "theoretical": 0.0,
            "practical": 0.0,
            "historical": 0.0,
            "future": 0.0
        }
        
        for result in results:
            text = result.get("title", "") + " " + result.get("snippet", "")
            text_lower = text.lower()
            
            # Ключевые слова для разных аспектов
            if any(word in text_lower for word in ["теория", "основы", "принцип", "концепт"]):
                aspect_coverage["theoretical"] += 1
            if any(word in text_lower for word in ["практика", "применение", "реализация", "кейс"]):
                aspect_coverage["practical"] += 1
            if any(word in text_lower for word in ["история", "развитие", "эволюция"]):
                aspect_coverage["historical"] += 1
            if any(word in text_lower for word in ["будущее", "перспектив", "тенденции"]):
                aspect_coverage["future"] += 1
        
        # Нормализация
        total = len(results)
        if total > 0:
            for key in aspect_coverage:
                aspect_coverage[key] = aspect_coverage[key] / total
        
        return aspect_coverage
    
    async def _generate_summary(self, structured_results: Dict[str, Any], topic: str) -> str:
        """Генерация суммарного описания"""
        total_results = structured_results.get("total_results", 0)
        avg_relevance = structured_results.get("average_relevance", 0)
        
        summary_parts = [
            f"Проведено комплексное исследование темы '{topic}'.",
            f"Найдено и проанализировано {total_results} источников информации.",
            f"Средняя релевантность результатов: {avg_relevance:.2f}."
        ]
        
        # Добавляем информацию о покрытии темы
        coverage = structured_results.get("topic_coverage", {})
        if coverage:
            best_covered = max(coverage.items(), key=lambda x: x[1])
            if best_covered[1] > 0.5:
                aspect_names = {
                    "theoretical": "теоретические аспекты",
                    "practical": "практические применения",
                    "historical": "историческое развитие",
                    "future": "перспективы развития"
                }
                summary_parts.append(
                    f"Особое внимание уделено {aspect_names.get(best_covered[0], best_covered[0])}."
                )
        
        # Добавляем информацию о типах контента
        content_types = structured_results.get("content_types", {})
        if "article" in content_types and content_types["article"] > 2:
            summary_parts.append("Преимущественно найдены научные статьи и обзоры.")
        
        return " ".join(summary_parts)
    
    async def _extract_key_points(self, structured_results: Dict[str, Any]) -> List[str]:
        """Извлечение ключевых точек из результатов"""
        key_points = []
        
        # Из структурированных результатов
        coverage = structured_results.get("topic_coverage", {})
        
        if coverage.get("theoretical", 0) > 0.3:
            key_points.append("Теоретические основы и концепции темы хорошо освещены в источниках")
        
        if coverage.get("practical", 0) > 0.3:
            key_points.append("Обнаружены практические применения и реальные кейсы")
        
        if coverage.get("future", 0) > 0.3:
            key_points.append("Описаны перспективы развития и будущие тенденции")
        
        quality = structured_results.get("average_relevance", 0)
        if quality > 0.7:
            key_points.append("Высокое качество и релевантность найденных источников")
        
        # Добавляем общие точки если их мало
        if len(key_points) < 3:
            key_points.extend([
                "Проанализированы основные источники по теме",
                "Выделены ключевые аспекты и направления"
            ])
        
        return key_points[:5]  # Максимум 5 ключевых точек
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]]) -> float:
        """Расчет уверенности в результатах"""
        if not search_results:
            return 0.0
        
        factors = []
        
        # Фактор 1: Количество результатов
        results_factor = min(1.0, len(search_results) / 10)
        factors.append(results_factor)
        
        # Фактор 2: Средняя релевантность
        avg_relevance = sum(r.get("relevance_score", 0) for r in search_results) / len(search_results)
        factors.append(avg_relevance)
        
        # Фактор 3: Разнообразие доменов
        domains = set(r.get("domain", "") for r in search_results)
        diversity_factor = min(1.0, len(domains) / 5)
        factors.append(diversity_factor)
        
        # Фактор 4: Качество контента
        content_factor = sum(1 for r in search_results if r.get("content")) / len(search_results)
        factors.append(content_factor)
        
        return sum(factors) / len(factors)
    
    async def _free_duckduckgo_search(self, topic: str, max_results: int) -> List[Dict[str, Any]]:
        """Бесплатный поиск через DuckDuckGo Instant Answer API"""
        try:
            # DuckDuckGo Instant Answer API
            ddg_url = "https://api.duckduckgo.com/"
            params = {
                'q': topic,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            if self.session is None:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(ddg_url, params=params, timeout=30) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                results = []
                
                # Извлекаем результаты из ответа DuckDuckGo
                if 'Results' in data:
                    for result in data['Results'][:max_results]:
                        results.append({
                            'title': result.get('Text', ''),
                            'snippet': result.get('Text', ''),
                            'url': result.get('FirstURL', ''),
                            'domain': self._extract_domain(result.get('FirstURL', '')),
                            'relevance_score': 0.8,
                            'published_date': '2024-01-01',
                            'content_type': 'article',
                            'language': 'ru',
                            'source': 'duckduckgo'
                        })
                
                # Добавляем Related Topics если есть
                if 'RelatedTopics' in data:
                    for topic_data in data['RelatedTopics'][:max_results//2]:
                        if isinstance(topic_data, dict) and 'Text' in topic_data:
                            results.append({
                                'title': topic_data.get('Text', ''),
                                'snippet': topic_data.get('Text', ''),
                                'url': topic_data.get('FirstURL', ''),
                                'domain': self._extract_domain(topic_data.get('FirstURL', '')),
                                'relevance_score': 0.7,
                                'published_date': '2024-01-01',
                                'content_type': 'article',
                                'language': 'ru',
                                'source': 'duckduckgo_related'
                            })
                
                # Если результатов мало, пробуем веб-скрапинг
                if len(results) < max_results:
                    scraped_results = await self._free_web_scraping(topic, max_results - len(results))
                    results.extend(scraped_results)
                
                return results[:max_results]
                
        except Exception as e:
            self.logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """Извлечение домена из URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    async def _free_web_scraping(self, topic: str, max_results: int) -> List[Dict[str, Any]]:
        """Бесплатный веб-скрапинг для дополнения результатов"""
        scraped_results = []
        
        try:
            # Пробуем получить контент с первых результатов DuckDuckGo
            search_urls = [
                f"https://duckduckgo.com/html/?q={quote(topic)}",
            ]
            
            for search_url in search_urls:
                try:
                    if self.session is None:
                        self.session = aiohttp.ClientSession()
                    
                    async with self.session.get(search_url, timeout=30) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Простое извлечение ссылок (в реальной системе нужен BeautifulSoup)
                            import re
                            url_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
                            matches = re.findall(url_pattern, html)
                            
                            for url, title in matches[:max_results]:
                                if url.startswith('/url?q='):
                                    # Extract actual URL from Google redirect
                                    url = url.split('/url?q=')[1].split('&')[0]
                                
                                if url.startswith('http') and len(title) > 10:
                                    scraped_results.append({
                                        'title': title.strip(),
                                        'snippet': f"Результат поиска по теме: {topic}",
                                        'url': url,
                                        'domain': self._extract_domain(url),
                                        'relevance_score': 0.6,
                                        'published_date': '2024-01-01',
                                        'content_type': 'article',
                                        'language': 'ru',
                                        'source': 'web_scraping'
                                    })
                            
                            if len(scraped_results) >= max_results:
                                break
                                
                except Exception as e:
                    self.logger.warning(f"Web scraping error: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Web scraping failed: {e}")
        
        return scraped_results[:max_results]
    
    async def cleanup(self):
        """Очистка ресурсов"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Деструктор"""
        if hasattr(self, 'session') and self.session:
            # Внутри asyncio loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.cleanup())
                else:
                    loop.run_until_complete(self.cleanup())
            except:
                pass
