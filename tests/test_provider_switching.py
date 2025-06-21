"""
Test provider switching functionality in the API.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.api.main import app


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    # Mock the global health service and agent
    with patch('app.api.main.health_service') as mock_health_service, \
         patch('app.api.main.health_agent') as mock_health_agent:
        
        # Set up mock health service
        mock_health_service_instance = MagicMock()
        mock_health_service_instance._get_user_timezone.return_value = "UTC"
        mock_health_service.return_value = mock_health_service_instance
        
        # Set up mock health agent
        mock_health_agent_instance = MagicMock()
        mock_health_agent_instance.chat.return_value = "Test response"
        mock_health_agent.return_value = mock_health_agent_instance
        
        # Override the module-level variables by patching the imports
        import app.api.main as main_module
        main_module.health_service = mock_health_service_instance
        main_module.health_agent = mock_health_agent_instance
        
        yield TestClient(app)


def test_default_provider_ollama(client):
    """Test that default provider is Ollama when no provider specified."""
    response = client.post("/chat", json={
        "message": "Hello",
        "session_id": "test_session"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == "test_session"
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0


def test_provider_switching_openai(client):
    """Test switching to OpenAI provider (expects API key error)."""
    # This test will use the mocked agent from the fixture
    response = client.post("/chat", json={
        "message": "Hello",
        "session_id": "test_session",
        "provider": "openai"
    })
    
    # Expect 500 error due to missing API key (this proves provider switching works)
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "OPENAI_API_KEY environment variable is required" in data["detail"]


def test_environment_variable_restoration():
    """Test that environment variables are properly restored after provider switching."""
    original_provider = os.getenv("LLM_PROVIDER")
    
    # Mock the global health service and agent for this test
    with patch('app.api.main.health_service') as mock_health_service, \
         patch('app.api.main.health_agent') as mock_health_agent:
        
        # Set up mocks
        mock_health_service_instance = MagicMock()
        mock_health_service_instance._get_user_timezone.return_value = "UTC"
        mock_health_agent_instance = MagicMock()
        mock_health_agent_instance.chat.return_value = "Test response"
        
        # Override module variables
        import app.api.main as main_module
        main_module.health_service = mock_health_service_instance
        main_module.health_agent = mock_health_agent_instance
        
        client = TestClient(app)
        
        # Make request with different provider
        response = client.post("/chat", json={
            "message": "Hello",
            "provider": "anthropic"
        })
        
        # Expect 500 error due to missing dependency (this proves provider switching works)
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "langchain-anthropic" in data["detail"]
        
        # Verify environment variable was restored
        assert os.getenv("LLM_PROVIDER") == original_provider


def test_provider_list_endpoint(client):
    """Test that the providers endpoint returns available providers."""
    response = client.get("/providers")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "providers" in data
    providers = data["providers"]
    
    # Check that all expected providers are listed
    provider_names = [p["name"] for p in providers]
    expected_providers = ["ollama", "openai", "anthropic", "google", "azure"]
    
    for expected in expected_providers:
        assert expected in provider_names
    
    # Check that Ollama is marked as default
    ollama_provider = next(p for p in providers if p["name"] == "ollama")
    assert ollama_provider["default"] is True


if __name__ == "__main__":
    pytest.main([__file__]) 