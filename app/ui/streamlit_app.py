"""
Simplified Streamlit frontend for LifeBuddy - Chat interface only.
"""
import os
import requests
import streamlit as st
from typing import Dict, List, Optional, Any

# Configure Streamlit page
st.set_page_config(
    page_title="LifeBuddy - Your AI Health Companion",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration
API_BASE_URL = os.getenv("LIFEBUDDY_API_URL", "http://localhost:8000")


class LifeBuddyAPI:
    """Client for LifeBuddy FastAPI backend."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = requests.get(f"{self.base_url}/health/status", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_providers(self) -> Dict[str, Any]:
        """Get available LLM providers."""
        try:
            response = requests.get(f"{self.base_url}/providers", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"providers": []}
    
    def chat(self, message: str, session_id: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """Send message to health agent."""
        try:
            payload = {"message": message}
            if session_id:
                payload["session_id"] = session_id
            if provider:
                payload["provider"] = provider
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# Initialize API client
@st.cache_resource
def get_api_client():
    """Get cached API client."""
    return LifeBuddyAPI(API_BASE_URL)


def main():
    """Main Streamlit application - Chat interface only."""
    
    # Header
    st.title("🌟 LifeBuddy")
    st.markdown("*Your AI Health Companion*")
    
    # Check API status
    api = get_api_client()
    status = api.health_check()
    
    if status.get("status") != "healthy":
        st.error("🚨 Backend Service Unavailable")
        st.markdown(f"**Error:** {status.get('message', 'Unknown error')}")
        st.markdown("""
        Please start the FastAPI backend first:
        ```bash
        poetry run python -m app.api.main
        ```
        """)
        return
    
    # Success - show connected status
    st.success("✅ Connected to backend")
    
    # Model Provider Selection
    st.markdown("---")
    st.subheader("🤖 Model Provider")
    
    # Get available providers
    providers_data = api.get_providers()
    providers = providers_data.get("providers", [])
    
    if not providers:
        st.error("No providers available")
        return
    
    # Create provider options
    provider_options = {}
    default_provider = None
    
    for provider in providers:
        provider_options[provider["display"]] = provider["name"]
        if provider.get("default", False):
            default_provider = provider["display"]
    
    # Provider dropdown
    selected_display = st.selectbox(
        "Choose your AI model:",
        options=list(provider_options.keys()),
        index=list(provider_options.keys()).index(default_provider) if default_provider else 0,
        help="Select which AI model to use for your health conversations"
    )
    
    selected_provider = provider_options[selected_display]
    
    # Show provider info
    st.info(f"Using: **{selected_display}**")
    
    # Chat Interface
    st.markdown("---")
    st.subheader("💬 Chat with Your AI Health Companion")
    
    # Initialize session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.session_id = None
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your health data or just say hello..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = api.chat(
                    message=prompt, 
                    session_id=st.session_state.session_id,
                    provider=selected_provider
                )
                
                if "error" in response:
                    ai_response = f"Sorry, I encountered an error: {response['error']}"
                else:
                    ai_response = response.get("response", "I'm not sure how to respond to that.")
                    st.session_state.session_id = response.get("session_id")
                
                st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Chat controls
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()


if __name__ == "__main__":
    main() 