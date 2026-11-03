from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import config


def main_menu(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Оставить отзыв", callback_data="m:review")
    builder.button(text="ℹ️ О ресторане", callback_data="m:about")
    builder.button(text="📝 Мои отзывы", callback_data="m:my")
    if config.RESTAURANT.get("map_url"):
        builder.button(text="📍 Мы на карте", url=config.RESTAURANT["map_url"])
    if config.RESTAURANT.get("instagram"):
        builder.button(text="📸 Instagram", url=config.RESTAURANT["instagram"])
    if config.RESTAURANT.get("site_url"):
        builder.button(text="🌐 Сайт", url=config.RESTAURANT["site_url"])
    if config.is_admin(user_id):
        builder.button(text="🛠 Админ-панель", callback_data="adm:panel")
    builder.adjust(1, 2, 1, 1, 1)
    return builder.as_markup()


def rating_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for rating in range(1, 6):
        builder.button(text=str(rating), callback_data=f"rev:rate:{rating}")
    builder.button(text="❌ Отмена", callback_data="rev:cancel")
    builder.adjust(5, 1)
    return builder.as_markup()


def skip_text_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="rev:skiptext")
    builder.button(text="❌ Отмена", callback_data="rev:cancel")
    builder.adjust(2)
    return builder.as_markup()


def skip_name_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⏭ Пропустить", callback_data="rev:skipname")
    builder.button(text="❌ Отмена", callback_data="rev:cancel")
    builder.adjust(2)
    return builder.as_markup()


def summary_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data="rev:send")
    builder.button(text="✏️ Изменить текст", callback_data="rev:edit")
    builder.button(text="❌ Отмена", callback_data="rev:cancel")
    builder.adjust(1, 2)
    return builder.as_markup()


def thanks_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🍂 В меню", callback_data="m:menu")
    builder.adjust(1)
    return builder.as_markup()


def back_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В меню", callback_data="m:menu")
    builder.adjust(1)
    return builder.as_markup()


def my_reviews_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Оставить отзыв", callback_data="m:review")
    builder.button(text="⬅️ В меню", callback_data="m:menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="adm:stats")
    builder.button(text="📝 Отзывы", callback_data="adm:list:0")
    builder.button(text="📥 Экспорт в CSV", callback_data="adm:csv")
    builder.button(text="🖼 Заменить картинку", callback_data="adm:setphoto")
    builder.button(text="⬅️ В меню", callback_data="m:menu")
    builder.adjust(2, 1, 1, 1)
    return builder.as_markup()


def admin_back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛠 В панель", callback_data="adm:panel")
    builder.adjust(1)
    return builder.as_markup()


def admin_reviews_nav(offset: int, limit: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    pages = max(1, (total + limit - 1) // limit)
    page = min(pages, offset // limit + 1)

    if offset > 0:
        builder.button(
            text="⬅️ Новее",
            callback_data=f"adm:list:{max(0, offset - limit)}",
        )
    else:
        builder.button(text="⬅️ Новее", callback_data="adm:noop")

    builder.button(text=f"{page}/{pages}", callback_data="adm:noop")

    if offset + limit < total:
        builder.button(
            text="Старше ➡️",
            callback_data=f"adm:list:{offset + limit}",
        )
    else:
        builder.button(text="Старше ➡️", callback_data="adm:noop")

    builder.button(text="🛠 В панель", callback_data="adm:panel")
    builder.adjust(3, 1)
    return builder.as_markup()


def admin_photo_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ В панель", callback_data="adm:panel")
    builder.adjust(1)
    return builder.as_markup()
