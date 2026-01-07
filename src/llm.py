"""
LLM integration with OpenRouter via OpenAI SDK.
"""

import os
import logging
from openai import OpenAI
from typing import Optional

# Logger
logger = logging.getLogger(__name__)

# Global client instance
_client: Optional[OpenAI] = None


def get_llm_client() -> OpenAI:
    """
    Get or create OpenAI client configured for OpenRouter.
    
    Returns:
        Configured OpenAI client instance
    """
    global _client
    
    if _client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not api_key:
            logger.error("OPENROUTER_API_KEY is not set in environment variables")
            raise ValueError("OPENROUTER_API_KEY is required")
        
        _client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"OpenAI client initialized with base_url: {base_url}")
    
    return _client


def get_llm_response(user_message: str, system_prompt: str) -> str:
    """
    Get response from LLM via OpenRouter.
    
    Args:
        user_message: User's text message
        system_prompt: System prompt defining bot behavior
        
    Returns:
        LLM response text
        
    Raises:
        Exception: If LLM API call fails
    """
    client = get_llm_client()
    
    # Get LLM parameters from environment
    model = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))
    
    logger.info(f"Sending request to LLM (model: {model})")
    
    try:
        # Create chat completion request
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        # Extract response text
        assistant_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        logger.info(f"LLM response received (tokens: {tokens_used})")
        
        return assistant_message
    
    except Exception as e:
        logger.error(f"LLM API error: {e}", exc_info=True)
        raise

