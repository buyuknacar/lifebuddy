"""
LLM Provider abstraction supporting multiple providers through LangChain.
Ollama is the primary open-source option, with API-based providers available.
"""
import os
from langchain_core.language_models import BaseChatModel


class LLMProvider:
    """Factory for creating LLM instances based on configuration."""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama")
    
    def get_llm(self) -> BaseChatModel:
        """Get the configured LLM instance."""
        if self.provider == "ollama":
            return self._get_ollama_llm()
        elif self.provider == "openai":
            return self._get_openai_llm()
        elif self.provider == "anthropic":
            return self._get_anthropic_llm()
        elif self.provider == "google":
            return self._get_google_llm()
        elif self.provider == "azure":
            return self._get_azure_llm()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _get_ollama_llm(self) -> BaseChatModel:
        """Get Ollama LLM instance (open source)."""
        from langchain_ollama import ChatOllama
        
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Optimize parameters for tool use with small models
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0.0,  # Lower temperature for more consistent tool calls
            top_p=0.9,        # Reduce randomness 
            repeat_penalty=1.1,  # Prevent repetition
            num_predict=512  # Limit response length
        )
    
    def _get_openai_llm(self) -> BaseChatModel:
        """Get OpenAI LLM instance."""
        from langchain_openai import ChatOpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return ChatOpenAI(
            model=model,
            temperature=0.1,
            max_completion_tokens=1024,
            timeout=60,
            max_retries=2
        )
    
    def _get_anthropic_llm(self) -> BaseChatModel:
        """Get Anthropic Claude LLM instance."""
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("Install langchain-anthropic: pip install langchain-anthropic")
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        return ChatAnthropic(
            model_name=model,
            temperature=0.1,
            max_tokens_to_sample=1024,
            timeout=60,
            max_retries=2,
            stop=None
        )
    
    def _get_google_llm(self) -> BaseChatModel:
        """Get Google Gemini LLM instance."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError("Install langchain-google-genai: pip install langchain-google-genai")
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        model = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-001")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=0.1,
            max_tokens=1024,
            timeout=60,
            max_retries=2
        )
    
    def _get_azure_llm(self) -> BaseChatModel:
        """Get Azure OpenAI LLM instance."""
        from langchain_openai import AzureChatOpenAI
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        
        if not all([api_key, endpoint, deployment]):
            raise ValueError("AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT are required")
        
        return AzureChatOpenAI(
            azure_deployment=deployment,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
            temperature=0.1,
            max_tokens=1024,
            timeout=60,
            max_retries=2
        )


# Global LLM provider instance
llm_provider = LLMProvider() 