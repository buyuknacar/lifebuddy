"""
Fitness Agent - AI Personal Trainer
Provides personalized workout plans and fitness coaching based on user profile.
"""
import os
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseHealthAgent
from app.core.health_tools import get_fitness_tools
from app.core.logger import get_agent_logger

logger = get_agent_logger()


class FitnessAgent(BaseHealthAgent):
    """AI Personal Trainer - Provides personalized workout plans and fitness coaching."""
    
    def __init__(self):
        super().__init__(
            name="AI Personal Trainer",
            description="Personalized fitness coaching and workout planning",
            tools=get_fitness_tools()
        )
        self.user_profile = self._load_user_profile()
    
    def _load_user_profile(self) -> str:
        """Load user profile from the markdown file."""
        try:
            profile_path = os.path.join(os.path.dirname(__file__), "../../data/user_profile.md")
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning("User profile not found. Using default profile.")
                return "No user profile available. Please fill out your profile for personalized recommendations."
        except Exception as e:
            logger.error(f"Error loading user profile: {e}")
            return "Error loading user profile. Using general recommendations."
    
    def get_system_prompt(self) -> str:
        """Get the system prompt with user profile context."""
        base_prompt = """You are an AI Personal Trainer and Fitness Coach. Your role is to provide personalized workout plans, exercise guidance, and fitness coaching based on the user's profile and health data.

## Your Expertise:
- Exercise science and biomechanics
- Workout programming and periodization
- Form correction and injury prevention
- Motivation and goal setting
- Progress tracking and adjustments

## User Profile:
{user_profile}

## Guidelines:
1. **Safety First**: Always consider the user's health conditions, limitations, and experience level
2. **Personalization**: Tailor all recommendations to the user's goals, equipment, and schedule
3. **Progressive Overload**: Design workouts that gradually increase in difficulty
4. **Recovery**: Include proper rest and recovery recommendations
5. **Form Focus**: Emphasize proper form over heavy weights
6. **Motivation**: Be encouraging and supportive while being realistic

## Capabilities:
- Create custom workout plans (daily, weekly, monthly)
- Provide exercise alternatives for equipment/injury limitations
- Explain proper form and technique
- Suggest progression paths
- Analyze workout performance from health data
- Recommend rest and recovery protocols
- Adjust plans based on progress and feedback

## Health Data Integration:
You have access to the user's actual health data including:
- Heart rate trends and training zones
- Activity levels and step counts
- Workout history and performance
- Sleep quality and recovery metrics
- Weight and body composition trends

Use this data to provide evidence-based, personalized recommendations that align with their actual performance and recovery patterns.

## Communication Style:
- Be encouraging and motivational
- Explain the "why" behind recommendations
- Provide alternatives for different situations
- Check in on progress and adjust accordingly
- Celebrate achievements and milestones

Remember: You're not just providing workouts - you're a comprehensive fitness coach helping users achieve their health and fitness goals safely and effectively."""
        
        return base_prompt.format(user_profile=self.user_profile)
    
    def create_workout_plan(self, duration: str = "weekly", focus: str = "general") -> Dict[str, Any]:
        """Create a personalized workout plan based on user profile."""
        query = f"Create a {duration} {focus} workout plan based on my profile and current fitness level"
        response = self.process_query(query)
        
        return {
            "plan_type": f"{duration} {focus} workout plan",
            "recommendations": response,
            "profile_based": True
        }
    
    def analyze_workout_performance(self, workout_data: Dict[str, Any]) -> str:
        """Analyze workout performance and provide feedback."""
        query = f"Analyze this workout data and provide feedback: {workout_data}"
        return self.process_query(query)
    
    def suggest_exercise_alternatives(self, exercise: str, limitation: str) -> str:
        """Suggest alternative exercises for limitations."""
        query = f"Suggest alternatives to {exercise} for someone with {limitation}"
        return self.process_query(query)
    
    def check_form_guidance(self, exercise: str) -> str:
        """Provide form guidance for specific exercises."""
        query = f"Provide detailed form guidance for {exercise}"
        return self.process_query(query)
    
    def adjust_plan_based_on_progress(self, progress_data: Dict[str, Any]) -> str:
        """Adjust workout plan based on progress data."""
        query = f"Adjust my workout plan based on this progress: {progress_data}"
        return self.process_query(query)
    
    def refresh_profile(self) -> bool:
        """Refresh the user profile from the markdown file."""
        try:
            self.user_profile = self._load_user_profile()
            logger.info("User profile refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Error refreshing user profile: {e}")
            return False


# Global fitness agent instance
fitness_agent = FitnessAgent()


def get_fitness_agent() -> FitnessAgent:
    """Get the global fitness agent instance."""
    return fitness_agent


# Convenience functions for common operations
def create_workout_plan(duration: str = "weekly", focus: str = "general") -> Dict[str, Any]:
    """Create a personalized workout plan."""
    return fitness_agent.create_workout_plan(duration, focus)


def get_exercise_alternatives(exercise: str, limitation: str) -> str:
    """Get alternative exercises for limitations."""
    return fitness_agent.suggest_exercise_alternatives(exercise, limitation)


def get_form_guidance(exercise: str) -> str:
    """Get form guidance for an exercise."""
    return fitness_agent.check_form_guidance(exercise)


def analyze_performance(workout_data: Dict[str, Any]) -> str:
    """Analyze workout performance."""
    return fitness_agent.analyze_workout_performance(workout_data) 