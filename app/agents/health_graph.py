"""
LangGraph-based Health Agent System for LifeBuddy.
Migrates existing router and agent functionality to a graph-based agentic approach.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Any, TypedDict, Annotated, Literal, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

from app.core.llm_provider import LLMProvider
from app.core.health_tools import get_fitness_tools, get_nutrition_tools, get_wellness_tools, get_general_tools
from app.core.health_data_service import HealthDataService
from app.agents.intent_classifier import IntentClassifier, HealthIntent
from app.core.logger import get_agent_logger

# Initialize logger
logger = get_agent_logger()


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
        """Initialize the health agent graph."""
        # Initialize LLM provider
        self.llm_provider = LLMProvider()
        self.llm = self.llm_provider.get_llm()
        
        # Initialize other services
        self.health_service = HealthDataService()
        self.intent_classifier = IntentClassifier()
        
        # Initialize health tools with LLM
        self._init_tools()
        
        # Build the graph
        self.compiled_graph = self._build_graph().compile()
    
    def _init_tools(self):
        """Initialize health tools with current LLM."""
        # Use the existing tool functions that are already imported
        self.fitness_tools = get_fitness_tools()
        self.nutrition_tools = get_nutrition_tools()
        self.wellness_tools = get_wellness_tools()
        self.general_tools = get_general_tools()
    
    def update_llm(self, new_llm):
        """Update the LLM and rebuild tools and graph."""
        self.llm = new_llm
        self._init_tools()
        # Note: We don't rebuild the compiled graph as it's expensive
        # The tools will use the new LLM instance
    
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
            logger.warning(f"Error loading timezone: {e}")
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
            logger.warning(f"Intent classification error: {e}")
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

Always speak directly to the user using "you" and "your" (not "the user").
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

Always speak directly to the user using "you" and "your" (not "the user").
Keep responses evidence-based, balanced, and practical."""
        )
    
    def _wellness_analysis(self, state: HealthSessionState) -> HealthSessionState:
        """Execute wellness-focused analysis using existing tools and prompts."""
        return self._execute_specialized_analysis(
            state,
            "wellness",
            self.wellness_tools,
            """You are a wellness mentor AI with direct access to sleep and health data. Help users with:
- Sleep quality analysis and improvement
- Stress management and mental health  
- Mood tracking and emotional wellness
- Mindfulness and self-care practices

For sleep questions, immediately use the get_sleep_data tool with appropriate days (7 for recent, 30 for monthly trends).
For heart rate questions, use get_heart_rate_summary.
For overall wellness, use get_activity_summary.

IMPORTANT: Answer ONLY what the user specifically asked. Do not ask follow-up questions or provide additional analysis unless requested. Be direct and focused on their exact question.

Always speak directly to the user using "you" and "your" (not "the user").
Keep responses supportive, thoughtful, and data-driven."""
        )
    
    def _general_analysis(self, state: HealthSessionState) -> HealthSessionState:
        """Handle general conversation using fallback persona - no health data analysis."""
        from langchain_core.prompts import ChatPromptTemplate
        
        # For general/conversational queries, use simple LLM without tools
        latest_message = state["messages"][-1]
        user_query = str(latest_message.content)
        
        # Use friendly persona for all general intent queries (greetings, casual conversation, non-health topics)
        persona_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are LifeBuddy, a friendly AI health companion. You help users analyze their personal health data and provide insights.

You have access to tools that can analyze:
- Step counts and activity levels
- Heart rate and fitness metrics  
- Workout history and performance
- Weight tracking and trends
- Sleep and wellness patterns

For greetings, casual conversation, and non-health topics, be warm and friendly. Introduce your capabilities when appropriate.
If users ask about specific health data, guide them to ask more specific questions like "show my steps" or "analyze my workouts".

Always speak directly to the user using "you" and "your" (not "the user").
Keep responses concise and personable."""),
            ("human", "{query}")
        ])
        
        try:
            chain = persona_prompt | self.llm
            result = chain.invoke({"query": user_query})
            response_text = str(result.content) if hasattr(result, 'content') else str(result)
            
            state["current_analysis"] = {
                "domain": "general_conversation",
                "result": response_text,
                "tools_used": [],
                "thinking_chain": []  # No tools used in general conversation
            }
            
        except Exception as e:
            logger.warning(f"General conversation error: {e}")
            state["current_analysis"] = {
                "domain": "general_conversation", 
                "result": "Hello! I'm LifeBuddy, your AI health companion. I can help you analyze your health data including steps, workouts, heart rate, and more. What would you like to know about your health?",
                "tools_used": [],
                "thinking_chain": []
            }
        
        return state
    
    def _execute_specialized_analysis(self, state: HealthSessionState, domain: str, tools: List, system_prompt_template: str) -> HealthSessionState:
        """Execute specialized analysis using simple single-step tool prompting for small models."""
        from langchain_core.prompts import ChatPromptTemplate
        import re
        import json
        
        # Format system prompt with timezone info
        system_prompt = system_prompt_template.format(
            timezone_name=state['user_timezone']['name'],
            timezone_offset=state['user_timezone']['offset']
        )
        
        latest_message = state["messages"][-1]
        user_query = str(latest_message.content)
        
        # Create available tools list for the prompt
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        tools_text = "\n".join(tool_descriptions)
        
        # Single-step tool selection prompt - much simpler than ReAct
        tool_selection_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{system_prompt}

Available tools:
{tools_text}

Your task: Identify which tool to use and what input to provide.

Respond with EXACTLY this format:
TOOL: [tool_name]
INPUT: [input_value]

Examples:
User: "show my heart rate"
TOOL: get_heart_rate_summary  
INPUT: 7

User: "steps last 2 weeks"
TOOL: get_daily_steps
INPUT: 14

User: "my sleep patterns"  
TOOL: get_sleep_data
INPUT: 7

Be precise with the format. Use only tool names from the list above."""),
            ("human", "{query}")
        ])
        
        thinking_chain = []
        try:
            # Step 1: Get tool selection from LLM
            chain = tool_selection_prompt | self.llm
            result = chain.invoke({"query": user_query})
            response_text = str(result.content) if hasattr(result, 'content') else str(result)
            
            # Debug: Log what LLM generated
            logger.info(f"LLM tool selection output: {response_text}")
            
            # Step 2: Parse the simple format
            tool_match = re.search(r'TOOL:\s*(\w+)', response_text)
            input_match = re.search(r'INPUT:\s*(\w+)', response_text)
            
            if tool_match and input_match:
                tool_name = tool_match.group(1)
                tool_input = input_match.group(1)
                
                # Step 3: Find and execute the tool
                selected_tool = None
                for tool in tools:
                    if tool.name == tool_name:
                        selected_tool = tool
                        break
                
                if selected_tool:
                    # Execute the tool directly
                    tool_result = selected_tool.func(tool_input)
                    
                    # Record thinking chain
                    thinking_chain.append({
                        "tool_name": tool_name,
                        "tool_input": tool_input, 
                        "tool_output": tool_result
                    })
                    
                    # Step 4: Format response using LLM
                    # Escape any curly braces in tool_result to avoid template variable issues
                    escaped_tool_result = tool_result.replace("{", "{{").replace("}", "}}")
                    
                    response_prompt = ChatPromptTemplate.from_messages([
                        ("system", f"""{system_prompt}

The user asked: {user_query}

I retrieved this health data:
{escaped_tool_result}

Please provide a helpful, natural response to the user based on this data. Be friendly and conversational."""),
                        ("human", "Please analyze and explain this health data.")
                    ])
                    
                    response_chain = response_prompt | self.llm
                    final_response = response_chain.invoke({})
                    final_text = str(final_response.content) if hasattr(final_response, 'content') else str(final_response)
                    
                    state["current_analysis"] = {
                        "domain": domain,
                        "result": final_text,
                        "tools_used": [tool_name],
                        "thinking_chain": thinking_chain
                    }
                    state["tools_used"] = [tool_name]
                    
                else:
                    # Tool not found
                    state["current_analysis"] = {
                        "domain": domain,
                        "result": f"I tried to use '{tool_name}' but it's not available. Please try asking about steps, heart rate, workouts, or sleep data.",
                        "tools_used": [],
                        "thinking_chain": []
                    }
                    state["tools_used"] = []
            else:
                # Parsing failed - provide helpful guidance
                state["current_analysis"] = {
                    "domain": domain,
                    "result": f"I'm having trouble understanding your {domain} question. Try asking something like 'show my heart rate' or 'get my steps for last week'.",
                    "tools_used": [],
                    "thinking_chain": []
                }
                state["tools_used"] = []
        
        except Exception as e:
            logger.warning(f"{domain.title()} analysis error: {e}")
            
            # Fallback: Provide helpful response even when tools fail
            user_query_lower = user_query.lower()
            
            fallback_response = f"I'm having trouble accessing your {domain} data right now. "
            
            # Add domain-specific guidance
            if domain == "fitness" and any(word in user_query_lower for word in ["heart", "rate", "steps", "workout"]):
                fallback_response += "I can help you with heart rate analysis, step tracking, and workout insights when my data tools are working. Try asking me to 'get my heart rate summary' or 'show my recent workouts'."
            elif domain == "nutrition" and any(word in user_query_lower for word in ["weight", "calories", "diet"]):
                fallback_response += "I can help you with weight tracking and nutrition analysis when my data tools are working. Try asking me to 'show my weight progress' or 'analyze my calorie burn'."
            elif domain == "wellness" and any(word in user_query_lower for word in ["sleep", "stress", "mood"]):
                fallback_response += "I can help you with sleep analysis and wellness insights when my data tools are working. Try asking me to 'analyze my sleep data' or 'show my stress indicators'."
            else:
                fallback_response += "Please try rephrasing your question or ask me about a specific health metric like steps, heart rate, or sleep."
            
            state["current_analysis"] = {
                "domain": domain,
                "result": fallback_response,
                "tools_used": [],
                "thinking_chain": []
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
    
    def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
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
            result = self.compiled_graph.invoke(initial_state)
            # Extract thinking chain from current_analysis
            current_analysis = result.get("current_analysis", {})
            thinking_chain = current_analysis.get("thinking_chain", [])
            
            return {
                "response": result["final_response"],
                "thinking_chain": thinking_chain,
                "intent": result.get("current_intent", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "thinking_chain": [],
                "intent": "error"
            }
    
    def route_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """Compatibility method for existing router interface."""
        session_id = str(uuid.uuid4())
        response = self.chat(query, session_id)
        
        # Extract intent from last execution (for compatibility)
        # This maintains the same interface as the old router
        return {
            "intent": "general",  # Could be enhanced to track this
            "agent": "LangGraph Health Agent",
            "response": response["response"],
            "query": query,
            "session_id": session_id
        }


# Global instance for easy access (replaces old health_router)
health_graph = HealthAgentGraph() 