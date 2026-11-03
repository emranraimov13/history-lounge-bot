from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InputProfilePhotoStatic,
    Message,
)
from PIL import Image, UnidentifiedImageError

from .. import config, db, keyboards, texts
from ..ui import replace_text

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(F.chat.type == ChatType.PRIVATE)

PAGE_SIZE = 5


class AdminForm(StatesGroup):
    waiting_photo = State()


async def _allowed_callback(callback: CallbackQuery) -> bool:
    if config.is_admin(callback.from_user.id):
        return True
    await callback.answer("У вас нет доступа", show_alert=True)
    return False


async def _reviews_payload(offset: int) -> tuple[str, InlineKeyboardMarkup]:
    total = await db.count_reviews()
    if total and offset >= total:
        offset = ((total - 1) // PAGE_SIZE) * PAGE_SIZE

    reviews = await db.get_reviews(limit=PAGE_SIZE, offset=offset)
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(pages, offset // PAGE_SIZE + 1)
    return (
        texts.admin_reviews_text(reviews, page, pages, total),
        keyboards.admin_reviews_nav(offset, PAGE_SIZE, total),
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not config.is_admin(user_id):
        await message.answer(texts.admin_need_access(user_id))
        return
    await state.clear()
    stats = await db.get_stats()
    await message.answer(
        texts.admin_panel_text(stats),
        reply_markup=keyboards.admin_panel(),
    )


@router.message(Command("reviews"))
async def cmd_reviews(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not config.is_admin(user_id):
        await message.answer(texts.admin_need_access(user_id))
        return
    await state.clear()
    text, markup = await _reviews_payload(0)
    await message.answer(text, reply_markup=markup)


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not config.is_admin(user_id):
        await message.answer(texts.admin_need_access(user_id))
        return
    await state.clear()
    stats = await db.get_stats()
    await message.answer(
        texts.admin_stats_text(stats),
        reply_markup=keyboards.admin_back(),
    )


@router.callback_query(F.data == "adm:panel")
async def cb_panel(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _allowed_callback(callback):
        return
    await state.clear()
    stats = await db.get_stats()
    await callback.answer()
    await replace_text(
        callback.message,
        texts.admin_panel_text(stats),
        keyboards.admin_panel(),
    )


@router.callback_query(F.data == "adm:noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "adm:stats")
async def cb_stats(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _allowed_callback(callback):
        return
    await state.clear()
    stats = await db.get_stats()
    await callback.answer()
    await replace_text(
        callback.message,
        texts.admin_stats_text(stats),
        keyboards.admin_back(),
    )


@router.callback_query(F.data.startswith("adm:list:"))
async def cb_list(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _allowed_callback(callback):
        return
    await state.clear()

    try:
        offset = max(0, int((callback.data or "").rsplit(":", 1)[1]))
    except (ValueError, IndexError):
        offset = 0

    text, markup = await _reviews_payload(offset)
    await callback.answer()
    await replace_text(callback.message, text, markup)


@router.callback_query(F.data == "adm:csv")
async def cb_export(callback: CallbackQuery) -> None:
    if not await _allowed_callback(callback):
        return
    await callback.answer("Готовлю файл…")
    data = await db.export_csv()
    filename = f"history_lounge_reviews_{datetime.now():%Y-%m-%d}.csv"
    if callback.message:
        await callback.message.answer_document(
            BufferedInputFile(data, filename=filename),
            caption=f"📥 Все отзывы · {datetime.now():%d.%m.%Y}",
        )


@router.callback_query(F.data == "adm:setphoto")
async def cb_set_photo(callback: CallbackQuery, state: FSMContext) -> None:
    if not await _allowed_callback(callback):
        return
    await state.set_state(AdminForm.waiting_photo)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            texts.admin_photo_prompt(),
            reply_markup=keyboards.admin_photo_kb(),
        )


@router.message(AdminForm.waiting_photo, F.photo | F.document)
async def save_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    if not config.is_admin(message.from_user.id if message.from_user else None):
        await state.clear()
        return

    if message.photo:
        file = message.photo[-1]
    else:
        document = message.document
        if document is None or not (document.mime_type or "").startswith("image/"):
            await message.answer(
                texts.not_admin_photo(),
                reply_markup=keyboards.admin_photo_kb(),
            )
            return
        file = document

    temp_path = config.DATA_DIR / "welcome_upload.tmp"
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        await bot.download(file, destination=str(temp_path))
        with Image.open(temp_path) as image:
            image = image.convert("RGB")
            image.thumbnail((1600, 1600))
            image.save(config.WELCOME_IMAGE, "JPEG", quality=90, optimize=True)
    except (UnidentifiedImageError, OSError):
        await message.answer(
            "Не получилось прочитать изображение. Попробуйте отправить другое фото."
        )
        return
    except Exception:
        logger.exception("Не удалось сохранить приветственную картинку")
        await message.answer(
            "Не удалось сохранить картинку. Попробуйте ещё раз или отправьте файл поменьше."
        )
        return
    finally:
        temp_path.unlink(missing_ok=True)

    await db.delete_setting("welcome_file_id")

    try:
        await bot.set_my_profile_photo(
            photo=InputProfilePhotoStatic(
                photo=FSInputFile(config.WELCOME_IMAGE)
            )
        )
    except TelegramAPIError as error:
        logger.warning("Не удалось обновить аватар бота: %s", error)

    await state.clear()

    await message.answer_photo(
        FSInputFile(config.WELCOME_IMAGE),
        caption=texts.admin_photo_saved(),
        reply_markup=keyboards.admin_panel(),
    )


@router.message(AdminForm.waiting_photo)
async def wrong_photo(message: Message) -> None:
    await message.answer(
        texts.not_admin_photo(),
        reply_markup=keyboards.admin_photo_kb(),
    )
