# Определения Workflow MultiAgent Content Creator

## Основной Workflow: Content Creation Pipeline

### High-level описание
```
Пользовательский ввод (понятие) 
    ↓
[ЭТАП 1: ИССЛЕДОВАНИЕ]
    ↓
[ЭТАП 2: ПРЕЗЕНТАЦИЯ] 
    ↓
[ЭТАП 3: МЕДИА]
    ↓
Финальный видеоконтент (1 минута)
```

## Детальный Workflow

### ПРЕФАЗ: Валидация и подготовка

```python
class PrefphaseValidator:
    async def validate_topic(self, topic: str) -> ValidationResult:
        """Проверка валидности пользовательского ввода"""
        checks = [
            self._check_length(topic),      # 1-100 символов
            self._check_language(topic),    # Русский/English
            self._check_content(topic),     # Нет запрещенного контента
            self._check_feasibility(topic)  # Возможность исследования
        ]
        return ValidationResult(
            valid=all(check.passed for check in checks),
            score=sum(check.score for check in checks) / len(checks),
            issues=[check.issue for check in checks if not check.passed]
        )
```

### ЭТАП 1: ИССЛЕДОВАНИЕ ПОНЯТИЯ

#### Шаг 1.1: ResearchAgent
```python
class ResearchStep(BaseStep):
    agent = ResearchAgent()
    timeout = 30
    
    async def execute(self, topic: str) -> ResearchResult:
        # 1. Формирование поисковых запросов
        search_queries = self._generate_search_queries(topic)
        
        # 2. Параллельный поиск
        search_results = await asyncio.gather(*[
            self._search_google(query) for query in search_queries
        ])
        
        # 3. Валидация и фильтрация
        validated_results = [
            result for result in search_results
            if self._validate_source(result) > 0.7
        ]
        
        return ResearchResult(
            topic=topic,
            search_results=validated_results[:10],
            summary=self._generate_summary(validated_results),
            key_points=self._extract_key_points(validated_results)
        )
    
    def _generate_search_queries(self, topic: str) -> List[str]:
        return [
            f"что такое {topic}",
            f"{topic} определение",
            f"{topic} применение",
            f"{topic} примеры",
            f"{topic} объяснение простыми словами"
        ]
```

#### Quality Gate 1: Research Quality Check
```python
class ResearchQualityGate(QualityGate):
    threshold = 0.70
    
    async def evaluate(self, result: ResearchResult) -> QualityResult:
        metrics = {
            "relevance": await self._check_relevance(result),
            "source_count": min(len(result.sources) / 3, 1.0),
            "coverage": await self._check_coverage(result),
            "reliability": await self._check_source_reliability(result)
        }
        
        overall_score = sum(metrics.values()) / len(metrics)
        
        return QualityResult(
            score=overall_score,
            passed=overall_score >= self.threshold,
            details=metrics,
            issues=self._identify_issues(metrics)
        )
```

#### Шаг 1.2: ExplanationAgent
```python
class ExplanationStep(BaseStep):
    agent = ExplanationAgent()
    timeout = 45
    
    async def execute(self, research_result: ResearchResult) -> ExplanationResult:
        # 1. Анализ целевой аудитории
        audience = self._analyze_audience(research_result.topic)
        
        # 2. Выбор стратегии объяснения
        strategy = self._select_explanation_strategy(
            research_result.topic, 
            audience
        )
        
        # 3. Генерация объяснения
        explanation_prompt = self._build_explanation_prompt(
            research_result, 
            strategy
        )
        
        llm_response = await self.openai_client.generate(
            prompt=explanation_prompt,
            model="gpt-4",
            max_tokens=1000
        )
        
        # 4. Парсинг и структурирование
        parsed_result = self._parse_explanation_response(llm_response)
        
        return ExplanationResult(
            topic=research_result.topic,
            explanation=parsed_result.explanation,
            examples=parsed_result.examples,
            analogies=parsed_result.analogies,
            key_concepts=parsed_result.concepts
        )
```

#### Quality Gate 2: Explanation Quality Check
```python
class ExplanationQualityGate(QualityGate):
    threshold = 0.80
    
    async def evaluate(self, result: ExplanationResult) -> QualityResult:
        metrics = {
            "clarity": await self._assess_clarity(result.explanation),
            "examples_relevance": await self._check_examples(result.examples),
            "structure": await self._check_structure(result),
            "audience_match": await self._check_audience_match(result)
        }
        
        overall_score = sum(metrics.values()) / len(metrics)
        
        return QualityResult(
            score=overall_score,
            passed=overall_score >= self.threshold,
            details=metrics
        )
```

#### Шаг 1.3: SynthesisAgent
```python
class SynthesisStep(BaseStep):
    agent = SynthesisAgent()
    timeout = 30
    
    async def execute(self, 
                     research_result: ResearchResult,
                     explanation_result: ExplanationResult) -> SynthesisResult:
        
        # 1. Идентификация перекрытий и противоречий
        overlap_analysis = self._analyze_content_overlap(
            research_result, 
            explanation_result
        )
        
        # 2. Создание единой нарративной линии
        narrative = self._create_narrative_flow(
            research_result,
            explanation_result,
            overlap_analysis
        )
        
        # 3. Генерация финального описания
        synthesis_prompt = self._build_synthesis_prompt(
            research_result,
            explanation_result,
            narrative
        )
        
        llm_response = await self.openai_client.generate(
            prompt=synthesis_prompt,
            model="gpt-4",
            max_tokens=800
        )
        
        return SynthesisResult(
            topic=research_result.topic,
            final_description=llm_response.content,
            key_insights=self._extract_insights(llm_response),
            practical_applications=self._extract_applications(llm_response)
        )
```

#### Quality Gate 3: Synthesis Quality Check
```python
class SynthesisQualityGate(QualityGate):
    threshold = 0.80
    
    async def evaluate(self, result: SynthesisResult) -> QualityResult:
        metrics = {
            "coherence": await self._assess_coherence(result.final_description),
            "completeness": await self._check_completeness(result),
            "consistency": await self._check_consistency(result),
            "structure": await self._check_narrative_structure(result)
        }
        
        overall_score = sum(metrics.values()) / len(metrics)
        
        return QualityResult(
            score=overall_score,
            passed=overall_score >= self.threshold,
            details=metrics
        )
```

---

### ЭТАП 2: СОЗДАНИЕ ПРЕЗЕНТАЦИИ

#### Шаг 2.1: PresentationAgent
```python
class PresentationStep(BaseStep):
    agent = PresentationAgent()
    timeout = 60
    
    async def execute(self, synthesis_result: SynthesisResult) -> PresentationResult:
        # 1. Анализ содержания для структуры
        content_analysis = self._analyze_content_for_slides(synthesis_result)
        
        # 2. Расчет структуры презентации
        slide_structure = self._calculate_slide_structure(
            content_analysis,
            target_duration=60
        )
        
        # 3. Генерация контента для каждого слайда
        slides = []
        for slide_config in slide_structure:
            slide_content = await self._generate_slide_content(
                synthesis_result,
                slide_config
            )
            slides.append(Slide(
                slide_number=slide_config.number,
                title=slide_content.title,
                content=slide_content.content,
                speaker_notes=slide_content.notes,
                duration_estimate=slide_config.duration,
                visual_type=slide_content.visual_type
            ))
        
        # 4. Валидация общего времени
        total_duration = sum(slide.duration_estimate for slide in slides)
        if abs(total_duration - 60) > 5:
            slides = self._adjust_slide_timing(slides, target_duration=60)
        
        return PresentationResult(
            topic=synthesis_result.topic,
            slides=slides,
            total_duration=sum(slide.duration_estimate for slide in slides),
            slide_timings=[slide.duration_estimate for slide in slides]
        )
    
    def _calculate_slide_structure(self, content_analysis, target_duration: int):
        """Расчет оптимальной структуры слайдов"""
        base_duration = target_duration // 5  # Примерно по 12 секунд на слайд
        
        return [
            {
                "number": 1,
                "type": "introduction",
                "duration": base_duration - 2,
                "content_focus": "definition_and_importance
