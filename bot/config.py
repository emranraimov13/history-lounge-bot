"""Настройки бота. Секреты берутся из .env, тексты ресторана — ниже."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _parse_ids(raw: str) -> set[int]:
    """Принимает "123, 456;789" и возвращает набор чисел."""
    ids: set[int] = set()
    for part in raw.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = _parse_ids(os.getenv("ADMIN_IDS", ""))

# Имя бота в Telegram (не username). Устанавливается при каждом запуске.
BOT_NAME = os.getenv("BOT_NAME", "History отзывы").strip()

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "reviews.db"
ASSETS_DIR = BASE_DIR / "assets"
WELCOME_IMAGE = ASSETS_DIR / "welcome.jpg"

# ---------------------------------------------------------------------------
# Информация о ресторане.
# Заполните нужные поля — бот покажет только то, что указано.
# Пустые строки просто не попадут в сообщение.
# ---------------------------------------------------------------------------
RESTAURANT = {
    "name": "History Lounge",
    "tagline": "ресторан · лаунж-бар",
    "address": "г. Ташкент, Мирабадский район, ул. Шахрисабз, 23",
    "hours": "ежедневно с 12:00 до 01:00",
    "phone": "+998 77 131-11-11",
    "instagram": "https://www.instagram.com/history.lounge/",
    "map_url": "https://yandex.uz/maps/-/CDVgiMZa",
    "site_url": "",
}


def is_admin(user_id: int | None) -> bool:
    return bool(user_id) and user_id in ADMIN_IDS
