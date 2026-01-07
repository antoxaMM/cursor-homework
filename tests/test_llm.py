"""
Tests for LLM integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.llm import get_llm_response, get_llm_client


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = Mock()
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test LLM response"
    response.usage = Mock()
    response.usage.total_tokens = 100
    
    client.chat.completions.create.return_value = response
    return client


@patch('src.llm.OpenAI')
@patch('src.llm.os.getenv')
def test_get_llm_client(mock_getenv, mock_openai_class):
    """Test OpenAI client initialization."""
    mock_getenv.side_effect = lambda key, default=None: {
        'OPENROUTER_API_KEY': 'test-key',
        'OPENROUTER_BASE_URL': 'https://test.api'
    }.get(key, default)
    
    # Reset global client
    import src.llm
    src.llm._client = None
    
    client = get_llm_client()
    
    # Check that OpenAI was initialized with correct params
    mock_openai_class.assert_called_once()
    call_kwargs = mock_openai_class.call_args.kwargs
    assert call_kwargs['api_key'] == 'test-key'
    assert call_kwargs['base_url'] == 'https://test.api'


@patch('src.llm.get_llm_client')
@patch('src.llm.os.getenv')
def test_get_llm_response_simple(mock_getenv, mock_get_client, mock_openai_client):
    """Test LLM request without conversation history."""
    mock_getenv.side_effect = lambda key, default=None: {
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.7',
        'LLM_MAX_TOKENS': '500',
        'CONVERSATION_HISTORY_LIMIT': '10',
        'LLM_RETRY_ATTEMPTS': '3'
    }.get(key, default)
    
    mock_get_client.return_value = mock_openai_client
    
    response = get_llm_response(
        user_message="Hello",
        system_prompt="You are a helpful assistant"
    )
    
    # Check response
    assert response == "Test LLM response"
    
    # Check that API was called with correct messages
    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    messages = call_kwargs['messages']
    
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[0]['content'] == 'You are a helpful assistant'
    assert messages[1]['role'] == 'user'
    assert messages[1]['content'] == 'Hello'


@patch('src.llm.get_llm_client')
@patch('src.llm.os.getenv')
def test_get_llm_response_with_history(mock_getenv, mock_get_client, mock_openai_client):
    """Test LLM request with conversation history."""
    mock_getenv.side_effect = lambda key, default=None: {
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.7',
        'LLM_MAX_TOKENS': '500',
        'CONVERSATION_HISTORY_LIMIT': '10',
        'LLM_RETRY_ATTEMPTS': '3'
    }.get(key, default)
    
    mock_get_client.return_value = mock_openai_client
    
    history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]
    
    response = get_llm_response(
        user_message="New question",
        system_prompt="System prompt",
        history=history
    )
    
    # Check that API was called with history
    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    messages = call_kwargs['messages']
    
    assert len(messages) == 4  # system + 2 history + current
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    assert messages[1]['content'] == 'Previous question'
    assert messages[2]['role'] == 'assistant'
    assert messages[2]['content'] == 'Previous answer'
    assert messages[3]['role'] == 'user'
    assert messages[3]['content'] == 'New question'


@patch('src.llm.get_llm_client')
@patch('src.llm.os.getenv')
def test_get_llm_response_history_limit(mock_getenv, mock_get_client, mock_openai_client):
    """Test that history limit is applied correctly."""
    mock_getenv.side_effect = lambda key, default=None: {
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.7',
        'LLM_MAX_TOKENS': '500',
        'CONVERSATION_HISTORY_LIMIT': '3',  # Limit to 3 messages
        'LLM_RETRY_ATTEMPTS': '3'
    }.get(key, default)
    
    mock_get_client.return_value = mock_openai_client
    
    # Create history with 10 messages
    history = []
    for i in range(10):
        history.append({"role": "user", "content": f"Message {i}"})
        history.append({"role": "assistant", "content": f"Response {i}"})
    
    response = get_llm_response(
        user_message="New question",
        system_prompt="System prompt",
        history=history
    )
    
    # Check that only last 3 history messages were included
    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    messages = call_kwargs['messages']
    
    # system + 3 limited history + current = 5 messages
    assert len(messages) == 5
    assert messages[0]['role'] == 'system'
    # Last 3 from history: indices -3, -2, -1
    # history[-3] = "Response 8" (index 17 = 8*2+1)
    # history[-2] = "Message 9" (index 18 = 9*2)
    # history[-1] = "Response 9" (index 19 = 9*2+1)
    assert "Response 8" in messages[1]['content']
    assert "Message 9" in messages[2]['content']
    assert "Response 9" in messages[3]['content']


@patch('src.llm.get_llm_client')
@patch('src.llm.os.getenv')
@patch('src.llm.time.sleep')  # Mock sleep to speed up test
def test_get_llm_response_retry_success(mock_sleep, mock_getenv, mock_get_client):
    """Test retry logic when API fails then succeeds."""
    mock_getenv.side_effect = lambda key, default=None: {
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.7',
        'LLM_MAX_TOKENS': '500',
        'CONVERSATION_HISTORY_LIMIT': '10',
        'LLM_RETRY_ATTEMPTS': '3'
    }.get(key, default)
    
    client = Mock()
    # Fail twice, succeed on third attempt
    response_success = Mock()
    response_success.choices = [Mock()]
    response_success.choices[0].message = Mock()
    response_success.choices[0].message.content = "Success response"
    response_success.usage = Mock()
    response_success.usage.total_tokens = 100
    
    client.chat.completions.create.side_effect = [
        Exception("API Error 1"),
        Exception("API Error 2"),
        response_success
    ]
    
    mock_get_client.return_value = client
    
    response = get_llm_response(
        user_message="Test",
        system_prompt="System"
    )
    
    # Check that we got successful response
    assert response == "Success response"
    
    # Check that 3 attempts were made
    assert client.chat.completions.create.call_count == 3
    
    # Check that sleep was called 2 times (between attempts)
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(1)


@patch('src.llm.get_llm_client')
@patch('src.llm.os.getenv')
@patch('src.llm.time.sleep')
def test_get_llm_response_retry_all_fail(mock_sleep, mock_getenv, mock_get_client):
    """Test retry logic when all attempts fail."""
    mock_getenv.side_effect = lambda key, default=None: {
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.7',
        'LLM_MAX_TOKENS': '500',
        'CONVERSATION_HISTORY_LIMIT': '10',
        'LLM_RETRY_ATTEMPTS': '3'
    }.get(key, default)
    
    client = Mock()
    # All attempts fail
    client.chat.completions.create.side_effect = Exception("API Error")
    
    mock_get_client.return_value = client
    
    # Check that exception is raised after all retries
    with pytest.raises(Exception, match="API Error"):
        get_llm_response(
            user_message="Test",
            system_prompt="System"
        )
    
    # Check that 3 attempts were made
    assert client.chat.completions.create.call_count == 3
    
    # Check that sleep was called 2 times (not after last attempt)
    assert mock_sleep.call_count == 2

