"""
LangChain tools for accessing health data.
These tools allow agents to query real health data from the SQLite database.
Now includes timezone-aware functionality.
"""
import json
import re
from typing import Dict, Any
from langchain_core.tools import Tool
from app.core.health_data_service import health_service


def _parse_integer_from_input(input_str: str, default: int = 7) -> int:
    """
    Extract integer from potentially quoted or mixed input using regex.
    Handles cases like: '7', "7", 7, "'7'", "7", etc.
    """
    if not input_str:
        return default
    
    # Use regex to find the first integer in the string
    match = re.search(r'\d+', str(input_str))
    if match:
        return int(match.group())
    
    # Fallback to default if no integer found
    return default


def get_timezone_info_tool(unused_input: str = "") -> str:
    """Get user's timezone information. Ignores any input parameter."""
    try:
        result = health_service.get_user_timezone_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting timezone info: {str(e)}"


def get_steps_tool(days_back: str = "7") -> str:
    """Get daily step counts for the specified number of days back."""
    try:
        days = _parse_integer_from_input(days_back, 7)
        result = health_service.get_daily_steps(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting step data: {str(e)}"


def get_heart_rate_tool(days_back: str = "7") -> str:
    """Get heart rate summary for the specified number of days back."""
    try:
        days = _parse_integer_from_input(days_back, 7)
        result = health_service.get_heart_rate_summary(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting heart rate data: {str(e)}"


def get_workouts_tool(limit: str = "10") -> str:
    """Get recent workout activities."""
    try:
        workout_limit = _parse_integer_from_input(limit, 10)
        result = health_service.get_recent_workouts(workout_limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting workout data: {str(e)}"


def get_weight_tool(days_back: str = "30") -> str:
    """Get weight tracking progress for the specified number of days back."""
    try:
        days = _parse_integer_from_input(days_back, 30)
        result = health_service.get_weight_progress(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting weight data: {str(e)}"


def get_activity_summary_tool(days_back: str = "7") -> str:
    """Get comprehensive activity summary for the specified number of days back."""
    try:
        days = _parse_integer_from_input(days_back, 7)
        result = health_service.get_activity_summary(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting activity data: {str(e)}"


def search_health_data_tool(metric_and_days: str) -> str:
    """Search for specific health data. Format: 'metric_type,days_back' (e.g., 'steps,7' or 'heart_rate,14')."""
    try:
        if not metric_and_days:
            return "Error: Please provide metric type and days in format 'metric_type,days_back'"
        
        parts = metric_and_days.split(',')
        if len(parts) != 2:
            return "Error: Please provide metric type and days in format 'metric_type,days_back' (e.g., 'steps,7')"
        
        metric_type = parts[0].strip()
        days_back = _parse_integer_from_input(parts[1].strip(), 7)
        
        result = health_service.search_health_data(metric_type, days_back)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching health data: {str(e)}"


def get_sleep_data_tool(days_back: str = "7") -> str:
    """Get sleep data and patterns. Input should be just the number of days (e.g., 7 for last week, 30 for last month). Shows total sleep hours, sleep stages (Core/REM/Deep), and sleep quality trends."""
    try:
        days = _parse_integer_from_input(days_back, 7)
        result = health_service.get_sleep_data(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting sleep data: {str(e)}"


# Create LangChain Tool objects with clear descriptions
health_tools = [
    Tool(
        name="get_user_timezone",
        description="Get user's timezone information. No input needed - just use empty string or None.",
        func=get_timezone_info_tool
    ),
    Tool(
        name="get_daily_steps",
        description="Get daily step counts. Input should be just the number of days (e.g., 7)",
        func=get_steps_tool
    ),
    Tool(
        name="get_heart_rate_summary",
        description="Get heart rate summary. Input should be just the number of days (e.g., 7)",
        func=get_heart_rate_tool
    ),
    Tool(
        name="get_recent_workouts",
        description="Get recent workout activities. Input should be just the number of workouts (e.g., 10)",
        func=get_workouts_tool
    ),
    Tool(
        name="get_weight_progress",
        description="Get weight tracking progress. Input should be just the number of days (e.g., 30)",
        func=get_weight_tool
    ),
    Tool(
        name="get_activity_summary",
        description="Get comprehensive activity summary. Input should be just the number of days (e.g., 7)",
        func=get_activity_summary_tool
    ),
    Tool(
        name="search_health_data",
        description="Search for specific health metrics. Input format: 'metric_type,days_back' (e.g., 'steps,7')",
        func=search_health_data_tool
    ),
    Tool(
        name="get_sleep_data",
        description="Get sleep data and patterns. Input should be just the number of days (e.g., 7)",
        func=get_sleep_data_tool
    )
]


def get_fitness_tools():
    """Get tools relevant for fitness agent."""
    return [
        health_tools[0],  # timezone
        health_tools[1],  # steps
        health_tools[2],  # heart_rate
        health_tools[3],  # workouts
        health_tools[5],  # activity_summary
    ]


def get_nutrition_tools():
    """Get tools relevant for nutrition agent."""
    return [
        health_tools[0],  # timezone
        health_tools[4],  # weight
        health_tools[5],  # activity_summary (for calorie burn)
    ]


def get_wellness_tools():
    """Get tools relevant for wellness agent."""
    return [
        health_tools[2],  # heart_rate (stress indicator)
        health_tools[5],  # activity_summary (overall wellness)
        health_tools[7],  # sleep_data (sleep quality and duration)
    ]


def get_general_tools():
    """Get all tools for general health agent."""
    return health_tools 