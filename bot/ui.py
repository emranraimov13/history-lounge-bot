from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message


async def replace_text(
    message: Message | None,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Редактирует сообщение, а если нельзя (например, это фото) — присылает новое."""
    if message is None:
        return
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as error:
        if "message is not modified" in str(error):
            return
        await message.answer(text, reply_markup=markup)
