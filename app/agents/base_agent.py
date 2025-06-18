"""
Base agent class for health-focused AI agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.llm_provider import llm_provider


class BaseHealthAgent(ABC):
    """Base class for all health agents."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.llm = llm_provider.get_llm()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def create_chain(self):
        """Create the LangChain processing chain."""
        prompt = PromptTemplate(
            input_variables=["query", "context"],
            template=f"""{self.get_system_prompt()}

Context: {{context}}

User Query: {{query}}

Response:"""
        )
        return prompt | self.llm | StrOutputParser()
    
    def process_query(self, query: str, context: str = "") -> str:
        """Process a user query and return a response."""
        chain = self.create_chain()
        return chain.invoke({
            "query": query,
            "context": context
        }) 