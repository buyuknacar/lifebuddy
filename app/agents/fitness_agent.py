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
                    # Check if key fields have values (not just empty template)
                    # Look for lines like "- **Name**: SomeValue" or "**Name**: SomeValue"
                    import re
                    name_match = re.search(r'\*\*Name\*\*:\s*(.+)', content)
                    age_match = re.search(r'\*\*Age\*\*:\s*(.+)', content)
                    
                    if name_match and name_match.group(1).strip() and age_match and age_match.group(1).strip():
                        return content  # Profile is filled out
                    else:
                        return "TEMPLATE_NOT_FILLED"  # Profile is empty/template
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
        
        # Debug logging
        logger.info(f"Profile status: {self.user_profile[:100] if len(self.user_profile) > 100 else self.user_profile}")
        logger.info(f"User name extracted: {user_name}")
        logger.info(f"Has profile: {has_profile}")
        logger.info(f"Workout plan status: {self.workout_plan_status}")
        
        # Create the prompt with state information
        if has_profile:
            prompt = PromptTemplate(
                input_variables=["query", "user_name", "user_profile", "workout_plan_status"],
                template="""You are an AI Personal Trainer and Fitness Coach for {user_name}.

USER PROFILE:
{user_profile}

WORKOUT PLAN STATUS: {workout_plan_status}

INSTRUCTIONS:
1. Greet {user_name} by name warmly
2. You have their complete profile - reference their specific goals, fitness level, and preferences
3. Workout plan status: {workout_plan_status}
   - If HAS_PLAN: acknowledge they have a workout plan naturally
   - If EMPTY/NO_FILE: offer to create their first workout plan
4. Address their specific question: {query}
5. Be encouraging and supportive
6. NEVER mention status codes like "HAS_PLAN" - use natural language

Response:"""
            )
        else:
            prompt = PromptTemplate(
                input_variables=["query"],
                template="""You are an AI Personal Trainer and Fitness Coach.

The user does not have a complete profile yet.

INSTRUCTIONS:
1. Greet them warmly as their personal trainer
2. Explain that you need their profile information to provide personalized fitness guidance
3. Ask them to fill out their profile with: Name, Age, Gender, Fitness Level, Goals, Limitations, Schedule, Equipment
4. Be encouraging and explain how this will help you create better workout plans for them

User Query: {query}

Response:"""
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
            
            if has_profile:
                response = chain.invoke({
                    "query": enhanced_query,
                    "user_name": user_name or "friend",
                    "user_profile": self.user_profile,
                    "workout_plan_status": self.workout_plan_status
                })
            else:
                response = chain.invoke({
                    "query": enhanced_query
                })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I'm having trouble processing your request right now. Please make sure your profile is set up in data/user_profile.md. Error: {str(e)}"


# Global fitness agent instance
fitness_agent = FitnessAgent() 