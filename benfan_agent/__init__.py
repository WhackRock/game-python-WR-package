"""
BenFan Agent - A GAME agent that manages WhackRock funds based on Benjamin Cowen's market analysis.
"""

from .worker import BenFanWorker
from .signal import derive_weights, get_last_analysis, NUM_LLM_SIGNAL_ASSETS

__all__ = [
    "BenFanWorker",
    "derive_weights", 
    "get_last_analysis",
    "NUM_LLM_SIGNAL_ASSETS"
]

__version__ = "1.0.0" 