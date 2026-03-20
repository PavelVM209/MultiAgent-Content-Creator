"""
Модели данных для мультиагентной системы
"""

from .workflow import *
from .agents import *
from .quality import *

__all__ = [
    # Workflow models
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowState",
    
    # Agent models
    "AgentResult",
    "AgentError",
    "ValidationResult",
    "AgentConfig",
    "TimeoutConfig",
    
    # Quality models
    "QualityResult",
    "QualityMetrics",
    "QualityThreshold"
]
