"""
FastAPI backend for LifeBuddy health analytics platform.
Provides REST API endpoints and WebSocket chat interface.
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.health_data_service import HealthDataService
from app.agents.health_graph import HealthAgentGraph
from app.core.llm_provider import LLMProvider
from app.core.logger import get_api_logger

# Initialize logger
logger = get_api_logger()


# Pydantic models for API requests/responses
class HealthQuery(BaseModel):
    """Request model for health data queries."""
    metric_type: str = Field(..., description="Type of health metric to query")
    days_back: int = Field(default=7, ge=1, le=365, description="Number of days to look back")


class ChatMessage(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., description="User message to the health agent")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    provider: Optional[str] = Field(None, description="LLM provider to use (ollama, openai, anthropic, google, azure)")
    model: Optional[str] = Field(None, description="Specific model to use (e.g., gpt-4o, claude-3-sonnet-20240229)")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthMetricsResponse(BaseModel):
    """Response model for health metrics."""
    data: Dict[str, Any] = Field(..., description="Health metrics data")
    query_info: Dict[str, Any] = Field(..., description="Query metadata")


# Global instances
health_service: Optional[HealthDataService] = None
health_agent: Optional[HealthAgentGraph] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup."""
    global health_service, health_agent
    
    logger.info("Starting LifeBuddy FastAPI backend...")
    
    # Initialize health data service
    try:
        health_service = HealthDataService()
        logger.info("Health data service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize health data service: {e}")
        raise
    
    # Initialize health agent
    try:
        health_agent = HealthAgentGraph()
        logger.info("Health agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize health agent: {e}")
        raise
    
    logger.info("LifeBuddy backend ready!")
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down LifeBuddy backend...")


# Create FastAPI app
app = FastAPI(
    title="LifeBuddy API",
    description="AI-powered personal health and wellness companion API",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get health service
def get_health_service() -> HealthDataService:
    """Dependency to get health data service."""
    if health_service is None:
        raise HTTPException(status_code=500, detail="Health service not initialized")
    return health_service


def get_health_agent() -> HealthAgentGraph:
    """Dependency to get health agent."""
    if health_agent is None:
        raise HTTPException(status_code=500, detail="Health agent not initialized")
    return health_agent


# Health endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LifeBuddy API",
        "version": "0.1.0",
        "description": "AI-powered personal health and wellness companion",
        "endpoints": {
            "health": "/health/*",
            "chat": "/chat",
            "websocket": "/ws"
        }
    }


@app.get("/health/status")
async def health_status():
    """Check API health status."""
    try:
        # Test database connection
        service = get_health_service()
        user_tz = service._get_user_timezone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timezone": user_tz,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/providers")
async def get_available_providers():
    """Get list of available LLM providers."""
    return {
        "providers": [
            {"name": "ollama", "display": "Ollama (Local)", "default": True},
            {"name": "openai", "display": "OpenAI GPT", "default": False},
            {"name": "anthropic", "display": "Anthropic Claude", "default": False},
            {"name": "google", "display": "Google Gemini", "default": False},
            {"name": "azure", "display": "Azure OpenAI", "default": False}
        ]
    }


@app.get("/health/steps", response_model=HealthMetricsResponse)
async def get_steps(
    days_back: int = 7,
    service: HealthDataService = Depends(get_health_service)
):
    """Get daily step counts."""
    try:
        data = service.get_daily_steps(days_back)
        return HealthMetricsResponse(
            data=data,
            query_info={
                "metric_type": "steps",
                "days_back": days_back,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/heart-rate", response_model=HealthMetricsResponse)
async def get_heart_rate(
    days_back: int = 7,
    service: HealthDataService = Depends(get_health_service)
):
    """Get heart rate summary."""
    try:
        data = service.get_heart_rate_summary(days_back)
        return HealthMetricsResponse(
            data=data,
            query_info={
                "metric_type": "heart_rate",
                "days_back": days_back,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/workouts", response_model=HealthMetricsResponse)
async def get_workouts(
    limit: int = 10,
    service: HealthDataService = Depends(get_health_service)
):
    """Get recent workouts."""
    try:
        data = service.get_recent_workouts(limit)
        return HealthMetricsResponse(
            data=data,
            query_info={
                "metric_type": "workouts",
                "limit": limit,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health/weight", response_model=HealthMetricsResponse)
async def get_weight(
    days_back: int = 30,
    service: HealthDataService = Depends(get_health_service)
):
    """Get weight progress."""
    try:
        data = service.get_weight_progress(days_back)
        return HealthMetricsResponse(
            data=data,
            query_info={
                "metric_type": "weight",
                "days_back": days_back,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/health/search", response_model=HealthMetricsResponse)
async def search_health_data(
    query: HealthQuery,
    service: HealthDataService = Depends(get_health_service)
):
    """Search for specific health data."""
    try:
        data = service.search_health_data(query.metric_type, query.days_back)
        return HealthMetricsResponse(
            data=data,
            query_info={
                "metric_type": query.metric_type,
                "days_back": query.days_back,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_message(
    chat_request: ChatMessage,
    agent: HealthAgentGraph = Depends(get_health_agent)
):
    """Send a message to the health agent."""
    try:
        session_id = chat_request.session_id or "default"
        
        # Handle dynamic provider switching
        if chat_request.provider:
            # Create a new agent instance with the requested provider
            import os
            
            # Temporarily override the environment variable
            original_provider = os.getenv("LLM_PROVIDER")
            os.environ["LLM_PROVIDER"] = chat_request.provider
            
            try:
                # Create new LLM provider and agent with the requested provider
                dynamic_llm_provider = LLMProvider()
                dynamic_llm = dynamic_llm_provider.get_llm()
                
                # Create a new agent instance with the dynamic LLM
                from app.agents.health_graph import HealthAgentGraph
                dynamic_agent = HealthAgentGraph()
                dynamic_agent.update_llm(dynamic_llm)  # Use the update method
                
                # Use the dynamic agent for this request
                response = dynamic_agent.chat(
                    message=chat_request.message,
                    session_id=session_id
                )
                
            finally:
                # Restore original provider
                if original_provider:
                    os.environ["LLM_PROVIDER"] = original_provider
                else:
                    os.environ.pop("LLM_PROVIDER", None)
        else:
            # Use default agent (Ollama from Docker environment)
            response = agent.chat(
                message=chat_request.message,
                session_id=session_id
            )
        
        return ChatResponse(
            response=response,
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# WebSocket for real-time chat
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket)
    session_id = None
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            session_id = message_data.get("session_id", session_id)
            provider = message_data.get("provider")  # Add provider support
            
            if not user_message:
                await manager.send_personal_message(
                    json.dumps({"error": "Empty message"}), 
                    websocket
                )
                continue
            
            # Process with health agent
            try:
                # Handle dynamic provider switching (same logic as HTTP endpoint)
                if provider:
                    import os
                    original_provider = os.getenv("LLM_PROVIDER")
                    os.environ["LLM_PROVIDER"] = provider
                    
                    try:
                        dynamic_llm_provider = LLMProvider()
                        dynamic_llm = dynamic_llm_provider.get_llm()
                        
                        from app.agents.health_graph import HealthAgentGraph
                        dynamic_agent = HealthAgentGraph()
                        dynamic_agent.update_llm(dynamic_llm)
                        
                        response = dynamic_agent.chat(user_message, session_id)
                        
                    finally:
                        if original_provider:
                            os.environ["LLM_PROVIDER"] = original_provider
                        else:
                            os.environ.pop("LLM_PROVIDER", None)
                else:
                    # Use default agent
                    agent = get_health_agent()
                    response = agent.chat(user_message, session_id)
                
                # Send response back to client
                response_data = {
                    "response": response,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                await manager.send_personal_message(
                    json.dumps(response_data), 
                    websocket
                )
                
            except Exception as e:
                error_response = {
                    "error": f"Processing error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(
                    json.dumps(error_response), 
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for session: {session_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 