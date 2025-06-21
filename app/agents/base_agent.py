"""
Base agent class for health-focused AI agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from app.core.llm_provider import llm_provider
from app.core.logger import get_agent_logger

# Initialize logger
logger = get_agent_logger()


class BaseHealthAgent(ABC):
    """Base class for all health agents."""
    
    def __init__(self, name: str, description: str, tools: List | None = None):
        self.name = name
        self.description = description
        self.llm = llm_provider.get_llm()
        self.tools = tools or []
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    def create_agent_with_tools(self):
        """Create a ReAct agent that can use tools."""
        if not self.tools:
            return None
        
        # Use the standard ReAct prompt from LangChain hub
        try:
            prompt = hub.pull("hwchase17/react")
        except:
            # Fallback to a simpler prompt if hub is not available
            from langchain_core.prompts import PromptTemplate
            prompt_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
            prompt = PromptTemplate.from_template(prompt_template)
        
        # Create the agent
        agent = create_react_agent(self.llm, self.tools, prompt)
        
        # Create the executor
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=False,  # Set to False to reduce noise
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def create_simple_chain(self):
        """Create the simple LangChain processing chain without tools."""
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
        # Use tools if available, otherwise use simple chain
        if self.tools:
            agent_executor = self.create_agent_with_tools()
            if agent_executor:
                try:
                    result = agent_executor.invoke({"input": query})
                    return result.get("output", "Sorry, I couldn't process that request.")
                except Exception as e:
                    # Fallback to simple chain if agent fails
                    logger.warning(f"Agent execution failed: {e}, falling back to simple response")
        
        # Simple chain fallback
        chain = self.create_simple_chain()
        return chain.invoke({
            "query": query,
            "context": context
        }) 