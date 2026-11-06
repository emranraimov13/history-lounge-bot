from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from .. import config, db, keyboards, texts
from ..ui import replace_text
from .review import start_review

logger = logging.getLogger(__name__)

router = Router(name="user")
router.message.filter(F.chat.type == ChatType.PRIVATE)


async def show_welcome(message: Message, state: FSMContext) -> None:
    """Приветствие: картинка + подпись + меню."""
    await state.clear()
    user_id = message.from_user.id if message.from_user else 0
    markup = keyboards.main_menu(user_id)
    caption = texts.welcome_text()

    file_id = await db.get_setting("welcome_file_id")
    if file_id:
        try:
            await message.answer_photo(file_id, caption=caption, reply_markup=markup)
            return
        except TelegramBadRequest:
            await db.delete_setting("welcome_file_id")

    if config.WELCOME_IMAGE.exists():
        sent = await message.answer_photo(
            FSInputFile(config.WELCOME_IMAGE),
            caption=caption,
            reply_markup=markup,
        )
        if sent.photo:
            await db.set_setting("welcome_file_id", sent.photo[-1].file_id)
    else:
        await message.answer(caption, reply_markup=markup)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    if message.from_user:
        await db.upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    await show_welcome(message, state)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        texts.menu_text(),
        reply_markup=keyboards.main_menu(message.from_user.id),
    )


@router.message(Command("review"))
async def cmd_review(message: Message, state: FSMContext) -> None:
    await start_review(message, state)


@router.message(Command("about"))
async def cmd_about(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.about_text(), reply_markup=keyboards.about_kb())


@router.message(Command("site"))
async def cmd_site(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.site_text(), reply_markup=keyboards.site_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        texts.cancelled_text(),
        reply_markup=keyboards.main_menu(message.from_user.id),
    )


@router.message(Command("myid"))
async def cmd_myid(message: Message) -> None:
    if message.from_user:
        await message.answer(
            f"Ваш Telegram ID: <code>{message.from_user.id}</code>"
        )


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🍂 <b>Бот History Lounge</b>\n\n"
        "/review — оставить отзыв\n"
        "/about — о ресторане\n"
        "/site — сайт, меню и бонусы\n"
        "/menu — главное меню\n"
        "/cancel — отменить действие\n"
        "/myid — ваш Telegram ID\n\n"
        "Если что-то пошло не так — просто отправьте /start.",
        reply_markup=keyboards.main_menu(message.from_user.id),
    )


@router.callback_query(F.data == "m:menu")
async def cb_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await replace_text(
        callback.message,
        texts.menu_text(),
        keyboards.main_menu(callback.from_user.id),
    )


@router.callback_query(F.data == "m:about")
async def cb_about(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await replace_text(
        callback.message,
        texts.about_text(),
        keyboards.about_kb(),
    )


@router.callback_query(F.data == "m:my")
async def cb_my_reviews(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    reviews = await db.get_user_reviews(callback.from_user.id, limit=5)
    await replace_text(
        callback.message,
        texts.my_reviews_text(reviews),
        keyboards.my_reviews_kb(),
    )


@router.callback_query(F.data == "m:review")
async def cb_review(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await start_review(callback.message, state)


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def fallback_text(message: Message) -> None:
    await message.answer(
        "Не совсем понял 🙂\n\n"
        "Пользуйтесь кнопками ниже или отправьте /start, чтобы открыть меню.",
        reply_markup=keyboards.main_menu(message.from_user.id),
    )
