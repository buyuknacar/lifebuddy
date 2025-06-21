"""
Agent router for directing health queries to specialized agents.
"""
from typing import Dict, Any
from app.agents.intent_classifier import IntentClassifier, HealthIntent
from app.agents.base_agent import BaseHealthAgent
from app.core.health_tools import (
    get_fitness_tools, get_nutrition_tools, 
    get_wellness_tools, get_general_tools
)


class SimpleHealthAgent(BaseHealthAgent):
    """Simple health agent for demonstration."""
    
    def __init__(self, intent: HealthIntent):
        self.intent = intent
        name = f"{intent.value.title()} Agent"
        description = f"Specialized agent for {intent.value} related queries"
        
        # Get appropriate tools for this agent type
        tools_map = {
            HealthIntent.FITNESS: get_fitness_tools(),
            HealthIntent.NUTRITION: get_nutrition_tools(),
            HealthIntent.WELLNESS: get_wellness_tools(),
            HealthIntent.GENERAL: get_general_tools()
        }
        tools = tools_map.get(intent, [])
        
        super().__init__(name, description, tools)
    
    def get_system_prompt(self) -> str:
        """Get the system prompt based on intent."""
        prompts = {
            HealthIntent.FITNESS: """You are a fitness coach AI with access to real health data. Help users with:
- Exercise recommendations and workout analysis
- Activity tracking and performance insights  
- Heart rate and fitness metrics interpretation
- Movement and exercise form guidance

You have access to tools to get the user's actual health data including steps, heart rate, workouts, and activity summaries. Use these tools to provide personalized, data-driven advice based on their real metrics.

Keep responses practical, encouraging, and data-driven.""",

            HealthIntent.NUTRITION: """You are a nutrition advisor AI with access to real health data. Help users with:
- Diet analysis and nutritional insights
- Calorie and macronutrient tracking
- Weight management guidance
- Food choice recommendations

You have access to tools to get the user's weight progress and activity data to calculate their caloric needs and provide personalized nutrition advice.

Keep responses evidence-based, balanced, and practical.""",

            HealthIntent.WELLNESS: """You are a wellness mentor AI. Help users with:
- Sleep quality analysis and improvement
- Stress management and mental health
- Mood tracking and emotional wellness
- Mindfulness and self-care practices

Keep responses supportive, thoughtful, and holistic.""",

            HealthIntent.GENERAL: """You are a general health data analyst AI with access to comprehensive health data. Help users with:
- Health data summaries and trends
- Cross-metric correlations and insights
- General questions about their health patterns
- Data interpretation and explanations

You have access to all health data tools including steps, heart rate, workouts, weight, and activity summaries. Use these tools to provide comprehensive analysis and insights.

Keep responses clear, analytical, and informative."""
        }
        return prompts.get(self.intent, prompts[HealthIntent.GENERAL])


class HealthAgentRouter:
    """Routes health queries to appropriate specialized agents."""
    
    def __init__(self):
        self.classifier = IntentClassifier()
        # Create agents for each intent
        self.agents = {
            intent: SimpleHealthAgent(intent) 
            for intent in HealthIntent
        }
    
    def route_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """Route a query to the appropriate agent and get response."""
        # Classify the intent
        intent = self.classifier.classify(query)
        
        # Get the appropriate agent
        agent = self.agents[intent]
        
        # Process the query
        response = agent.process_query(query, context)
        
        return {
            "intent": intent.value,
            "agent": agent.name,
            "response": response,
            "query": query
        }


# Global router instance
health_router = HealthAgentRouter() 