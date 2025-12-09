"""Constants for F1 Analytics Application.

This module contains all constants, configuration values, and static data
used throughout the application.
"""
from typing import List, Dict

# ============================================================================
# METRICS CONFIGURATION
# ============================================================================

METRIC_OPTIONS: List[str] = [
    "Average Lap Time",
    "Best Lap Time",
    "Total Laps",
    "Fastest Laps Count",
    "Average Sector 1",
    "Average Sector 2",
    "Average Sector 3",
    "Average Position",
    "Best Position",
    "Worst Position",
    "Pit Stop Laps",
    "Total Sessions"
]

METRIC_HELP_TEXT: str = """
📊 LAP PERFORMANCE
• Average Lap Time: Mean lap duration in seconds
• Best Lap Time: Fastest lap recorded
• Total Laps: Count of laps completed
• Fastest Laps Count: Number of times driver achieved fastest lap

⏱️ SECTOR TIMES
• Average Sector 1/2/3: Mean sector times (track is divided into 3 sectors)

🏁 RACE POSITION
• Average/Best/Worst Position: Race finishing positions

🔧 PIT STRATEGY
• Pit Stop Laps: Laps where driver exited pit lane (first lap after pit stop)

📅 GENERAL
• Total Sessions: Number of race sessions
"""

DEFAULT_METRICS: List[str] = ["Average Lap Time", "Total Laps"]

# ============================================================================
# DIMENSIONS CONFIGURATION
# ============================================================================

DIMENSION_OPTIONS: List[str] = [
    "Driver",
    "Team",
    "Season",
    "Circuit",
    "Laps"
]

DIMENSION_HELP_TEXT: str = """
👤 CORE DIMENSIONS
• Driver: Group by individual driver (e.g., Max Verstappen, Lewis Hamilton)
• Team: Group by constructor/team (e.g., Red Bull Racing, Mercedes)

📍 TIME & LOCATION
• Season: Group by year (e.g., 2023, 2024, 2025)
• Circuit: Group by race track (e.g., Monaco, Silverstone, Monza)

🔍 DETAILED ANALYSIS
• Laps: Show lap-by-lap details including lap number, position during lap, and pit stops

💡 TIP: Combine dimensions for detailed analysis
Example: Driver + Circuit shows performance per driver at each track
"""

DEFAULT_DIMENSIONS: List[str] = ["Driver"]

# ============================================================================
# VISUALIZATION CONFIGURATION
# ============================================================================

VISUALIZATION_OPTIONS: List[str] = [
    "Table",
    "Bar Chart",
    "Line Chart",
    "Scatter Plot"
]

# ============================================================================
# AI ASSISTANT CONFIGURATION
# ============================================================================

AI_ASSISTANT_DESCRIPTION: str = """
Ask questions about F1 data and get ML-powered predictions and analytics:
- **Predictions**: "Who will win the next race?" (ML model trained on historical performance)
- **Analysis**: "Compare Verstappen's performance across 2023-2025" (Multi-season trends)
- **Historical**: "Who won the last race?" (Real-time data queries)
"""

# Keywords that trigger chart visualization
CHART_KEYWORDS: List[str] = ["chart", "plot", "graph", "visualize", "show"]

# Keywords that trigger table display
TABLE_KEYWORDS: List[str] = ["table", "show data", "raw data"]

# Keywords that indicate historical data questions
HISTORICAL_KEYWORDS: List[str] = [
    "who", "what", "which", "how many",
    "fastest", "slowest", "average", "last", "latest"
]

# Keywords that indicate race prediction questions
PREDICTION_KEYWORDS: List[str] = ["next race", "will win"]

# Driver name mapping for performance analysis
DRIVER_NAME_MAPPING: Dict[str, str] = {
    "verstappen": "Max Verstappen",
    "hamilton": "Lewis Hamilton",
    "leclerc": "Charles Leclerc"
}

# Default circuit for predictions
DEFAULT_PREDICTION_CIRCUIT: str = "monza"

# Current year for performance analysis
CURRENT_YEAR: int = 2025

# Number of seasons to compare in performance analysis
PERFORMANCE_SEASONS_LOOKBACK: int = 3

# ============================================================================
# UI CONFIGURATION
# ============================================================================

APP_TITLE: str = "🏁 ApexML – F1 Race Analytics"
APP_DESCRIPTION: str = "Real-time F1 data analytics powered by Snowflake, dbt, and OpenF1 API"

TAB_CUSTOM_ANALYSIS: str = "🔧 Custom Analysis"
TAB_AI_ASSISTANT: str = "💬 AI Assistant"

# ============================================================================
# WARNING MESSAGES
# ============================================================================

WARNING_NO_METRICS_DIMENSIONS: str = "Please select at least one metric and one dimension"
WARNING_NO_SEASONS: str = "⚠️ Please select at least one season to analyze"
WARNING_NO_DATA: str = "No data to display"

# ============================================================================
# ERROR MESSAGES
# ============================================================================

ERROR_INSUFFICIENT_DATA: str = "I don't have enough data yet to make predictions."
ERROR_NO_DATA_FOR_DRIVER: str = "No data available for {driver} in those seasons."

# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

PREDICTION_FALLBACK_MESSAGE: str = "I can predict race winners and performance trends. Try asking 'Who will win the next race?'"

# ============================================================================
# SPINNER MESSAGES
# ============================================================================

SPINNER_THINKING: str = "Thinking..."
SPINNER_TRAINING_MODEL: str = "Training ML model and generating predictions..."
SPINNER_ANALYZING_PERFORMANCE: str = "Analyzing {driver}'s performance across seasons..."

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

SIDEBAR_ML_MODELS: str = "**ML Models:** Random Forest (Win Prediction), Gradient Boosting (Performance)"
SIDEBAR_AI_INFO: str = "**AI:** OpenRouter (GPT-4o-mini) + scikit-learn"
SIDEBAR_DATA_UPDATE: str = "**Updated:** Real-time via dbt transformations"
SIDEBAR_GITHUB_BADGE: str = "[![GitHub](https://img.shields.io/badge/GitHub-apex--ml-blue?logo=github)](https://github.com/youngpada1/apex-ml)"

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHE_TTL_SECONDS: int = 300  # 5 minutes
