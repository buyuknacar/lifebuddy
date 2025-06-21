"""
Intent classifier for routing health queries to appropriate agents.
"""
from enum import Enum
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm_provider import llm_provider


class HealthIntent(Enum):
    """Health-related intents for routing queries."""
    FITNESS = "fitness"
    NUTRITION = "nutrition" 
    WELLNESS = "wellness"
    GENERAL = "general"


class IntentClassifier:
    """Classifies user queries into health intents."""
    
    def __init__(self):
        self.llm = llm_provider.get_llm()
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""Classify this query into ONE category:

Categories:
- fitness: specific questions about exercise, workouts, activity levels, steps, heart rate, performance data
- nutrition: specific questions about diet, food, calories, weight tracking, eating habits  
- wellness: specific questions about sleep, stress, mood, mental health data
- general: greetings, casual conversation, non-health questions, or requests for general health summaries

Query: {query}

Answer with just the category name (fitness/nutrition/wellness/general):"""
        )
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def classify(self, query: str) -> HealthIntent:
        """Classify a query into a health intent."""
        result = self.chain.invoke({"query": query}).strip().lower()
        
        # Map result to enum
        intent_map = {
            "fitness": HealthIntent.FITNESS,
            "nutrition": HealthIntent.NUTRITION,
            "wellness": HealthIntent.WELLNESS,
            "general": HealthIntent.GENERAL
        }
        
        return intent_map.get(result, HealthIntent.GENERAL)


# Global classifier instance
intent_classifier = IntentClassifier() 