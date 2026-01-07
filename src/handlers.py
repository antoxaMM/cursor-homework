"""
Message and command handlers for the Telegram bot.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import logging
import os

from src.llm import get_llm_response

# Create router for handlers
router = Router()

# Logger
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Handle /start command with a greeting message.
    
    Args:
        message: Incoming message from user
    """
    user = message.from_user
    username = user.username or user.first_name or "пользователь"
    
    logger.info(f"User @{username} (ID: {user.id}) started the bot")
    
    greeting = (
        f"Здравствуйте, {username}! 👋\n\n"
        "Я бот-ассистент для консультаций. "
        "Напишите мне текстовое сообщение, и я отвечу вам."
    )
    
    await message.answer(greeting)


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """
    Process text message with LLM and send response.
    
    Args:
        message: Incoming text message from user
    """
    user = message.from_user
    username = user.username or "unknown"
    
    logger.info(f"Received text from @{username} (ID: {user.id}): {message.text}")
    
    # Get system prompt from environment
    system_prompt = os.getenv("SYSTEM_PROMPT", "Вы - полезный ИИ-ассистент.")
    
    try:
        # Get response from LLM
        llm_response = get_llm_response(message.text, system_prompt)
        
        # Send LLM response to user
        await message.answer(llm_response)
        
    except Exception as e:
        logger.error(f"Error getting LLM response: {e}", exc_info=True)
        
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

