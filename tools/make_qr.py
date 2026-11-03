"""Фирменный QR-код History Lounge.

Запуск:  .venv/bin/python tools/make_qr.py
Результат: assets/qr_history_lounge.png (2400×2400)
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "qr_history_lounge.png"

URL = "https://t.me/loungeHistory_bot"

DESIGN = 2000
SCALE = 2
S = DESIGN * SCALE
FINAL = 2400

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_ULTRA = 5
FONT_LIGHT = 7
FONT_MEDIUM = 10

INK = (24, 19, 14)
CREAM = (247, 241, 230)
GOLD = (201, 162, 39)
GOLD_DARK = (154, 116, 34)
MUTED = (122, 110, 96)
BG_TOP = (18, 15, 12)
BG_BOTTOM = (9, 8, 7)


def lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> Image.Image:
    strip = Image.new("RGB", (1, height))
    px = strip.load()
    for y in range(height):
        t = y / max(1, height - 1)
        px[0, y] = tuple(lerp(top[i], bottom[i], t) for i in range(3))
    return strip.resize((width, height), Image.Resampling.BICUBIC)


def radial_glow(size: int, color: tuple, strength: float) -> Image.Image:
    small = 300
    mask = Image.new("L", (small, small))
    px = mask.load()
    c = (small - 1) / 2
    for y in range(small):
        for x in range(small):
            d = math.hypot(x - c, y - c) / (small / 2)
            px[x, y] = int(255 * max(0.0, 1.0 - d) ** 1.8)
    mask = mask.resize((size, size), Image.Resampling.BICUBIC)
    layer = Image.new("RGBA", (size, size), (*color, 0))
    layer.putalpha(mask.point(lambda v: int(v * strength)))
    return layer


def make_background() -> Image.Image:
    bg = vertical_gradient(S, S, BG_TOP, BG_BOTTOM).convert("RGBA")
    glow = radial_glow(int(S * 0.9), (150, 112, 45), 0.20)
    bg.alpha_composite(glow, ((S - glow.width) // 2, (S - glow.height) // 2))

    rng = random.Random(5)
    specks = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(specks)
    for _ in range(220):
        x = rng.randint(0, S)
        y = rng.randint(0, S)
        r = rng.randint(1, 3)
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(214, 178, 96, rng.randint(6, 18)))
    bg.alpha_composite(specks.filter(ImageFilter.GaussianBlur(2)))

    noise = Image.effect_noise((S, S), 16).convert("L")
    grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (S, S), 7)))
    bg.alpha_composite(grain)

    border = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(border)
    inset = int(46 * SCALE)
    bd.rounded_rectangle(
        (inset, inset, S - inset, S - inset),
        radius=int(10 * SCALE),
        outline=(*GOLD, 150),
        width=max(1, int(1.6 * SCALE)),
    )
    bg.alpha_composite(border)
    return bg


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


def draw_qr(canvas: Image.Image, box: tuple[float, float, float, float]) -> None:
    qr = segno.make(URL, error="h")
    matrix = qr.matrix
    n = len(matrix)

    x, y, size, _ = box
    total = n + 8  # quiet zone 4 модуля с каждой стороны
    module = size / total
    ox = x + 4 * module
    oy = y + 4 * module

    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
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
                fill=(*INK, 255),
            )

    def eye(col: int, row: int) -> None:
        x0 = ox + col * module
        y0 = oy + row * module
        draw.rounded_rectangle(
            (x0, y0, x0 + 7 * module, y0 + 7 * module),
            radius=1.45 * module,
            fill=(*INK, 255),
        )
        draw.rounded_rectangle(
            (x0 + module, y0 + module, x0 + 6 * module, y0 + 6 * module),
            radius=1.05 * module,
            fill=(*CREAM, 255),
        )
        draw.rounded_rectangle(
            (x0 + 2 * module, y0 + 2 * module, x0 + 5 * module, y0 + 5 * module),
            radius=0.65 * module,
            fill=(*INK, 255),
        )

    eye(0, 0)
    eye(n - 7, 0)
    eye(0, n - 7)

    # Монограмма в центре: кремовый круг с золотым кольцом.
    cx = x + size / 2
    cy = y + size / 2
    r = 80 * SCALE
    draw.ellipse(
        (cx - r - 6 * SCALE, cy - r - 6 * SCALE, cx + r + 6 * SCALE, cy + r + 6 * SCALE),
        fill=(*GOLD, 255),
    )
    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill=(*CREAM, 255),
    )
    font_h = ImageFont.truetype(FONT_PATH, int(98 * SCALE), index=FONT_LIGHT)
    draw.text((cx, cy + 2 * SCALE), "H", font=font_h, fill=(*INK, 255), anchor="mm")

    canvas.alpha_composite(layer)


def main() -> None:
    canvas = make_background()

    # Тень карточки.
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (250 * SCALE, 150 * SCALE, 1750 * SCALE, 1880 * SCALE),
        radius=100 * SCALE,
        fill=(0, 0, 0, 170),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(60 * SCALE))
    canvas.alpha_composite(shadow, (0, 18 * SCALE))

    # Кремовая карточка с тонкой золотой обводкой.
    card = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle(
        (250 * SCALE, 130 * SCALE, 1750 * SCALE, 1860 * SCALE),
        radius=100 * SCALE,
        fill=(*CREAM, 255),
        outline=(*GOLD, 255),
        width=max(1, int(2.2 * SCALE)),
    )
    canvas.alpha_composite(card)

    draw_qr(canvas, (400 * SCALE, 210 * SCALE, 1200 * SCALE, 1200 * SCALE))

    font_history = ImageFont.truetype(FONT_PATH, int(122 * SCALE), index=FONT_ULTRA)
    font_lounge = ImageFont.truetype(FONT_PATH, int(44 * SCALE), index=FONT_LIGHT)
    font_small = ImageFont.truetype(FONT_PATH, int(28 * SCALE), index=FONT_LIGHT)
    font_handle = ImageFont.truetype(FONT_PATH, int(38 * SCALE), index=FONT_MEDIUM)

    text = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    td.text(
        (1000 * SCALE, 1498 * SCALE),
        "History",
        font=font_history,
        fill=(*INK, 255),
        anchor="mm",
    )
    draw_tracking(
        td,
        "lounge",
        font_lounge,
        13 * SCALE,
        (*GOLD_DARK, 255),
        1000 * SCALE,
        1580 * SCALE,
    )

    td.line(
        (900 * SCALE, 1636 * SCALE, 1100 * SCALE, 1636 * SCALE),
        fill=(*GOLD, 170),
        width=max(1, int(1.6 * SCALE)),
    )

    td.text(
        (1000 * SCALE, 1682 * SCALE),
        "Сканируйте, чтобы оставить отзыв",
        font=font_small,
        fill=(*MUTED, 255),
        anchor="mm",
    )
    td.text(
        (1000 * SCALE, 1745 * SCALE),
        "@loungeHistory_bot",
        font=font_handle,
        fill=(*INK, 255),
        anchor="mm",
    )

    canvas.alpha_composite(text)

    result = canvas.convert("RGB").resize((FINAL, FINAL), Image.Resampling.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.save(OUT, "PNG", optimize=True)
    print(f"Готово: {OUT} ({OUT.stat().st_size // 1024} КБ, {FINAL}×{FINAL})")


if __name__ == "__main__":
    main()
