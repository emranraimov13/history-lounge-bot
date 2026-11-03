from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.types import Message

from .. import keyboards

router = Router(name="fallback")
router.message.filter(F.chat.type == ChatType.PRIVATE, StateFilter(None))


@router.message()
async def unknown_message(message: Message) -> None:
    await message.answer(
        "Не совсем понял 🙂\n\n"
        "Отправьте /start — покажу меню и помогу оставить отзыв.",
        reply_markup=keyboards.main_menu(message.from_user.id),
    )
