"""
LangGraph-based Health Agent System for LifeBuddy.
Migrates existing router and agent functionality to a graph-based agentic approach.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, TypedDict, Annotated, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

from app.core.llm_provider import LLMProvider
from app.core.health_tools import get_fitness_tools, get_nutrition_tools, get_wellness_tools, get_general_tools
from app.core.health_data_service import HealthDataService
from app.agents.intent_classifier import IntentClassifier, HealthIntent


class HealthSessionState(TypedDict):
    """State schema for health conversation sessions."""
    # Current conversation
    messages: Annotated[List[BaseMessage], add_messages]
    current_intent: str
    
    # User context (loaded from persistent storage)
    user_timezone: Dict[str, str]
    session_id: str
    turn_count: int
    
    # Analysis context
    current_analysis: Dict[str, Any]
    tools_used: List[str]
    health_data_cache: Dict[str, Any]
    
    # Response generation
    final_response: str


class HealthAgentGraph:
    """Main LangGraph-based health agent orchestrator."""
    
    def __init__(self):
        self.llm_provider = LLMProvider()
        self.llm = self.llm_provider.get_llm()
        self.health_service = HealthDataService()
        self.intent_classifier = IntentClassifier()
        
        # Initialize tools for different health domains (from existing system)
        self.fitness_tools = get_fitness_tools()
        self.nutrition_tools = get_nutrition_tools()
        self.wellness_tools = get_wellness_tools()
        self.general_tools = get_general_tools()
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Initialize graph without checkpointer for now (can be added later)
        # TODO: Fix checkpointer initialization for session persistence
        self.compiled_graph = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """Build the main health agent graph."""
        graph = StateGraph(HealthSessionState)
        
        # Add nodes
        graph.add_node("load_context", self._load_session_context)
        graph.add_node("classify_intent", self._classify_intent_and_enrich)
        graph.add_node("fitness_analysis", self._fitness_analysis)
        graph.add_node("nutrition_analysis", self._nutrition_analysis)
        graph.add_node("wellness_analysis", self._wellness_analysis)
        graph.add_node("general_analysis", self._general_analysis)
        graph.add_node("generate_response", self._generate_response)
        
        # Define the flow
        graph.set_entry_point("load_context")
        
        # Load context -> Intent classification
        graph.add_edge("load_context", "classify_intent")
        
        # Intent classification -> Specialized analysis (replaces old router logic)
        graph.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "fitness": "fitness_analysis",
                "nutrition": "nutrition_analysis",
                "wellness": "wellness_analysis",
                "general": "general_analysis"
            }
        )
        
        # All analysis nodes -> Response generation
        graph.add_edge("fitness_analysis", "generate_response")
        graph.add_edge("nutrition_analysis", "generate_response")
        graph.add_edge("wellness_analysis", "generate_response")
        graph.add_edge("general_analysis", "generate_response")
        
        # Response generation -> End
        graph.add_edge("generate_response", END)
        
        return graph
    
    def _load_session_context(self, state: HealthSessionState) -> HealthSessionState:
        """Load user context and session information."""
        # Generate session ID if not present
        if not state.get("session_id"):
            state["session_id"] = str(uuid.uuid4())
        
        # Load user timezone from health service (timezone-aware system)
        try:
            timezone_info = self.health_service.get_user_timezone_info()
            state["user_timezone"] = {
                "name": timezone_info["timezone_name"],
                "offset": timezone_info["timezone_offset"]
            }
        except Exception as e:
            print(f"⚠️ Error loading timezone: {e}")
            state["user_timezone"] = {"name": "UTC", "offset": "+0000"}
        
        # Initialize session metadata
        state["turn_count"] = state.get("turn_count", 0) + 1
        state["health_data_cache"] = state.get("health_data_cache", {})
        state["tools_used"] = []
        
        return state
    
    def _classify_intent_and_enrich(self, state: HealthSessionState) -> HealthSessionState:
        """Classify user intent using existing intent classifier."""
        # Get the latest user message
        latest_message = state["messages"][-1] if state["messages"] else None
        if not latest_message or not isinstance(latest_message, HumanMessage):
            state["current_intent"] = "general"
            return state
        
        # Use existing intent classifier
        try:
            intent = self.intent_classifier.classify(str(latest_message.content))
            state["current_intent"] = intent.value
        except Exception as e:
            print(f"⚠️ Intent classification error: {e}")
            state["current_intent"] = "general"
        
        return state
    
    def _route_by_intent(self, state: HealthSessionState) -> Literal["fitness", "nutrition", "wellness", "general"]:
        """Route to appropriate analysis based on intent (replaces old router)."""
        intent = state["current_intent"]
        if intent in ["fitness", "nutrition", "wellness", "general"]:
            return intent  # type: ignore
        return "general"
    
    def _fitness_analysis(self, state: HealthSessionState) -> HealthSessionState:
        """Execute fitness-focused analysis using existing tools and prompts."""
        return self._execute_specialized_analysis(
            state, 
            "fitness", 
            self.fitness_tools,
            """You are a fitness coach AI with access to real health data. Help users with:
- Exercise recommendations and workout analysis
- Activity tracking and performance insights  
- Heart rate and fitness metrics interpretation
- Movement and exercise form guidance

User is in timezone: {timezone_name} ({timezone_offset})

You have access to tools to get the user's actual health data including steps, heart rate, workouts, and activity summaries. Use these tools to provide personalized, data-driven advice based on their real metrics.

Keep responses practical, encouraging, and data-driven."""
        )
    
    def _nutrition_analysis(self, state: HealthSessionState) -> HealthSessionState:
        """Execute nutrition-focused analysis using existing tools and prompts."""
        return self._execute_specialized_analysis(
            state,
            "nutrition",
            self.nutrition_tools,
            """You are a nutrition advisor AI with access to real health data. Help users with:
- Diet analysis and nutritional insights
- Calorie and macronutrient tracking
- Weight management guidance
- Food choice recommendations

User is in timezone: {timezone_name} ({timezone_offset})

You have access to tools to get the user's weight progress and activity data to calculate their caloric needs and provide personalized nutrition advice.

Keep responses evidence-based, balanced, and practical."""
        )
    
    def _wellness_analysis(self, state: HealthSessionState) -> HealthSessionState:
        """Execute wellness-focused analysis using existing tools and prompts."""
        return self._execute_specialized_analysis(
            state,
            "wellness",
            self.wellness_tools,
            """You are a wellness mentor AI. Help users with:
- Sleep quality analysis and improvement
- Stress management and mental health
- Mood tracking and emotional wellness
- Mindfulness and self-care practices

User is in timezone: {timezone_name} ({timezone_offset})

Keep responses supportive, thoughtful, and holistic."""
        )
    
    def _general_analysis(self, state: HealthSessionState) -> HealthSessionState:
        """Execute general health data analysis using existing tools and prompts."""
        return self._execute_specialized_analysis(
            state,
            "general",
            self.general_tools,
            """You are a general health data analyst AI with access to comprehensive health data. Help users with:
- Health data summaries and trends
- Cross-metric correlations and insights
- General questions about their health patterns
- Data interpretation and explanations

User is in timezone: {timezone_name} ({timezone_offset})

You have access to all health data tools including steps, heart rate, workouts, weight, and activity summaries. Use these tools to provide comprehensive analysis and insights.

Keep responses clear, analytical, and informative."""
        )
    
    def _execute_specialized_analysis(self, state: HealthSessionState, domain: str, tools: List, system_prompt_template: str) -> HealthSessionState:
        """Execute specialized analysis using ReAct agent (migrated from base_agent.py)."""
        from langchain.agents import create_react_agent, AgentExecutor
        from langchain_core.prompts import PromptTemplate
        
        # Format system prompt with timezone info
        system_prompt = system_prompt_template.format(
            timezone_name=state['user_timezone']['name'],
            timezone_offset=state['user_timezone']['offset']
        )
        
        # Create ReAct agent (same pattern as base_agent.py)
        react_prompt = PromptTemplate.from_template("""
{system_prompt}

TOOLS:
------
You have access to the following tools:

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
Thought: {agent_scratchpad}
""")
        
        # Set up agent with domain-specific tools
        agent = create_react_agent(self.llm, tools, react_prompt.partial(system_prompt=system_prompt))
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, 
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        # Execute analysis
        try:
            latest_message = state["messages"][-1]
            result = agent_executor.invoke({
                "input": str(latest_message.content),
                "system_prompt": system_prompt
            })
            
            state["current_analysis"] = {
                "domain": domain,
                "result": result["output"],
                "tools_used": [tool.name for tool in tools]
            }
            state["tools_used"] = [tool.name for tool in tools]
            
        except Exception as e:
            print(f"⚠️ {domain.title()} analysis error: {e}")
            state["current_analysis"] = {
                "domain": domain,
                "result": f"I encountered an error analyzing your {domain} data: {str(e)}",
                "tools_used": []
            }
            state["tools_used"] = []
        
        return state
    
    def _generate_response(self, state: HealthSessionState) -> HealthSessionState:
        """Generate final response and add to messages."""
        analysis = state.get("current_analysis", {})
        response_text = analysis.get("result", "I couldn't process your request properly.")
        
        # Add AI response to messages
        state["messages"].append(AIMessage(content=response_text))
        state["final_response"] = response_text
        
        return state
    
    def chat(self, message: str, session_id: str = None) -> str:
        """Main chat interface for health conversations."""
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "session_id": session_id or str(uuid.uuid4()),
            "current_intent": "",
            "user_timezone": {},
            "turn_count": 0,
            "current_analysis": {},
            "tools_used": [],
            "health_data_cache": {},
            "final_response": ""
        }
        
        # Execute graph
        try:
            config = {"configurable": {"thread_id": initial_state["session_id"]}}
            result = self.compiled_graph.invoke(initial_state, config=config)
            return result["final_response"]
            
        except Exception as e:
            print(f"⚠️ Graph execution error: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def route_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """Compatibility method for existing router interface."""
        session_id = str(uuid.uuid4())
        response = self.chat(query, session_id)
        
        # Extract intent from last execution (for compatibility)
        # This maintains the same interface as the old router
        return {
            "intent": "general",  # Could be enhanced to track this
            "agent": "LangGraph Health Agent",
            "response": response,
            "query": query,
            "session_id": session_id
        }


# Global instance for easy access (replaces old health_router)
health_graph = HealthAgentGraph() 