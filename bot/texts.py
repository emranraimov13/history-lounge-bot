"""Все тексты бота собраны здесь — их легко править без программиста."""

from __future__ import annotations

from . import config
from .utils import display_guest, esc, plural, short, stars

RESTAURANT = config.RESTAURANT


# ---------------------------------------------------------------------------
# Пользовательская часть
# ---------------------------------------------------------------------------
def welcome_text() -> str:
    return (
        f"🍂 <b>Добро пожаловать в {esc(RESTAURANT['name'])}</b>\n\n"
        "Это официальный бот нашего ресторана. Здесь вы можете оставить отзыв "
        "о визите — мы читаем каждый и используем, чтобы стать лучше.\n\n"
        "⭐ Оцените визит по пятибалльной шкале\n"
        "✍️ Расскажите, что понравилось, а что стоит улучшить\n"
        "💬 Это займёт меньше минуты\n\n"
        "Выберите действие 👇"
    )


def menu_text() -> str:
    return "🍂 <b>Главное меню</b>\n\nЧто хотите сделать?"


def about_text() -> str:
    lines = [
        f"<b>{esc(RESTAURANT['name'])}</b>",
        esc(RESTAURANT.get("tagline", "")),
        "<i>✨ Make history with us</i>",
        "",
    ]
    details = []
    if RESTAURANT.get("hours"):
        details.append(f"🕐 <b>Часы работы:</b> {esc(RESTAURANT['hours'])}")
    if RESTAURANT.get("address"):
        details.append(f"📍 <b>Адрес:</b> {esc(RESTAURANT['address'])}")
    if RESTAURANT.get("phone"):
        details.append(f"📞 <b>Телефон:</b> {esc(RESTAURANT['phone'])}")
    if details:
        lines.extend(details)
    else:
        lines.append(
            "Часы работы и адрес скоро появятся здесь. "
            "А пока — будем рады вашему отзыву."
        )
    lines.extend(
        [
            "",
            "<b>Нам важно ваше мнение</b>",
            "Оценка и комментарий помогают нам улучшать кухню, сервис и атмосферу. "
            "Спасибо, что уделили минуту 🍂",
        ]
    )
    return "\n".join(lines)


def rating_prompt() -> str:
    return (
        "<b>Как прошёл визит?</b>\n\n"
        "Поставьте оценку от 1 до 5 — это займёт пару секунд."
    )


def rating_done(rating: int) -> str:
    return (
        f"Ваша оценка: <b>{rating}/5</b> {stars(rating)}\n\n"
        "Теперь расскажите, что понравилось, а что можно улучшить.\n"
        "Можно отправить одно сообщение — или пропустить этот шаг."
    )


def text_prompt() -> str:
    return (
        "✍️ <b>Напишите отзыв</b>\n\n"
        "Расскажите о визите: кухня, сервис, атмосфера. "
        "Что порадовало, а что стоит исправить?\n\n"
        "<i>До 1200 символов. Это сообщение увидит только команда ресторана.</i>"
    )


def need_text() -> str:
    return "Пожалуйста, отправьте отзыв обычным текстом (до 1200 символов)."


def text_too_long() -> str:
    return "Отзыв получился слишком длинным. Сократите, пожалуйста, до 1200 символов."


def there_is_command() -> str:
    return (
        "Сейчас бот ждёт текст отзыва. Чтобы выйти, отправьте /cancel "
        "или нажмите кнопку «Отмена»."
    )


def name_prompt() -> str:
    return (
        "👤 <b>Подпишете отзыв?</b>\n\n"
        "Напишите имя — или пропустите этот шаг, и отзыв будет анонимным."
    )


def name_too_long() -> str:
    return "Имя слишком длинное — до 64 символов. Попробуйте ещё раз."


def summary_text(data: dict) -> str:
    rating = int(data.get("rating") or 0)
    name = (data.get("guest_name") or "").strip()
    text = (data.get("text") or "").strip()
    lines = [
        "<b>Проверьте отзыв</b>",
        "",
        f"⭐ Оценка: <b>{rating}/5</b> {stars(rating)}",
        f"👤 Имя: <b>{esc(name)}</b>" if name else "👤 Имя: <i>не указано</i>",
        "",
        f"💬 {esc(text)}" if text else "💬 <i>Без текста — только оценка</i>",
        "",
        "Отправить?",
    ]
    return "\n".join(lines)


def thanks_text(guest_name: str | None = None) -> str:
    name = (guest_name or "").strip()
    greeting = f"Спасибо, {esc(name)}!" if name else "Спасибо!"
    return (
        f"🙏 <b>{greeting}</b>\n\n"
        "Ваш отзыв отправлен. Мы обязательно его прочитаем "
        "и постараемся удивить вас в следующий раз.\n\n"
        f"Ждём вас снова в {esc(RESTAURANT['name'])} 🍂"
    )


def cancelled_text() -> str:
    return (
        "Хорошо, отменили.\n\n"
        "Если захотите оставить отзыв — это можно сделать в любой момент."
    )


def my_reviews_text(reviews: list[dict]) -> str:
    if not reviews:
        return (
            "<b>Ваши отзывы</b>\n\n"
            "Вы пока не оставляли отзывов — здесь появятся все ваши оценки "
            "и комментарии.\n\n"
            "Нажмите «Оставить отзыв», чтобы рассказать о визите."
        )
    average = sum(int(review["rating"]) for review in reviews) / len(reviews)
    blocks = [
        "<b>Ваши отзывы</b>",
        f"Средняя оценка: <b>{average:.1f} / 5</b> · показаны последние {len(reviews)}",
    ]
    for review in reviews:
        block = [
            "",
            f"<b>#{review['id']}</b> · {esc(_fmt(review['created_at']))}",
            f"{stars(int(review['rating']))} <b>{review['rating']}/5</b>",
        ]
        if review.get("text"):
            block.append(esc(short(review["text"], 500)))
        blocks.append("\n".join(block))
    return "\n".join(blocks)


def _fmt(iso: str | None) -> str:
    from .utils import fmt_dt

    return fmt_dt(iso)


# ---------------------------------------------------------------------------
# Админ-часть
# ---------------------------------------------------------------------------
def admin_new_review(review: dict) -> str:
    guest = display_guest(review)
    username = f"@{review['username']}" if review.get("username") else "—"
    lines = [
        f"🆕 <b>Новый отзыв</b> <i>#{review['id']}</i>",
        "",
        f"⭐ Оценка: <b>{review['rating']}/5</b> {stars(int(review['rating']))}",
        f"👤 Гость: <b>{esc(guest)}</b>",
    ]
    if review.get("text"):
        lines.extend(["", f"💬 {esc(review['text'])}"])
    else:
        lines.extend(["", "💬 <i>Без текста — только оценка</i>"])
    lines.extend(
        [
            "",
            f"🕐 {esc(_fmt(review['created_at']))}",
            f"🔗 {esc(username)} · ID <code>{review['user_id']}</code>",
        ]
    )
    return "\n".join(lines)


def admin_panel_text(stats: dict | None = None) -> str:
    text = (
        "🛠 <b>Админ-панель</b>\n\n"
        "Здесь можно посмотреть статистику и все отзывы гостей."
    )
    if stats is not None:
        if stats["total"]:
            text += (
                f"\n\n📝 Отзывов: <b>{stats['total']}</b>"
                f" · средняя оценка <b>{stats['avg']:.1f}/5</b>"
            )
        else:
            text += "\n\n📝 Отзывов пока нет."
    return text


def admin_stats_text(stats: dict) -> str:
    total = stats["total"]
    avg = stats["avg"]
    words = plural(total, "отзыв", "отзыва", "отзывов")
    if total:
        rating_words = {
            1: "очень плохо",
            2: "так себе",
            3: "нормально",
            4: "хорошо",
            5: "отлично",
        }
        mood = rating_words.get(round(avg), "")
    else:
        mood = "пока нет оценок"

    lines = [
        "<b>📊 Статистика</b>",
        "",
        f"Всего: <b>{total}</b> {words}",
        f"Средняя оценка: <b>{avg:.1f} / 5</b>" + (f" — {mood}" if total else ""),
        f"За последние 7 дней: <b>{stats['week']}</b>",
        f"Сегодня: <b>{stats['today']}</b>",
        "",
        "<b>Распределение оценок</b>",
    ]
    for rating in range(5, 0, -1):
        count = stats["by_rating"].get(rating, 0)
        lines.append(f"{stars(rating)} — <b>{count}</b>")
    return "\n".join(lines)


def admin_reviews_text(reviews: list[dict], page: int, pages: int, total: int) -> str:
    if not reviews:
        return (
            "<b>📝 Отзывы</b>\n\n"
            "Пока ни одного отзыва.\n\n"
            "Как только гости оценят визит, отзывы появятся здесь автоматически."
        )
    blocks = [f"<b>📝 Отзывы</b> · стр. {page} из {pages} · всего {total}"]
    for review in reviews:
        guest = display_guest(review)
        username = f"@{review['username']}" if review.get("username") else ""
        header = f"<b>#{review['id']}</b> · {esc(_fmt(review['created_at']))} · {stars(int(review['rating']))} <b>{review['rating']}/5</b>"
        author = f"👤 {esc(guest)}"
        if username:
            author += f" ({esc(username)})"
        block = ["", "──────────────────", header, author]
        block.append(esc(short(review.get("text"), 350)) if review.get("text") else "<i>Без текста</i>")
        blocks.append("\n".join(block))
    return "\n".join(blocks)


def admin_need_access(user_id: int) -> str:
    return (
        "🛠 <b>Админ-панель</b>\n\n"
        "У вас нет доступа.\n\n"
        f"Ваш Telegram ID: <code>{user_id}</code>\n\n"
        "Добавьте его в файл <code>.env</code> в строку <code>ADMIN_IDS</code> "
        "и перезапустите бота."
    )


def admin_photo_prompt() -> str:
    return (
        "🖼 <b>Новая приветственная картинка</b>\n\n"
        "Отправьте фото (или файл-изображение). Оно будет показываться "
        "при входе в бота вместе с приветствием.\n\n"
        "Рекомендуемый размер: квадрат, от 800×800 px.\n"
        "Отмена — /cancel."
    )


def admin_photo_saved() -> str:
    return (
        "✅ Картинка обновлена!\n\n"
        "Она показывается при входе в бота и установлена на аватарку.\n\n"
        "Проверьте: отправьте /start."
    )


def not_admin_photo() -> str:
    return "Пожалуйста, отправьте именно фото или файл-изображение."
