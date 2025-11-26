"""
Analysis rules for code review.
"""

from ..tree_sitter_analyzer import AnalysisRule
from .cpp_rules import get_cpp_rules
from .python_rules import get_python_rules

__all__ = [
    'AnalysisRule',
    'get_cpp_rules',
    'get_python_rules'
]
