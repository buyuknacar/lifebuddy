"""
Fitness Agent - AI Personal Trainer
Provides personalized workout plans and fitness coaching based on user profile.
"""
import os
import re
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm_provider import llm_provider
from app.core.logger import get_agent_logger

logger = get_agent_logger()


class FitnessAgent:
    """AI Personal Trainer - Provides personalized workout plans and fitness coaching."""
    
    def __init__(self):
        self.name = "AI Personal Trainer"
        self.description = "Personalized fitness coaching and workout planning"
        self.llm = llm_provider.get_llm()
        self.user_profile = self._load_user_profile()
        self.workout_plan_status = self._check_workout_plan_status()
    
    def _load_user_profile(self) -> str:
        """Load user profile from the markdown file."""
        try:
            profile_path = os.path.join(os.path.dirname(__file__), "../../data/user_profile.md")
            if os.path.exists(profile_path):
                with open(profile_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check if it's still the template (contains [Your Name] etc.)
                    if "[Your Name]" in content or "[Your Age]" in content:
                        return "TEMPLATE_NOT_FILLED"
                    return content
            else:
                return "NO_PROFILE_FILE"
        except Exception as e:
            logger.error(f"Error loading user profile: {e}")
            return "ERROR_LOADING_PROFILE"
    
    def _check_workout_plan_status(self) -> str:
        """Check if workout plan exists and is filled (without loading full content)."""
        try:
            plan_path = os.path.join(os.path.dirname(__file__), "../../data/workout_plan.md")
            if os.path.exists(plan_path):
                with open(plan_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check if it's still the template
                    if "*Add your workout plan here*" in content or len(content.strip()) < 50:
                        return "EMPTY"
                    return "HAS_PLAN"
            else:
                return "NO_FILE"
        except Exception as e:
            logger.error(f"Error checking workout plan: {e}")
            return "ERROR"
    
    def read_workout_plan(self) -> str:
        """Tool to read the full workout plan when needed."""
        try:
            plan_path = os.path.join(os.path.dirname(__file__), "../../data/workout_plan.md")
            if os.path.exists(plan_path):
                with open(plan_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "*Add your workout plan here*" in content:
                        return "Workout plan file exists but is empty. User hasn't added their plan yet."
                    return content
            else:
                return "No workout plan file found."
        except Exception as e:
            logger.error(f"Error reading workout plan: {e}")
            return f"Error reading workout plan: {str(e)}"
    
    def _extract_user_name(self) -> str:
        """Extract user name from profile."""
        if self.user_profile not in ["TEMPLATE_NOT_FILLED", "NO_PROFILE_FILE", "ERROR_LOADING_PROFILE"]:
            # Look for name pattern
            name_match = re.search(r'\*\*Name\*\*:\s*([^\n\r]+)', self.user_profile)
            if name_match:
                name = name_match.group(1).strip()
                if name and name != "[Your Name]":
                    return name
        return ""
    
    def _save_user_profile(self, profile_content: str) -> bool:
        """Save user profile to the markdown file."""
        try:
            profile_path = os.path.join(os.path.dirname(__file__), "../../data/user_profile.md")
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(profile_content)
            logger.info("User profile saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            return False
    
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
    
    def refresh_profile(self) -> bool:
        """Refresh the user profile and workout plan status."""
        try:
            self.user_profile = self._load_user_profile()
            self.workout_plan_status = self._check_workout_plan_status()
            logger.info("User profile and workout plan status refreshed successfully")
            return True
        except Exception as e:
            logger.error(f"Error refreshing profile: {e}")
            return False
    
    def process_query(self, query: str, context: str = "") -> str:
        """Process a user query and return a response following the specific flow."""
        
        # Refresh profile data
        self.refresh_profile()
        
        # Analyze current state
        user_name = self._extract_user_name()
        has_profile = self.user_profile not in ["TEMPLATE_NOT_FILLED", "NO_PROFILE_FILE", "ERROR_LOADING_PROFILE"]
        has_workout_plan = self.workout_plan_status == "HAS_PLAN"
        
        # Create the prompt with state information
        prompt = PromptTemplate(
            input_variables=["query", "user_name", "has_profile", "has_workout_plan", "user_profile", "workout_plan_status"],
            template="""You are an AI Personal Trainer and Fitness Coach. Follow this specific conversation flow:

CURRENT STATE:
- User has profile: {has_profile}
- User name: {user_name}
- User has workout plan: {has_workout_plan}
- Workout plan status: {workout_plan_status}

USER PROFILE:
{user_profile}

TOOLS AVAILABLE:
- read_workout_plan(): Use this tool when user asks about their current workout plan or wants to modify it

 CONVERSATION FLOW TO FOLLOW:
 1. If no user profile exists or is unfilled:
    - Greet warmly as their personal trainer
    - Explain you'd love to help them reach their fitness goals
    - Ask them to share: Name, Age, Gender, Height, Weight, Fitness Level, Goals, Health limitations, Schedule, Equipment, Preferences
    - Make it feel personal and encouraging

 2. If user profile exists:
    - Greet them by name warmly as their personal trainer
    - Reference their specific fitness goal and current level
    - Show you remember their equipment and limitations

  3. Check workout plan:
     - If no workout plan exists (status: EMPTY/NO_FILE), get excited about creating their first personalized plan
     - If workout plan exists (status: HAS_PLAN), acknowledge they have a plan and ask how it's going

 4. For greetings/casual conversation: Focus on motivation and goal-setting
 5. If user asks about their current workout plan: Use read_workout_plan() to get the details
 6. Then address their specific question: {query}

INSTRUCTIONS:
- Be warm, encouraging, and personal
- Use their name when you know it
- Reference their specific profile details (goals, limitations, equipment, etc.)
- Keep responses focused and actionable
- Don't ask too many questions at once

Respond naturally following this flow:"""
        )
        
        # Create the chain
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            # Check if user is asking about their workout plan
            workout_plan_keywords = ["workout plan", "current plan", "my plan", "training plan", "exercise plan", "routine"]
            asking_about_plan = any(keyword in query.lower() for keyword in workout_plan_keywords)
            
            # Get workout plan details if needed
            workout_plan_details = ""
            if asking_about_plan and has_workout_plan:
                workout_plan_details = f"\n\nCURRENT WORKOUT PLAN:\n{self.read_workout_plan()}"
            
            # Create enhanced query context
            enhanced_query = query
            if workout_plan_details:
                enhanced_query = f"{query}{workout_plan_details}"
            
            response = chain.invoke({
                "query": enhanced_query,
                "user_name": user_name or "friend",
                "has_profile": has_profile,
                "has_workout_plan": has_workout_plan,
                "user_profile": self.user_profile if has_profile else "No profile found",
                "workout_plan_status": self.workout_plan_status
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I'm having trouble processing your request right now. Please make sure your profile is set up in data/user_profile.md. Error: {str(e)}"


# Global fitness agent instance
fitness_agent = FitnessAgent() 