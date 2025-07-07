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
- fitness: specific questions about exercise, workouts, activity levels, steps, heart rate, performance data, workout plans, exercise form
- general: greetings, casual conversation, non-health questions, general health summaries, or any questions about diet, nutrition, sleep, stress, mood (currently not specialized)

Query: {query}

Answer with just the category name (fitness/general):"""
        )
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def classify(self, query: str) -> HealthIntent:
        """Classify a query into a health intent."""
        result = self.chain.invoke({"query": query}).strip().lower()
        
        # Map result to enum
        intent_map = {
            "fitness": HealthIntent.FITNESS,
            "general": HealthIntent.GENERAL
        }
        
        return intent_map.get(result, HealthIntent.GENERAL)


# Global classifier instance
intent_classifier = IntentClassifier() 