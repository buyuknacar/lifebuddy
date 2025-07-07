"""
Simplified Streamlit frontend for LifeBuddy - Chat interface only.
"""
import os
import requests
import streamlit as st
from typing import Dict, List, Optional, Any
import re

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


def parse_user_profile() -> Dict[str, Any]:
    """Parse user profile from markdown file."""
    try:
        profile_path = "data/user_profile.md"
        if not os.path.exists(profile_path):
            return {"exists": False}
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract key information using regex
        profile_data: Dict[str, Any] = {"exists": True}
        
        # Basic info
        name_match = re.search(r'\*\*Name\*\*:\s*(.+)', content)
        age_match = re.search(r'\*\*Age\*\*:\s*(.+)', content)
        gender_match = re.search(r'\*\*Gender\*\*:\s*(.+)', content)
        
        # Fitness level
        experience_match = re.search(r'\*\*Experience\*\*:\s*(.+)', content)
        activity_match = re.search(r'\*\*Current Activity\*\*:\s*(.+)', content)
        
        # Goals
        goal_match = re.search(r'\*\*Primary Goal\*\*:\s*(.+)', content)
        timeline_match = re.search(r'\*\*Timeline\*\*:\s*(.+)', content)
        
        # Health & Limitations
        injuries_match = re.search(r'\*\*Injuries/Conditions\*\*:\s*(.+)', content)
        limitations_match = re.search(r'\*\*Physical Limitations\*\*:\s*(.+)', content)
        
        # Preferences
        days_match = re.search(r'\*\*Available Days per Week\*\*:\s*(.+)', content)
        duration_match = re.search(r'\*\*Workout Duration\*\*:\s*(.+)', content)
        location_match = re.search(r'\*\*Location\*\*:\s*(.+)', content)
        
        # Assign values if found
        profile_data["name"] = name_match.group(1).strip() if name_match else ""
        profile_data["age"] = age_match.group(1).strip() if age_match else ""
        profile_data["gender"] = gender_match.group(1).strip() if gender_match else ""
        profile_data["experience"] = experience_match.group(1).strip() if experience_match else ""
        profile_data["activity"] = activity_match.group(1).strip() if activity_match else ""
        profile_data["goal"] = goal_match.group(1).strip() if goal_match else ""
        profile_data["timeline"] = timeline_match.group(1).strip() if timeline_match else ""
        profile_data["injuries"] = injuries_match.group(1).strip() if injuries_match else ""
        profile_data["limitations"] = limitations_match.group(1).strip() if limitations_match else ""
        profile_data["days"] = days_match.group(1).strip() if days_match else ""
        profile_data["duration"] = duration_match.group(1).strip() if duration_match else ""
        profile_data["location"] = location_match.group(1).strip() if location_match else ""
        
        # Check if profile is filled out (has at least name and age)
        profile_data["is_filled"] = bool(profile_data["name"] and profile_data["age"])
        
        return profile_data
    
    except Exception as e:
        return {"exists": False, "error": str(e)}


def display_profile_card():
    """Display user profile card in sidebar."""
    profile = parse_user_profile()
    
    if not profile.get("exists", False):
        st.sidebar.warning("📝 No profile found - Create data/user_profile.md")
        return
    
    if not profile.get("is_filled", False):
        st.sidebar.warning("📝 Profile incomplete - Fill out your profile")
        return
    
    # Profile card
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Your Profile")
    
    # Basic info
    if profile["name"]:
        st.sidebar.markdown(f"**Name:** {profile['name']}")
    if profile["age"]:
        st.sidebar.markdown(f"**Age:** {profile['age']}")
    if profile["gender"]:
        st.sidebar.markdown(f"**Gender:** {profile['gender']}")
    
    # Fitness level
    if profile["experience"] or profile["activity"]:
        st.sidebar.markdown("**Fitness Level:**")
        if profile["experience"]:
            st.sidebar.markdown(f"• {profile['experience']}")
        if profile["activity"]:
            st.sidebar.markdown(f"• {profile['activity']}")
    
    # Goals
    if profile["goal"]:
        st.sidebar.markdown("**Primary Goal:**")
        st.sidebar.markdown(f"• {profile['goal']}")
    
    # Health considerations
    if profile["injuries"] or profile["limitations"]:
        st.sidebar.markdown("**Health Notes:**")
        if profile["injuries"]:
            st.sidebar.markdown(f"• {profile['injuries']}")
        if profile["limitations"]:
            st.sidebar.markdown(f"• {profile['limitations']}")
    
    # Preferences
    if profile["days"] or profile["duration"] or profile["location"]:
        st.sidebar.markdown("**Preferences:**")
        if profile["days"]:
            st.sidebar.markdown(f"• {profile['days']}")
        if profile["duration"]:
            st.sidebar.markdown(f"• {profile['duration']}")
        if profile["location"]:
            st.sidebar.markdown(f"• {profile['location']}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("✅ *AI Coach has your profile*")


def main():
    """Main Streamlit application - Chat interface only."""
    
    # Header
    st.title("🌟 LifeBuddy")
    st.markdown("*Your AI Health Companion*")
    
    # Check API status (silently)
    api = get_api_client()
    status = api.health_check()
    
    if status.get("status") != "healthy":
        st.error("🚨 Backend Service Unavailable")
        st.markdown("""
        Please start the FastAPI backend first:
        ```bash
        poetry run python -m app.api.main
        ```
        """)
        return
    
    # Model Provider Selection (compact)
    with st.expander("🤖 AI Model", expanded=False):
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
            "Choose AI model:",
            options=list(provider_options.keys()),
            index=list(provider_options.keys()).index(default_provider) if default_provider else 0,
            help="Select which AI model to use for health conversations"
        )
        
        selected_provider = provider_options[selected_display]
        st.info(f"Using: **{selected_display}**")
    
    # Initialize session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.session_id = None
    
    # Display profile card in sidebar
    display_profile_card()
    
    # Chat Introduction (only show when chat is empty)
    if len(st.session_state.messages) == 0:
        st.markdown("---")
        st.markdown("""
        ### 💬 Hi there!
        
        ---
        """)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your health data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            # Create placeholder for thinking chain
            thinking_placeholder = st.empty()
            response_placeholder = st.empty()
            
            with thinking_placeholder.container():
                st.info("🤔 Thinking...")
            
            # Get response from API
            response = api.chat(
                message=prompt, 
                session_id=st.session_state.session_id,
                provider=selected_provider
            )
            
            if "error" in response:
                ai_response = f"Sorry, I encountered an error: {response['error']}"
                thinking_chain = []
            else:
                ai_response = response.get("response", "I'm not sure how to respond to that.")
                thinking_chain = response.get("thinking_chain", [])
                st.session_state.session_id = response.get("session_id")
            
            # Show thinking chain if available
            if thinking_chain:
                with thinking_placeholder.container():
                    # Only show "Health Data Retrieved" if actually retrieving health data
                    has_health_data = any(step.get('tool_name', '').startswith('get_') for step in thinking_chain)
                    if has_health_data:
                        st.success("🔍 **Health Data Retrieved:**")
                    else:
                        st.success("🤖 **AI Processing:**")
                    
                    for i, step in enumerate(thinking_chain):
                        with st.expander(f"📊 {step.get('tool_name', 'Unknown')}", expanded=False):
                            st.text(f"Input: {step.get('tool_input', 'N/A')}")
                            st.text("Data:")
                            st.code(step.get('tool_output', 'No output'), language="json")
            else:
                thinking_placeholder.empty()
            
            # Show final response
            with response_placeholder.container():
                st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Chat controls (bottom)
    if len(st.session_state.messages) > 0:
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.session_state.session_id = None
                st.rerun()


if __name__ == "__main__":
    main() 