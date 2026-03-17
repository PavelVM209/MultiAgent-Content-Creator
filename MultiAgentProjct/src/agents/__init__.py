"""
Агенты мультиагентной системы
"""

from .base import BaseAgent
from .research_agent import ResearchAgent
from .explanation_agent import ExplanationAgent
from .synthesis_agent import SynthesisAgent
from .presentation_agent import PresentationAgent
from .image_generator_agent import ImageGeneratorAgent
from .audio_agent import AudioAgent
from .video_agent import VideoAgent

__all__ = [
    "BaseAgent",
    "ResearchAgent",
    "ExplanationAgent", 
    "SynthesisAgent",
    "PresentationAgent",
    "ImageGeneratorAgent",
    "AudioAgent",
    "VideoAgent",
]
