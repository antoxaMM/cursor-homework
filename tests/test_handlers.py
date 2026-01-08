"""
Tests for message and command handlers.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.handlers import (
    cmd_start,
    cmd_clear,
    handle_text,
    handle_non_text,
    conversation_history,
    conversation_meta
)


@pytest.fixture
def mock_message():
    """Create a mock Message object for testing."""
    message = AsyncMock()
    message.from_user = Mock()
    message.from_user.id = 12345
    message.from_user.username = "test_user"
    message.from_user.first_name = "Test"
    message.chat = Mock()
    message.chat.id = 12345
    message.text = "Test message"
    message.answer = AsyncMock()
    return message


@pytest.fixture(autouse=True)
def clean_conversation_storage():
    """Clean conversation storage before each test."""
    conversation_history.clear()
    conversation_meta.clear()
    yield
    conversation_history.clear()
    conversation_meta.clear()


@pytest.mark.asyncio
async def test_cmd_start(mock_message):
    """Test /start command handler."""
    await cmd_start(mock_message)
    
    # Check that greeting message was sent
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Здравствуйте" in call_args
    assert "test_user" in call_args
    assert "/clear" in call_args
    
    # Check that conversation metadata was created
    chat_id = mock_message.chat.id
    assert chat_id in conversation_meta
    assert conversation_meta[chat_id]["username"] == "test_user"
    assert "started_at" in conversation_meta[chat_id]
    assert chat_id in conversation_history
    assert len(conversation_history[chat_id]) == 0


@pytest.mark.asyncio
async def test_cmd_clear_with_history(mock_message):
    """Test /clear command when history exists."""
    chat_id = mock_message.chat.id
    
    # Create some history
    conversation_history[chat_id] = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"}
    ]
    conversation_meta[chat_id] = {"username": "test_user"}
    
    await cmd_clear(mock_message)
    
    # Check that history was cleared
    assert chat_id not in conversation_history
    assert chat_id not in conversation_meta
    
    # Check confirmation message
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "очищена" in call_args


@pytest.mark.asyncio
async def test_cmd_clear_without_history(mock_message):
    """Test /clear command when no history exists."""
    await cmd_clear(mock_message)
    
    # Check confirmation message still sent
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "очищена" in call_args


@pytest.mark.asyncio
@patch('src.handlers.get_llm_response')
@patch('src.handlers.os.getenv')
async def test_handle_text(mock_getenv, mock_llm, mock_message):
    """Test text message handler."""
    mock_getenv.return_value = "Test system prompt"
    mock_llm.return_value = "Test LLM response"
    
    await handle_text(mock_message)
    
    chat_id = mock_message.chat.id
    
    # Check that history was created and message saved
    assert chat_id in conversation_history
    assert len(conversation_history[chat_id]) == 2
    assert conversation_history[chat_id][0]["role"] == "user"
    assert conversation_history[chat_id][0]["content"] == "Test message"
    assert conversation_history[chat_id][1]["role"] == "assistant"
    assert conversation_history[chat_id][1]["content"] == "Test LLM response"
    
    # Check that LLM was called
    mock_llm.assert_called_once()
    
    # Check that response was sent to user
    mock_message.answer.assert_called_once_with("Test LLM response")


@pytest.mark.asyncio
@patch('src.handlers.get_llm_response')
@patch('src.handlers.os.getenv')
async def test_handle_text_with_existing_history(mock_getenv, mock_llm, mock_message):
    """Test that existing history is passed to LLM."""
    mock_getenv.return_value = "Test system prompt"
    mock_llm.return_value = "Response"
    
    chat_id = mock_message.chat.id
    
    # Create existing history
    conversation_history[chat_id] = [
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ]
    conversation_meta[chat_id] = {"username": "test_user"}
    
    await handle_text(mock_message)
    
    # Check that history was passed to LLM (excluding current message)
    call_kwargs = mock_llm.call_args.kwargs
    assert "history" in call_kwargs
    assert len(call_kwargs["history"]) == 2
    
    # Check that new messages were added
    assert len(conversation_history[chat_id]) == 4


@pytest.mark.asyncio
@patch('src.handlers.get_llm_response')
@patch('src.handlers.os.getenv')
async def test_handle_text_error_removes_from_history(mock_getenv, mock_llm, mock_message):
    """Test that user message is removed from history on error."""
    mock_getenv.return_value = "Test system prompt"
    mock_llm.side_effect = Exception("LLM Error")
    
    chat_id = mock_message.chat.id
    
    await handle_text(mock_message)
    
    # Check that history is empty (user message was removed)
    assert len(conversation_history[chat_id]) == 0
    
    # Check that error message was sent
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Извините" in call_args
    assert "ошибка" in call_args


@pytest.mark.asyncio
async def test_handle_non_text(mock_message):
    """Test non-text message handler."""
    # Remove text to simulate non-text message
    mock_message.text = None
    
    await handle_non_text(mock_message)
    
    # Check that warning message was sent
    mock_message.answer.assert_called_once()
    call_args = mock_message.answer.call_args[0][0]
    assert "Контент не распознан" in call_args
    assert "текстовое сообщение" in call_args


