"""
Точка входа приложения.
"""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.utils.logger import logger
from bot.handlers import register_all_handlers
from bot.services.database import init_db, close_db


async def on_startup():
    """Действия при запуске бота."""
    logger.info("[START] Starting bot...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG_MODE}")
    logger.info(f"Personal Plan feature: {'ENABLED' if settings.is_personal_plan_enabled else 'DISABLED'}")

    # Инициализация БД (в production используйте Alembic)
    # await init_db()


async def on_shutdown():
    """Действия при остановке бота."""
    logger.info("[STOP] Shutting down bot...")
    await close_db()


async def main():
    """Основная функция запуска бота."""

    # Создать бота
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    # Создать диспетчер с MemoryStorage (для локальной разработки)
    # В production используйте Redis storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Зарегистрировать хендлеры
    register_all_handlers(dp)

    # Зарегистрировать startup/shutdown хуки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запустить polling
    try:
        logger.info("[OK] Bot started successfully!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("[PAUSE] Bot stopped by user")
    except Exception as e:
        logger.error(f"[ERROR] Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[BYE] Goodbye!")
