from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from . import config, texts

logger = logging.getLogger(__name__)


async def notify_new_review(bot: Bot, review: dict) -> None:
    """Отправляет новый отзыв всем администраторам из ADMIN_IDS."""
    if not config.ADMIN_IDS:
        logger.warning(
            "Новый отзыв #%s, но ADMIN_IDS не настроен — уведомление не отправлено.",
            review.get("id"),
        )
        return

    text = texts.admin_new_review(review)
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError as error:
            logger.warning("Не удалось отправить отзыв админу %s: %s", admin_id, error)
