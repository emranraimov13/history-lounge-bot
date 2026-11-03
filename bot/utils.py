from __future__ import annotations

import html
from datetime import datetime


def esc(value: object) -> str:
    """Безопасная вставка пользовательского текста в HTML-сообщение."""
    return html.escape(str(value or ""), quote=False)


def fmt_dt(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d.%m.%Y %H:%M")
    except (TypeError, ValueError):
        return str(iso)


def stars(rating: int, total: int = 5) -> str:
    rating = max(0, min(total, int(rating)))
    return "⭐" * rating + "☆" * (total - rating)


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(int(n)) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def display_guest(review: dict) -> str:
    name = (review.get("guest_name") or "").strip()
    if name:
        return name
    full_name = (review.get("full_name") or "").strip()
    if full_name:
        return full_name
    return "Гость"


def short(text: str | None, limit: int = 300) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
