"""Machine Learning module for F1 race predictions and analysis."""

# AI Assistant (LLM-based)
from .ai_assistant import (
    get_ai_response,
    generate_sql_from_question,
    answer_question_from_data,
    get_dynamic_schema_context
)

# ML Predictions (scikit-learn)
from .ml_predictions import (
    RaceWinnerPredictor,
    PerformanceAnalyzer,
    detect_question_type
)

__all__ = [
    # AI Assistant functions
    'get_ai_response',
    'generate_sql_from_question',
    'answer_question_from_data',
    'get_dynamic_schema_context',
    # ML Prediction classes
    'RaceWinnerPredictor',
    'PerformanceAnalyzer',
    'detect_question_type',
]
