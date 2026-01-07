"""
Message and command handlers for the Telegram bot.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import logging
import os
from datetime import datetime

from src.llm import get_llm_response

# Create router for handlers
router = Router()

# Logger
logger = logging.getLogger(__name__)

# In-memory storage for conversation history
conversation_history: dict[int, list[dict]] = {}
conversation_meta: dict[int, dict] = {}


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Handle /start command with a greeting message.
    
    Args:
        message: Incoming message from user
    """
    user = message.from_user
    chat_id = message.chat.id
    username = user.username or user.first_name or "пользователь"
    
    logger.info(f"User @{username} (ID: {user.id}) started the bot")
    
    # Initialize conversation metadata if new user
    if chat_id not in conversation_meta:
        conversation_meta[chat_id] = {
            "username": username,
            "started_at": datetime.now().isoformat()
        }
        conversation_history[chat_id] = []
        logger.info(f"Created new conversation for chat_id: {chat_id}")
    
    greeting = (
        f"Здравствуйте, {username}! 👋\n\n"
        "Я бот-ассистент для консультаций. "
        "Напишите мне текстовое сообщение, и я отвечу вам.\n\n"
        "Используйте /clear для очистки истории диалога."
    )
    
    await message.answer(greeting)


@router.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    """
    Clear conversation history for current user.
    
    Args:
        message: Incoming message from user
    """
    chat_id = message.chat.id
    user = message.from_user
    username = user.username or "unknown"
    
    # Clear history if exists
    if chat_id in conversation_history:
        msg_count = len(conversation_history[chat_id])
        del conversation_history[chat_id]
        del conversation_meta[chat_id]
        logger.info(f"Cleared conversation history for @{username} (chat_id: {chat_id}, messages: {msg_count})")
    else:
        logger.info(f"No history to clear for @{username} (chat_id: {chat_id})")
    
    await message.answer(
        "История диалога очищена. Можем начать с чистого листа! 🔄"
    )


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """
    Process text message with LLM using conversation history.
    
    Args:
        message: Incoming text message from user
    """
    user = message.from_user
    chat_id = message.chat.id
    username = user.username or "unknown"
    
    logger.info(f"Received text from @{username} (ID: {user.id}): {message.text}")
    
    # Initialize history if new user
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []
        conversation_meta[chat_id] = {
            "username": username,
            "started_at": datetime.now().isoformat()
        }
        logger.info(f"Created new conversation for chat_id: {chat_id}")
    
    # Add user message to history
    conversation_history[chat_id].append({
        "role": "user",
        "content": message.text
    })
    
    # Get system prompt from environment
    system_prompt = os.getenv("SYSTEM_PROMPT", "Вы - полезный ИИ-ассистент.")
    
    try:
        # Get response from LLM with conversation history
        llm_response = get_llm_response(
            user_message=message.text,
            system_prompt=system_prompt,
            history=conversation_history[chat_id][:-1]  # Exclude current message (already in user_message)
        )
        
        # Add assistant response to history
        conversation_history[chat_id].append({
            "role": "assistant",
            "content": llm_response
        })
        
        logger.info(f"Conversation history size for chat_id {chat_id}: {len(conversation_history[chat_id])} messages")
        
        # Send LLM response to user
        await message.answer(llm_response)
        
    except Exception as e:
        # Remove user message from history on error
        if conversation_history[chat_id] and conversation_history[chat_id][-1]["role"] == "user":
            conversation_history[chat_id].pop()
        
        logger.error(
            f"Error getting LLM response for @{username} (chat_id: {chat_id}): {e}",
            exc_info=True
        )
        
        # Send user-friendly error message
        error_message = (
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Попробуйте чуть позже."
        )
        await message.answer(error_message)


@router.message()
async def handle_non_text(message: Message) -> None:
    """
    Handle non-text content (photos, files, stickers, etc.).
    
    Args:
        message: Incoming non-text message from user
    """
    user = message.from_user
    username = user.username or "unknown"
    
    logger.warning(f"Received non-text content from @{username} (ID: {user.id})")
    
    error_message = (
        "Контент не распознан. "
        "Пожалуйста, напишите текстовое сообщение."
    )
    
    await message.answer(error_message)

