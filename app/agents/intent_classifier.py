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
    HEALTH = "health"


class IntentClassifier:
    """Classifies user queries into health intents."""
    
    def __init__(self):
        self.llm = llm_provider.get_llm()
        self.prompt = PromptTemplate(
            input_variables=["query"],
            template="""Classify this query into ONE category:

Categories:
- fitness: workout plans, exercise guidance, gym routines, form tips, fitness goals, personal training, greetings, general conversation
- health: Apple Health data analysis, steps, heart rate, sleep data, weight tracking, health metrics, "show my data", "analyze my health"

Query: {query}

Answer with just the category name (fitness/health):"""
        )
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def classify(self, query: str) -> HealthIntent:
        """Classify a query into a health intent."""
        result = self.chain.invoke({"query": query}).strip().lower()
        
        # Map result to enum
        intent_map = {
            "fitness": HealthIntent.FITNESS,
            "health": HealthIntent.HEALTH
        }
        
        return intent_map.get(result, HealthIntent.FITNESS)


# Global classifier instance
intent_classifier = IntentClassifier() 