"""
Fitness Agent - AI Personal Trainer
Provides personalized workout plans and fitness coaching based on user profile.
"""
import os
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
        self.workout_plan = self._load_workout_plan()
    
    def _load_user_profile(self) -> str:
        """Load user profile from the markdown file."""
        try:
            profile_path = os.path.join(os.path.dirname(__file__), "../../data/user_profile.md")
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "No user profile available. Please fill out your profile for personalized recommendations."
        except Exception as e:
            logger.error(f"Error loading user profile: {e}")
            return "Error loading user profile. Using general recommendations."
    
    def _load_workout_plan(self) -> str:
        """Load current workout plan from the markdown file."""
        try:
            plan_path = os.path.join(os.path.dirname(__file__), "../../data/workout_plan.md")
            if os.path.exists(plan_path):
                with open(plan_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "No workout plan found."
        except Exception as e:
            logger.error(f"Error loading workout plan: {e}")
            return "Error loading workout plan."
    
    def _save_workout_plan(self, plan: str) -> bool:
        """Save workout plan to the markdown file."""
        try:
            plan_path = os.path.join(os.path.dirname(__file__), "../../data/workout_plan.md")
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(plan)
            logger.info("Workout plan saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving workout plan: {e}")
            return False
    
    def get_system_prompt(self) -> str:
        """Get the system prompt with user profile and workout plan context."""
        return f"""You are an AI Personal Trainer and Fitness Coach. Your role is to provide personalized workout plans, exercise guidance, and fitness coaching based on the user's profile and health data.

## Your Expertise:
- Exercise science and biomechanics
- Workout programming and periodization
- Form correction and injury prevention
- Motivation and goal setting
- Progress tracking and adjustments

## User Profile:
{self.user_profile}

## Current Workout Plan:
{self.workout_plan}

## Guidelines:
1. **Safety First**: Always consider the user's health conditions, limitations, and experience level
2. **Personalization**: Tailor all recommendations to the user's goals, equipment, and schedule
3. **Progressive Overload**: Design workouts that gradually increase in difficulty
4. **Recovery**: Include proper rest and recovery recommendations
5. **Form Focus**: Emphasize proper form over heavy weights
6. **Motivation**: Be encouraging and supportive while being realistic

## Workout Plan Management:
- If the user has no workout plan, suggest creating one and offer to add it to their workout plan file
- If they have a plan, help them modify, progress, or troubleshoot it
- Always work with their existing plan rather than completely replacing it unless requested

## Communication Style:
- Be encouraging and motivational
- Explain the "why" behind recommendations
- Provide alternatives for different situations
- Check in on progress and adjust accordingly

Remember: You're helping users achieve their health and fitness goals safely and effectively."""


# Global fitness agent instance
fitness_agent = FitnessAgent() 