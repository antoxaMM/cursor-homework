"""
Message and command handlers for the Telegram bot.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import logging

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
async def echo_text(message: Message) -> None:
    """
    Echo back text messages from user.
    
    Args:
        message: Incoming text message from user
    """
    user = message.from_user
    username = user.username or "unknown"
    
    logger.info(f"Received text from @{username} (ID: {user.id}): {message.text}")
    
    # Echo the message back
    await message.answer(message.text)


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

