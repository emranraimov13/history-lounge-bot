from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from .. import db, keyboards, texts
from ..notify import notify_new_review
from ..ui import replace_text

logger = logging.getLogger(__name__)

router = Router(name="review")
router.message.filter(F.chat.type == ChatType.PRIVATE)

MAX_TEXT = 1200
MAX_NAME = 64


class ReviewForm(StatesGroup):
    rating = State()
    text = State()
    name = State()
    confirm = State()


async def start_review(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ReviewForm.rating)
    await message.answer(texts.rating_prompt(), reply_markup=keyboards.rating_kb())


@router.callback_query(ReviewForm.rating, F.data.startswith("rev:rate:"))
async def choose_rating(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        rating = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer()
        return
    if rating not in range(1, 6):
        await callback.answer("Некорректная оценка", show_alert=True)
        return

    await state.update_data(rating=rating)
    await state.set_state(ReviewForm.text)
    await callback.answer(f"Оценка: {rating}/5")
    await replace_text(
        callback.message,
        texts.rating_done(rating),
        keyboards.skip_text_kb(),
    )


@router.callback_query(ReviewForm.text, F.data == "rev:skiptext")
async def skip_text(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(text=None)
    await state.set_state(ReviewForm.name)
    await callback.answer("Пропущено")
    await replace_text(
        callback.message,
        texts.name_prompt(),
        keyboards.skip_name_kb(),
    )


@router.message(ReviewForm.text)
async def enter_text(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer(texts.need_text())
        return
    if raw.startswith("/"):
        await message.answer(texts.there_is_command())
        return
    if len(raw) > MAX_TEXT:
        await message.answer(texts.text_too_long())
        return

    await state.update_data(text=raw)
    await state.set_state(ReviewForm.name)
    await message.answer(texts.name_prompt(), reply_markup=keyboards.skip_name_kb())


@router.callback_query(ReviewForm.name, F.data == "rev:skipname")
async def skip_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(guest_name=None)
    await state.set_state(ReviewForm.confirm)
    data = await state.get_data()
    await callback.answer("Анонимно")
    await replace_text(
        callback.message,
        texts.summary_text(data),
        keyboards.summary_kb(),
    )


@router.message(ReviewForm.name)
async def enter_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, напишите имя текстом или нажмите «Пропустить».")
        return
    raw = message.text.strip()
    if raw.startswith("/"):
        await message.answer(texts.there_is_command())
        return
    if len(raw) > MAX_NAME:
        await message.answer(texts.name_too_long())
        return

    await state.update_data(guest_name=raw or None)
    await state.set_state(ReviewForm.confirm)
    data = await state.get_data()
    await message.answer(texts.summary_text(data), reply_markup=keyboards.summary_kb())


@router.callback_query(ReviewForm.confirm, F.data == "rev:edit")
async def edit_text(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(text=None)
    await state.set_state(ReviewForm.text)
    await callback.answer()
    await replace_text(
        callback.message,
        texts.text_prompt(),
        keyboards.skip_text_kb(),
    )


@router.callback_query(ReviewForm.confirm, F.data == "rev:send")
async def send_review(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    data = await state.get_data()
    rating = int(data.get("rating") or 0)
    if rating not in range(1, 6):
        await state.clear()
        await callback.answer("Сессия устарела — начнём заново", show_alert=True)
        if callback.message:
            await start_review(callback.message, state)
        return

    text = (data.get("text") or "").strip() or None
    guest_name = (data.get("guest_name") or "").strip() or None
    user = callback.from_user

    review_id = await db.add_review(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        guest_name=guest_name,
        rating=rating,
        text=text,
    )
    await state.clear()

    await replace_text(
        callback.message,
        texts.thanks_text(guest_name),
        keyboards.thanks_kb(),
    )
    await callback.answer("Отправлено ✅")

    review = {
        "id": review_id,
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "guest_name": guest_name,
        "rating": rating,
        "text": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    logger.info("Новый отзыв #%s: %s/5", review_id, rating)
    await notify_new_review(bot, review)


@router.callback_query(F.data == "rev:cancel")
async def cancel_review(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    await replace_text(
        callback.message,
        texts.cancelled_text(),
        keyboards.main_menu(callback.from_user.id),
    )


@router.callback_query(StateFilter(None), F.data.startswith("rev:"))
async def stale_review(callback: CallbackQuery) -> None:
    await callback.answer(
        "Эта кнопка уже неактуальна. Откройте меню командой /start.",
        show_alert=True,
    )
