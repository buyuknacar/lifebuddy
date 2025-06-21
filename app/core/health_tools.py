"""
LangChain tools for accessing health data.
These tools allow agents to query real health data from the SQLite database.
Now includes timezone-aware functionality.
"""
import json
from typing import Dict, Any
from langchain_core.tools import Tool
from app.core.health_data_service import health_service


def get_timezone_info_tool() -> str:
    """Get user's timezone information."""
    try:
        result = health_service.get_user_timezone_info()
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting timezone info: {str(e)}"


def get_steps_tool(days_back: str = "7") -> str:
    """Get daily step counts for the specified number of days back."""
    try:
        days = int(days_back)
        result = health_service.get_daily_steps(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting step data: {str(e)}"


def get_heart_rate_tool(days_back: str = "7") -> str:
    """Get heart rate summary for the specified number of days back."""
    try:
        days = int(days_back)
        result = health_service.get_heart_rate_summary(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting heart rate data: {str(e)}"


def get_workouts_tool(limit: str = "10") -> str:
    """Get recent workout activities."""
    try:
        workout_limit = int(limit)
        result = health_service.get_recent_workouts(workout_limit)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting workout data: {str(e)}"


def get_weight_tool(days_back: str = "30") -> str:
    """Get weight tracking progress for the specified number of days back."""
    try:
        days = int(days_back)
        result = health_service.get_weight_progress(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting weight data: {str(e)}"


def get_activity_summary_tool(days_back: str = "7") -> str:
    """Get comprehensive activity summary for the specified number of days back."""
    try:
        days = int(days_back)
        result = health_service.get_activity_summary(days)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting activity data: {str(e)}"


def search_health_data_tool(metric_and_days: str) -> str:
    """Search for specific health data. Format: 'metric_type,days_back' (e.g., 'steps,7' or 'heart_rate,14')."""
    try:
        parts = metric_and_days.split(',')
        if len(parts) != 2:
            return "Error: Please provide metric type and days in format 'metric_type,days_back'"
        
        metric_type = parts[0].strip()
        days_back = int(parts[1].strip())
        
        result = health_service.search_health_data(metric_type, days_back)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error searching health data: {str(e)}"


# Create LangChain Tool objects
health_tools = [
    Tool(
        name="get_user_timezone",
        description="Get user's timezone information to understand the context of health data timestamps",
        func=get_timezone_info_tool
    ),
    Tool(
        name="get_daily_steps",
        description="Get daily step counts. Input: number of days back (default: 7)",
        func=get_steps_tool
    ),
    Tool(
        name="get_heart_rate_summary",
        description="Get heart rate summary including average, min, max. Input: number of days back (default: 7)",
        func=get_heart_rate_tool
    ),
    Tool(
        name="get_recent_workouts",
        description="Get recent workout activities with details. Input: number of workouts to show (default: 10)",
        func=get_workouts_tool
    ),
    Tool(
        name="get_weight_progress",
        description="Get weight tracking progress and trends. Input: number of days back (default: 30)",
        func=get_weight_tool
    ),
    Tool(
        name="get_activity_summary",
        description="Get comprehensive activity summary including steps, energy, exercise time. Input: number of days back (default: 7)",
        func=get_activity_summary_tool
    ),
    Tool(
        name="search_health_data",
        description="Search for specific health metrics. Input: 'metric_type,days_back' where metric_type is one of: steps, heart_rate, workouts, weight, activity",
        func=search_health_data_tool
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
        health_tools[0],  # timezone
        health_tools[2],  # heart_rate (stress indicator)
        health_tools[5],  # activity_summary (overall wellness)
    ]


def get_general_tools():
    """Get all tools for general health agent."""
    return health_tools 