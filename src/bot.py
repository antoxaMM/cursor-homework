"""
Entry point for the Telegram bot.
Initializes the bot, registers handlers, and starts polling.
"""

import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from src.handlers import router


def setup_logging() -> None:
    """
    Configure logging to stdout with format and level from environment.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


async def main() -> None:
    """
    Initialize and start the bot with polling.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get bot token from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
        sys.exit(1)
    
    # Initialize Bot and Dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Register handlers
    dp.include_router(router)
    
    logger.info("Bot started successfully")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")

