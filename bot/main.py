from __future__ import annotations

import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)

from . import config, db
from .handlers import admin, fallback, review, user

logger = logging.getLogger(__name__)

DEFAULT_COMMANDS = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="review", description="Оставить отзыв"),
    BotCommand(command="about", description="О ресторане"),
    BotCommand(command="site", description="Сайт, меню и бонусы"),
    BotCommand(command="myid", description="Мой Telegram ID"),
    BotCommand(command="help", description="Помощь"),
]

ADMIN_COMMANDS = [
    *DEFAULT_COMMANDS,
    BotCommand(command="admin", description="Админ-панель"),
    BotCommand(command="reviews", description="Все отзывы"),
    BotCommand(command="stats", description="Статистика"),
]

DESCRIPTION = (
    "🍂 History Lounge — ресторан, лаунж и бар.\n\n"
    "Оставьте отзыв о визите: оцените кухню, сервис и атмосферу. "
    "Мы читаем каждое сообщение и используем его, чтобы становиться лучше.\n\n"
    "🌐 Меню, акции и бонусы — на historylounge.app.\n\n"
    "Нажмите «Запустить», чтобы начать."
)
SHORT_DESCRIPTION = (
    "Отзывы гостей History Lounge. Меню, акции и бонусы — на historylounge.app."
)


def setup_logging() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        "%d.%m.%Y %H:%M:%S",
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        config.DATA_DIR / "bot.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[console, file_handler])
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


async def setup_bot(bot: Bot) -> None:
    """Имя, описание бота и команды — то, что видно до нажатия «Запустить»."""
    try:
        if config.BOT_NAME:
            await bot.set_my_name(config.BOT_NAME)
        await bot.set_my_description(DESCRIPTION)
        await bot.set_my_short_description(SHORT_DESCRIPTION)
        await bot.set_my_commands(DEFAULT_COMMANDS, scope=BotCommandScopeDefault())
    except TelegramAPIError as error:
        logger.warning("Не удалось обновить описание бота: %s", error)

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                ADMIN_COMMANDS,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except TelegramAPIError as error:
            logger.warning(
                "Не удалось обновить команды для админа %s: %s", admin_id, error
            )


async def main() -> None:
    setup_logging()
    if not config.BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN не задан. Откройте .env и вставьте токен от @BotFather."
        )

    await db.init_db()

    bot = Bot(
        config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(user.router)
    dispatcher.include_router(admin.router)
    dispatcher.include_router(review.router)
    dispatcher.include_router(fallback.router)

    await setup_bot(bot)
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        me = await bot.get_me()
        logger.info("Бот @%s запущен", me.username)
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as error:
        if isinstance(error, SystemExit) and error.code:
            logger.error("Остановлено: %s", error)
