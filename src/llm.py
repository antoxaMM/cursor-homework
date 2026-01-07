"""
LLM integration with OpenRouter via OpenAI SDK.
"""

import os
import logging
import time
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


def get_llm_response(
    user_message: str, 
    system_prompt: str,
    history: list[dict] | None = None
) -> str:
    """
    Get response from LLM via OpenRouter with conversation history.
    
    Args:
        user_message: User's current text message
        system_prompt: System prompt defining bot behavior
        history: Previous conversation messages (optional)
        
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
    history_limit = int(os.getenv("CONVERSATION_HISTORY_LIMIT", "10"))
    retry_attempts = int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))
    
    # Build messages list for LLM
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history with limit
    if history:
        # Apply limit: take last N messages
        limited_history = history[-history_limit:] if len(history) > history_limit else history
        messages.extend(limited_history)
        logger.info(f"Including {len(limited_history)} messages from history (limit: {history_limit})")
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    logger.info(f"Sending request to LLM (model: {model}, total messages: {len(messages)})")
    
    # Retry logic
    last_error = None
    
    for attempt in range(1, retry_attempts + 1):
        try:
            # Create chat completion request
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response text
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"LLM response received (tokens: {tokens_used})")
            
            return assistant_message
        
        except Exception as e:
            last_error = e
            
            if attempt < retry_attempts:
                # Not the last attempt - log warning and retry
                logger.warning(
                    f"LLM API error (attempt {attempt}/{retry_attempts}): {e}. "
                    f"Retrying in 1 second..."
                )
                time.sleep(1)  # Pause before retry
            else:
                # Last attempt failed - log error with full traceback
                logger.error(
                    f"LLM API error after {retry_attempts} attempts: {e}",
                    exc_info=True
                )
    
    # All attempts failed - raise the last error
    raise last_error

