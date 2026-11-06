"""Фирменные QR-материалы History Lounge.

Запуск:  .venv/bin/python tools/make_qr.py

Результат:
  assets/qr_history_lounge.png     — квадратный QR для соцсетей и печати
  assets/qr_table_stand_a5.png     — тёмная карточка на стол, A5, 300 dpi
  assets/qr_table_stand_a5.pdf     — тёмная, A5 с вылетами 3 мм, 600 dpi
  assets/qr_table_stand_mockup.jpg — макет тёмного варианта на столе
  assets/qr_table_stand_a5_light.* — светлый вариант карточки и PDF
  assets/qr_table_stand_mockup_light.jpg — макет светлого варианта
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

URL = "https://t.me/loungeHistory_bot"

# Спокойная болотно-коричневая гамма.
INK = (43, 41, 32)
DARK = (57, 54, 42)
DARK_DEEP = (33, 32, 25)
OLIVE = (79, 75, 56)
CREAM = (244, 238, 225)
CREAM_SOFT = (233, 224, 207)
BRASS = (166, 132, 85)
BRASS_LIGHT = (198, 168, 120)
MUTED_ON_DARK = (190, 181, 162)
MUTED_ON_CREAM = (104, 98, 80)

# Светлый вариант: бумага, олива и латунь.
PAPER_TOP = (249, 244, 235)
PAPER_BOTTOM = (235, 225, 210)
LIGHT_INK = (55, 52, 40)
LIGHT_OLIVE = (82, 77, 57)
LIGHT_MUTED = (120, 112, 94)
LIGHT_PAPER = (247, 242, 232)
BAND_TOP = (63, 59, 45)
BAND_BOTTOM = (45, 42, 32)

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
SERIF_PATH = "/System/Library/Fonts/Supplemental/Didot.ttc"
FONT_REGULAR = 0
FONT_ULTRA = 5
FONT_LIGHT = 7
FONT_MEDIUM = 10
FONT_BOLD = 4

DPI = 300
SCALE = 2


def lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def mm(value: float) -> int:
    return int(round(value / 25.4 * DPI * SCALE))


def pt(value: float) -> int:
    return int(round(value / 72 * DPI * SCALE))


def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> Image.Image:
    strip = Image.new("RGB", (1, height))
    pixels = strip.load()
    for y in range(height):
        t = y / max(1, height - 1)
        pixels[0, y] = tuple(lerp(top[i], bottom[i], t) for i in range(3))
    return strip.resize((width, height), Image.Resampling.BICUBIC)


def radial_glow(size: int, color: tuple, strength: float) -> Image.Image:
    small = 360
    mask = Image.new("L", (small, small))
    pixels = mask.load()
    center = (small - 1) / 2
    for y in range(small):
        for x in range(small):
            distance = math.hypot(x - center, y - center) / (small / 2)
            pixels[x, y] = int(255 * max(0.0, 1.0 - distance) ** 1.7)
    mask = mask.resize((size, size), Image.Resampling.BICUBIC)
    layer = Image.new("RGBA", (size, size), (*color, 0))
    layer.putalpha(mask.point(lambda v: int(v * strength)))
    return layer


def make_background(width: int, height: int) -> Image.Image:
    background = vertical_gradient(width, height, (62, 59, 46), (29, 28, 22)).convert(
        "RGBA"
    )

    glow_size = int(max(width, height) * 0.95)
    glow = radial_glow(glow_size, BRASS, 0.12)
    background.alpha_composite(
        glow, ((width - glow.width) // 2, int(height * 0.36) - glow.height // 2)
    )

    rng = random.Random(11)
    specks = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(specks)
    for _ in range(260):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        radius = rng.randint(1, 3)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(*BRASS_LIGHT, rng.randint(5, 16)),
        )
    background.alpha_composite(specks.filter(ImageFilter.GaussianBlur(2)))

    noise = Image.effect_noise((width, height), 15).convert("L")
    grain = Image.merge(
        "RGBA", (noise, noise, noise, Image.new("L", (width, height), 6))
    )
    background.alpha_composite(grain)

    vignette = Image.new("L", (width, height), 0)
    vd = ImageDraw.Draw(vignette)
    steps = 70
    for i in range(steps):
        t = i / steps
        inset = int(t * min(width, height) * 0.32)
        alpha = int(60 * (t**2))
        vd.rounded_rectangle(
            (inset, inset, width - inset, height - inset),
            radius=int(min(width, height) * 0.03),
            outline=alpha,
            width=max(2, int(min(width, height) * 0.012)),
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(mm(4)))
    black = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    black.putalpha(vignette)
    background.alpha_composite(black)
    return background


def make_light_background(width: int, height: int) -> Image.Image:
    background = vertical_gradient(width, height, PAPER_TOP, PAPER_BOTTOM).convert(
        "RGBA"
    )

    glow_size = int(max(width, height) * 0.8)
    glow = radial_glow(glow_size, (208, 178, 128), 0.10)
    background.alpha_composite(
        glow, ((width - glow.width) // 2, int(height * 0.18) - glow.height // 2)
    )

    rng = random.Random(23)
    fibres = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fibres)
    for _ in range(190):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        length = rng.randint(3, 14)
        fd.line(
            (x, y, x + length, y + rng.randint(-1, 1)),
            fill=(*LIGHT_OLIVE, rng.randint(3, 9)),
            width=1,
        )
    background.alpha_composite(fibres.filter(ImageFilter.GaussianBlur(0.8)))

    noise = Image.effect_noise((width, height), 12).convert("L")
    grain = Image.merge(
        "RGBA", (noise, noise, noise, Image.new("L", (width, height), 5))
    )
    background.alpha_composite(grain)
    return background


def draw_tracking(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
    fill: tuple,
    center_x: float,
    y: float,
) -> None:
    widths = [draw.textlength(char, font=font) for char in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = center_x - total / 2
    for char, width in zip(text, widths):
        draw.text((x, y), char, font=font, fill=fill, anchor="lm")
        x += width + tracking


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    center_x: float,
    y: float,
) -> None:
    draw.text((center_x, y), text, font=font, fill=fill, anchor="mm")


def draw_qr(
    canvas: Image.Image,
    box: tuple[float, float, float, float],
    *,
    ink: tuple = INK,
    paper: tuple = CREAM,
    logo: str | None = "H",
    logo_ratio: float = 0.135,
) -> None:
    """Рисует QR с тихой зоной и аккуратными скруглёнными модулями."""
    qr = segno.make(URL, error="h")
    matrix = qr.matrix
    n = len(matrix)

    x1, y1, x2, y2 = box
    x, y = x1, y1
    size = min(x2 - x1, y2 - y1)
    total = n + 8  # quiet zone 4 модуля с каждой стороны
    module = size / total
    ox = x + 4 * module
    oy = y + 4 * module

    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    def in_finder(row: int, col: int) -> bool:
        return (
            (row < 7 and col < 7)
            or (row < 7 and col >= n - 7)
            or (row >= n - 7 and col < 7)
        )

    radius = 0.30 * module
    for row in range(n):
        for col in range(n):
            if not matrix[row][col] or in_finder(row, col):
                continue
            x0 = ox + col * module
            y0 = oy + row * module
            draw.rounded_rectangle(
                (x0, y0, x0 + module, y0 + module),
                radius=radius,
                fill=(*ink, 255),
            )

    def eye(col: int, row: int) -> None:
        x0 = ox + col * module
        y0 = oy + row * module
        draw.rounded_rectangle(
            (x0, y0, x0 + 7 * module, y0 + 7 * module),
            radius=1.45 * module,
            fill=(*ink, 255),
        )
        draw.rounded_rectangle(
            (x0 + module, y0 + module, x0 + 6 * module, y0 + 6 * module),
            radius=1.05 * module,
            fill=(*paper, 255),
        )
        draw.rounded_rectangle(
            (x0 + 2 * module, y0 + 2 * module, x0 + 5 * module, y0 + 5 * module),
            radius=0.65 * module,
            fill=(*ink, 255),
        )

    eye(0, 0)
    eye(n - 7, 0)
    eye(0, n - 7)

    if logo:
        cx = x + size / 2
        cy = y + size / 2
        r = size * logo_ratio / 2
        draw.ellipse(
            (cx - r - mm(0.65), cy - r - mm(0.65), cx + r + mm(0.65), cy + r + mm(0.65)),
            fill=(*BRASS, 255),
        )
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*paper, 255))
        font = ImageFont.truetype(SERIF_PATH, int(r * 1.22), index=0)
        draw.text(
            (cx, cy + r * 0.02),
            logo,
            font=font,
            fill=(*ink, 255),
            anchor="mm",
        )

    canvas.alpha_composite(layer)


def add_frame(
    canvas: Image.Image,
    inset_mm: float,
    width_mm: float,
    alpha: int,
    *,
    color: tuple = BRASS,
) -> None:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    inset = mm(inset_mm)
    draw.rounded_rectangle(
        (inset, inset, canvas.width - inset, canvas.height - inset),
        radius=mm(2.8),
        outline=(*color, alpha),
        width=max(1, mm(width_mm)),
    )
    canvas.alpha_composite(layer)


def add_ornament(
    canvas: Image.Image,
    center_x: float,
    y: float,
    half_width_mm: float,
    *,
    alpha: int = 170,
    color: tuple = BRASS,
) -> None:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    gap = mm(2.6)
    half = mm(half_width_mm)
    line_width = max(1, mm(0.25))
    draw.line(
        (center_x - half, y, center_x - gap, y),
        fill=(*color, alpha),
        width=line_width,
    )
    draw.line(
        (center_x + gap, y, center_x + half, y),
        fill=(*color, alpha),
        width=line_width,
    )
    r = mm(1.15)
    draw.polygon(
        [
            (center_x, y - r),
            (center_x + r, y),
            (center_x, y + r),
            (center_x - r, y),
        ],
        fill=(*color, alpha),
    )
    canvas.alpha_composite(layer)


def draw_wordmark(
    canvas: Image.Image,
    center_x: float,
    top_y: float,
    *,
    history_pt: float = 53,
    lounge_pt: float = 14,
    history_color: tuple = CREAM,
    lounge_color: tuple = BRASS_LIGHT,
) -> float:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    font_history = ImageFont.truetype(FONT_PATH, pt(history_pt), index=FONT_ULTRA)
    font_lounge = ImageFont.truetype(FONT_PATH, pt(lounge_pt), index=FONT_LIGHT)

    draw.text(
        (center_x, top_y + pt(history_pt) * 0.52),
        "History",
        font=font_history,
        fill=(*history_color, 255),
        anchor="mm",
    )
    draw_tracking(
        draw,
        "lounge",
        font_lounge,
        pt(lounge_pt) * 0.52,
        (*lounge_color, 255),
        center_x,
        top_y + pt(history_pt) * 1.12,
    )

    canvas.alpha_composite(layer)
    return top_y + pt(history_pt) * 1.28


# ---------------------------------------------------------------------------
# Квадратный QR для соцсетей / универсальной печати
# ---------------------------------------------------------------------------


def make_square() -> Image.Image:
    size = 2400
    canvas = make_background(size, size)

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (235, 150, 2165, 2215),
        radius=86,
        fill=(0, 0, 0, 150),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(55))
    canvas.alpha_composite(shadow, (0, 14))

    card = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle(
        (235, 130, 2165, 2195),
        radius=86,
        fill=(*CREAM, 255),
        outline=(*BRASS, 255),
        width=5,
    )
    cd.rounded_rectangle(
        (255, 150, 2145, 2175),
        radius=72,
        outline=(*BRASS, 95),
        width=2,
    )
    canvas.alpha_composite(card)

    draw_qr(canvas, (450, 240, 1950, 1740))

    font_history = ImageFont.truetype(FONT_PATH, 140, index=FONT_ULTRA)
    font_lounge = ImageFont.truetype(FONT_PATH, 50, index=FONT_LIGHT)
    font_sub = ImageFont.truetype(FONT_PATH, 34, index=FONT_LIGHT)
    font_handle = ImageFont.truetype(FONT_PATH, 46, index=FONT_MEDIUM)

    text = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    td = ImageDraw.Draw(text)
    td.text((1200, 1845), "History", font=font_history, fill=(*INK, 255), anchor="mm")
    draw_tracking(
        td,
        "lounge",
        font_lounge,
        19,
        (*BRASS, 255),
        1200,
        1972,
    )
    td.line((1040, 2018, 1360, 2018), fill=(*BRASS, 150), width=2)
    td.text(
        (1200, 2058),
        "Сканируйте, чтобы оставить отзыв",
        font=font_sub,
        fill=(*MUTED_ON_CREAM, 255),
        anchor="mm",
    )
    td.text(
        (1200, 2112),
        "@loungeHistory_bot",
        font=font_handle,
        fill=(*INK, 255),
        anchor="mm",
    )
    canvas.alpha_composite(text)

    return canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Карточка на стол A5
# ---------------------------------------------------------------------------


def make_table_stand() -> tuple[Image.Image, Image.Image]:
    # 154×216 мм = A5 (148×210) + 3 мм вылета с каждой стороны.
    width = mm(154)
    height = mm(216)
    canvas = make_background(width, height)

    # Тонкая двойная рамка.
    add_frame(canvas, 11.5, 0.30, 115)
    add_frame(canvas, 12.5, 0.22, 65)

    wordmark_bottom = draw_wordmark(canvas, width / 2, mm(16.5))
    add_ornament(canvas, width / 2, wordmark_bottom + mm(4.2), 17.5)

    # Центральная кремовая карточка с QR.
    card_box = (mm(22), mm(53), mm(132), mm(161))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (
            card_box[0] + mm(0.5),
            card_box[1] + mm(1.2),
            card_box[2] + mm(0.8),
            card_box[3] + mm(1.6),
        ),
        radius=mm(4.2),
        fill=(0, 0, 0, 125),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(mm(2.8)))
    canvas.alpha_composite(shadow)

    card = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle(
        card_box,
        radius=mm(4.2),
        fill=(*CREAM, 255),
        outline=(*BRASS_LIGHT, 230),
        width=max(1, mm(0.28)),
    )
    cd.rounded_rectangle(
        (
            card_box[0] + mm(2.4),
            card_box[1] + mm(2.4),
            card_box[2] - mm(2.4),
            card_box[3] - mm(2.4),
        ),
        radius=mm(2.8),
        outline=(*BRASS, 90),
        width=max(1, mm(0.18)),
    )
    canvas.alpha_composite(card)

    qr_size = mm(94)
    qr_center_y = (card_box[1] + card_box[3]) / 2
    draw_qr(
        canvas,
        (
            width / 2 - qr_size / 2,
            qr_center_y - qr_size / 2,
            width / 2 + qr_size / 2,
            qr_center_y + qr_size / 2,
        ),
        logo="H",
        logo_ratio=0.14,
    )

    text = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    font_headline = ImageFont.truetype(FONT_PATH, pt(25), index=FONT_LIGHT)
    font_body = ImageFont.truetype(FONT_PATH, pt(10.5), index=FONT_LIGHT)
    font_handle = ImageFont.truetype(FONT_PATH, pt(11), index=FONT_MEDIUM)

    draw_centered(td, "Оставьте отзыв", font_headline, (*CREAM, 255), width / 2, mm(172))
    draw_centered(
        td,
        "Наведите камеру телефона на QR-код",
        font_body,
        (*MUTED_ON_DARK, 255),
        width / 2,
        mm(182),
    )

    line_half = mm(29)
    td.line(
        (width / 2 - line_half, mm(189), width / 2 + line_half, mm(189)),
        fill=(*BRASS, 120),
        width=max(1, mm(0.22)),
    )

    draw_tracking(
        td,
        "@loungeHistory_bot",
        font_handle,
        pt(11) * 0.06,
        (*BRASS_LIGHT, 255),
        width / 2,
        mm(196.5),
    )
    canvas.alpha_composite(text)

    # Превью без вылетов — для показа и макета.
    bleed = mm(3)
    preview = canvas.crop((bleed, bleed, width - bleed, height - bleed))
    return preview.convert("RGB"), canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Светлый вариант карточки A5
# ---------------------------------------------------------------------------


def make_table_stand_light() -> tuple[Image.Image, Image.Image]:
    width = mm(154)
    height = mm(216)
    canvas = make_light_background(width, height)

    # Тонкая оливковая рамка — легче, чем в тёмном варианте.
    add_frame(canvas, 10.5, 0.28, 85, color=LIGHT_OLIVE)
    add_frame(canvas, 11.4, 0.18, 40, color=LIGHT_OLIVE)

    wordmark_bottom = draw_wordmark(
        canvas,
        width / 2,
        mm(15.5),
        history_pt=46,
        lounge_pt=13,
        history_color=LIGHT_INK,
        lounge_color=BRASS,
    )
    add_ornament(
        canvas,
        width / 2,
        wordmark_bottom + mm(4.0),
        17.5,
        alpha=150,
        color=BRASS,
    )

    text = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(text)
    font_headline = ImageFont.truetype(FONT_PATH, pt(22), index=FONT_LIGHT)
    draw_centered(
        td,
        "Оставьте отзыв",
        font_headline,
        (*LIGHT_INK, 255),
        width / 2,
        mm(47.5),
    )
    canvas.alpha_composite(text)

    # Плоская кремовая панель: без тени и «карточки», только тонкая рамка.
    panel_box = (mm(25), mm(56.5), mm(129), mm(160.5))
    panel = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(
        panel_box,
        radius=mm(3.2),
        fill=(*LIGHT_PAPER, 255),
        outline=(*LIGHT_OLIVE, 125),
        width=max(1, mm(0.28)),
    )
    pd.rounded_rectangle(
        (
            panel_box[0] + mm(2.2),
            panel_box[1] + mm(2.2),
            panel_box[2] - mm(2.2),
            panel_box[3] - mm(2.2),
        ),
        radius=mm(2.2),
        outline=(*BRASS, 48),
        width=max(1, mm(0.15)),
    )
    canvas.alpha_composite(panel)

    qr_size = mm(94)
    qr_center_y = (panel_box[1] + panel_box[3]) / 2
    draw_qr(
        canvas,
        (
            width / 2 - qr_size / 2,
            qr_center_y - qr_size / 2,
            width / 2 + qr_size / 2,
            qr_center_y + qr_size / 2,
        ),
        ink=LIGHT_INK,
        paper=LIGHT_PAPER,
        logo="H",
        logo_ratio=0.14,
    )

    # Нижняя оливковая плашка с призывом.
    band_top = mm(174)
    band = vertical_gradient(width, height - band_top, BAND_TOP, BAND_BOTTOM).convert(
        "RGBA"
    )
    noise = Image.effect_noise((width, height - band_top), 14).convert("L")
    band.alpha_composite(
        Image.merge(
            "RGBA",
            (noise, noise, noise, Image.new("L", (width, height - band_top), 7)),
        )
    )
    canvas.alpha_composite(band, (0, band_top))

    line = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.line(
        (0, band_top, width, band_top),
        fill=(*BRASS, 190),
        width=max(1, mm(0.35)),
    )
    canvas.alpha_composite(line)

    text = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    font_eyebrow = ImageFont.truetype(FONT_PATH, pt(8), index=FONT_LIGHT)
    font_handle = ImageFont.truetype(FONT_PATH, pt(15), index=FONT_MEDIUM)
    font_footer = ImageFont.truetype(FONT_PATH, pt(7), index=FONT_LIGHT)

    draw_tracking(
        td,
        "СКАНИРУЙТЕ QR-КОД",
        font_eyebrow,
        pt(8) * 0.34,
        (*BRASS_LIGHT, 255),
        width / 2,
        mm(184),
    )
    draw_centered(
        td,
        "@loungeHistory_bot",
        font_handle,
        (*CREAM, 255),
        width / 2,
        mm(195),
    )
    draw_centered(
        td,
        "History Lounge · Ташкент",
        font_footer,
        (*MUTED_ON_DARK, 210),
        width / 2,
        mm(205),
    )
    canvas.alpha_composite(text)

    bleed = mm(3)
    preview = canvas.crop((bleed, bleed, width - bleed, height - bleed))
    return preview.convert("RGB"), canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Макет на столе
# ---------------------------------------------------------------------------


def find_coeffs(
    target: list[tuple[float, float]], source: list[tuple[float, float]]
) -> list[float]:
    """Коэффициенты перспективного преобразования target -> source."""
    matrix: list[list[float]] = []
    vector: list[float] = []
    for (tx, ty), (sx, sy) in zip(target, source):
        matrix.append([tx, ty, 1, 0, 0, 0, -sx * tx, -sx * ty])
        vector.append(sx)
        matrix.append([0, 0, 0, tx, ty, 1, -sy * tx, -sy * ty])
        vector.append(sy)

    n = 8
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(matrix[row][col]))
        if abs(matrix[pivot][col]) < 1e-9:
            raise ValueError("Не удалось построить перспективу")
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        vector[col], vector[pivot] = vector[pivot], vector[col]
        divisor = matrix[col][col]
        for j in range(col, n):
            matrix[col][j] /= divisor
        vector[col] /= divisor
        for row in range(n):
            if row == col:
                continue
            factor = matrix[row][col]
            if abs(factor) < 1e-12:
                continue
            for j in range(col, n):
                matrix[row][j] -= factor * matrix[col][j]
            vector[row] -= factor * vector[col]
    return vector


def perspective_paste(
    canvas: Image.Image,
    image: Image.Image,
    quad: list[tuple[float, float]],
) -> None:
    source = [
        (0, 0),
        (image.width, 0),
        (image.width, image.height),
        (0, image.height),
    ]
    coeffs = find_coeffs(quad, source)
    layer = image.transform(
        canvas.size,
        Image.Transform.PERSPECTIVE,
        coeffs,
        resample=Image.Resampling.BICUBIC,
    )
    canvas.alpha_composite(layer)


def make_mockup(card: Image.Image) -> Image.Image:
    width, height = 1800, 1350
    canvas = vertical_gradient(width, height, (39, 35, 26), (13, 12, 9)).convert("RGBA")

    # Тёплые блики ресторанного света.
    rng = random.Random(21)
    bokeh = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bokeh)
    for _ in range(38):
        x = rng.randint(-80, width + 80)
        y = rng.randint(-40, int(height * 0.7))
        r = rng.randint(18, 120)
        color = rng.choice([(196, 151, 91), (151, 132, 87), (218, 181, 119)])
        bd.ellipse((x - r, y - r, x + r, y + r), fill=(*color, rng.randint(8, 26)))
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(34))
    canvas.alpha_composite(bokeh)

    # Деревянная поверхность стола.
    table_top = int(height * 0.31)
    table = vertical_gradient(width, height - table_top, (45, 35, 25), (24, 19, 14))
    table = table.convert("RGBA")
    grain = Image.new("RGBA", (width, height - table_top), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    for _ in range(90):
        y = rng.randint(0, table.height)
        amplitude = rng.uniform(2, 9)
        phase = rng.uniform(0, math.tau)
        points = []
        for x in range(0, width + 20, 20):
            points.append(
                (x, y + math.sin(x / rng.uniform(180, 460) + phase) * amplitude)
            )
        gd.line(
            points,
            fill=(*rng.choice([(96, 76, 52), (20, 16, 12), (128, 102, 68)]), rng.randint(6, 26)),
            width=rng.randint(1, 3),
        )
    grain = grain.filter(ImageFilter.GaussianBlur(1.2))
    table.alpha_composite(grain)
    canvas.alpha_composite(table, (0, table_top))

    # Мягкая тень на столе.
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((470, 1010, 1430, 1235), fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(55))
    canvas.alpha_composite(shadow)

    # Карточка стоит с лёгким наклоном.
    quad = [
        (700.0, 300.0),
        (1200.0, 330.0),
        (1270.0, 1080.0),
        (620.0, 1040.0),
    ]

    # Толщина карточки.
    thickness = [(x + 10, y + 8) for x, y in quad]
    edge = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    ed.polygon(thickness, fill=(19, 18, 13, 235))
    ed.polygon(quad, fill=(19, 18, 13, 255))
    edge = edge.filter(ImageFilter.GaussianBlur(1.2))
    canvas.alpha_composite(edge)

    # Отражение на полированной поверхности.
    reflection = card.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert("RGBA")
    reflection.putalpha(26)
    reflection = reflection.filter(ImageFilter.GaussianBlur(12))
    reflection_quad = [
        (620.0, 1040.0),
        (1270.0, 1080.0),
        (1235.0, 1198.0),
        (665.0, 1162.0),
    ]
    perspective_paste(canvas, reflection, reflection_quad)

    # Сама карточка.
    perspective_paste(canvas, card.convert("RGBA"), quad)

    # Тонкий блик по верхней кромке.
    highlight = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.line([quad[0], quad[1]], fill=(238, 225, 200, 90), width=2)
    highlight = highlight.filter(ImageFilter.GaussianBlur(1.4))
    canvas.alpha_composite(highlight)

    # Лёгкая виньетка.
    vignette = Image.new("L", (width, height), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(60):
        t = i / 60
        inset = int(t * 500)
        vd.rectangle(
            (inset, inset, width - inset, height - inset),
            outline=int(80 * t**2),
            width=26,
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(70))
    black = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    black.putalpha(vignette)
    canvas.alpha_composite(black)

    return canvas.convert("RGB")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    square = make_square()
    square_path = ASSETS / "qr_history_lounge.png"
    square.save(square_path, "PNG", optimize=True)

    preview, print_version = make_table_stand()
    preview_path = ASSETS / "qr_table_stand_a5.png"
    preview.resize(
        (round(148 / 25.4 * DPI), round(210 / 25.4 * DPI)),
        Image.Resampling.LANCZOS,
    ).save(preview_path, "PNG", optimize=True)

    pdf_path = ASSETS / "qr_table_stand_a5.pdf"
    print_version.save(pdf_path, "PDF", resolution=DPI * SCALE)

    mockup = make_mockup(preview)
    mockup_path = ASSETS / "qr_table_stand_mockup.jpg"
    mockup.save(mockup_path, "JPEG", quality=93, optimize=True)

    light_preview, light_print = make_table_stand_light()
    light_preview_path = ASSETS / "qr_table_stand_a5_light.png"
    light_preview.resize(
        (round(148 / 25.4 * DPI), round(210 / 25.4 * DPI)),
        Image.Resampling.LANCZOS,
    ).save(light_preview_path, "PNG", optimize=True)

    light_pdf_path = ASSETS / "qr_table_stand_a5_light.pdf"
    light_print.save(light_pdf_path, "PDF", resolution=DPI * SCALE)

    light_mockup = make_mockup(light_preview)
    light_mockup_path = ASSETS / "qr_table_stand_mockup_light.jpg"
    light_mockup.save(light_mockup_path, "JPEG", quality=93, optimize=True)

    for path in (
        square_path,
        preview_path,
        pdf_path,
        mockup_path,
        light_preview_path,
        light_pdf_path,
        light_mockup_path,
    ):
        print(f"Готово: {path} ({path.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
