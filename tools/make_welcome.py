"""Генерирует приветственную картинку-заглушку для бота.

Запуск:  .venv/bin/python tools/make_welcome.py
Результат: assets/welcome.jpg (1280×1280)

Картинку можно заменить в самом боте: /admin → «Заменить картинку».
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "welcome.jpg"

SCALE = 2
SIZE = 1280
W = SIZE * SCALE
CENTER = W // 2

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_ULTRA = 5
FONT_LIGHT = 7

EMOJI_FONT_PATH = "/System/Library/Fonts/Apple Color Emoji.ttc"
EMOJI_SIZE = 160


def lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def vertical_gradient(width: int, height: int, top: tuple, bottom: tuple) -> Image.Image:
    strip = Image.new("RGB", (1, height))
    pixels = strip.load()
    for y in range(height):
        t = y / max(1, height - 1)
        pixels[0, y] = tuple(lerp(top[i], bottom[i], t) for i in range(3))
    return strip.resize((width, height), Image.Resampling.BICUBIC)


def radial_alpha(size: int, radius: float) -> Image.Image:
    """Круглая маска: 255 в центре, 0 на краю."""
    small = 360
    mask = Image.new("L", (small, small))
    px = mask.load()
    c = (small - 1) / 2
    for y in range(small):
        for x in range(small):
            d = math.hypot(x - c, y - c) / (small / 2)
            value = max(0.0, 1.0 - d) ** 1.6
            px[x, y] = int(255 * value)
    mask = mask.resize((size, size), Image.Resampling.BICUBIC)
    if size != int(radius * 2):
        mask = mask.crop(
            (
                int((size - radius * 2) / 2),
                int((size - radius * 2) / 2),
                int((size + radius * 2) / 2),
                int((size + radius * 2) / 2),
            )
        )
    return mask


def make_background() -> Image.Image:
    background = vertical_gradient(W, W, (12, 8, 5), (30, 17, 9)).convert("RGBA")

    glow_size = int(W * 0.95)
    mask = radial_alpha(glow_size, glow_size / 2)
    glow = Image.new("RGBA", (glow_size, glow_size), (255, 148, 68, 0))
    glow.putalpha(mask.point(lambda v: int(v * 0.55)))
    background.alpha_composite(
        glow, (CENTER - glow_size // 2, int(W * 0.58) - glow_size // 2)
    )

    rng = random.Random(7)
    bokeh = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bokeh)
    warm = [
        (196, 92, 34),
        (230, 128, 48),
        (244, 164, 78),
        (170, 66, 24),
    ]
    for _ in range(54):
        x = rng.randint(-100, W + 100)
        y = rng.randint(-100, W + 100)
        r = rng.randint(10, 88)
        color = rng.choice(warm)
        alpha = rng.randint(12, 46)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*color, alpha))
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(26))
    background.alpha_composite(bokeh)

    vignette = Image.new("L", (W, W), 0)
    vd = ImageDraw.Draw(vignette)
    steps = 90
    for i in range(steps):
        t = i / steps
        inset = int(t * W * 0.5)
        alpha = int(130 * (t**2))
        vd.ellipse(
            (inset, inset, W - inset, W - inset),
            outline=alpha,
            width=max(2, W // 120),
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(60))
    black = Image.new("RGBA", (W, W), (0, 0, 0, 255))
    black.putalpha(vignette)
    background.alpha_composite(black)
    return background


def emoji_sprite(emoji: str) -> Image.Image:
    font = ImageFont.truetype(EMOJI_FONT_PATH, EMOJI_SIZE)
    image = Image.new("RGBA", (EMOJI_SIZE * 2, EMOJI_SIZE * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((EMOJI_SIZE // 2, EMOJI_SIZE // 3), emoji, font=font, embedded_color=True)
    bbox = image.getbbox()
    return image.crop(bbox)


def add_leaf(
    canvas: Image.Image,
    sprite: Image.Image,
    center: tuple[float, float],
    size: int,
    angle: float,
    brightness: float = 1.0,
    blur: float = 0,
    alpha: int = 255,
) -> None:
    scale = size / max(sprite.size)
    leaf = sprite.resize(
        (max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale))),
        Image.Resampling.LANCZOS,
    )
    leaf = ImageEnhance.Brightness(leaf).enhance(brightness)
    leaf = leaf.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    if blur:
        leaf = leaf.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 255:
        leaf.putalpha(leaf.getchannel("A").point(lambda v: int(v * alpha / 255)))

    shadow = Image.new("RGBA", leaf.size, (0, 0, 0, 0))
    shadow.putalpha(leaf.getchannel("A").point(lambda v: int(v * 0.5)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(size * 0.06))
    x = int(center[0] - leaf.width / 2)
    y = int(center[1] - leaf.height / 2)
    canvas.alpha_composite(shadow, (x + size // 16, y + size // 12))
    canvas.alpha_composite(leaf, (x, y))


def add_ring(canvas: Image.Image) -> None:
    radius = int(W * 0.458)
    width = max(2, int(3.4 * SCALE))
    box = (CENTER - radius, CENTER - radius, CENTER + radius, CENTER + radius)

    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for extra, alpha in ((26 * SCALE, 26), (12 * SCALE, 55), (4 * SCALE, 90)):
        gd.ellipse(
            (box[0] - extra, box[1] - extra, box[2] + extra, box[3] + extra),
            outline=(255, 150, 64, alpha),
            width=max(2, width + extra // 3),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(9 * SCALE))
    canvas.alpha_composite(glow)

    ring = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse(box, outline=(255, 170, 84, 255), width=width)
    rd.ellipse(
        (box[0] - width, box[1] - width, box[2] + width, box[3] + width),
        outline=(255, 195, 130, 90),
        width=max(1, width // 2),
    )
    ring = ring.filter(ImageFilter.GaussianBlur(0.7 * SCALE))
    canvas.alpha_composite(ring)


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
    for char, char_width in zip(text, widths):
        draw.text((x, y), char, font=font, fill=fill, anchor="lm")
        x += char_width + tracking


def main() -> None:
    canvas = make_background()
    add_ring(canvas)

    maple = emoji_sprite("🍁")
    leaves = emoji_sprite("🍂")
    sprites = [maple, maple, maple, leaves]

    rng = random.Random(12)

    # Дальние, слегка размытые листья — глубина кадра.
    for angle in (18, 74, 132, 196, 254, 312):
        theta = math.radians(angle + rng.randint(-8, 8))
        distance = W * 0.505 + rng.randint(0, 26) * SCALE
        add_leaf(
            canvas,
            rng.choice(sprites),
            (CENTER + math.cos(theta) * distance, CENTER + math.sin(theta) * distance),
            rng.randint(110, 150) * SCALE,
            rng.randint(0, 360),
            brightness=rng.uniform(0.72, 0.88),
            blur=2.6 * SCALE,
            alpha=190,
        )

    # Основные листья по кольцу.
    angles = [4, 24, 47, 68, 91, 112, 135, 157, 181, 203, 226, 248, 270, 291, 314, 336]
    for index, angle in enumerate(angles):
        theta = math.radians(angle + rng.randint(-6, 6))
        distance = W * 0.472 + rng.randint(-10, 38) * SCALE
        size = rng.randint(74, 116) * SCALE
        foreground = index % 4 != 2
        add_leaf(
            canvas,
            rng.choice(sprites),
            (CENTER + math.cos(theta) * distance, CENTER + math.sin(theta) * distance),
            size,
            rng.randint(0, 360),
            brightness=rng.uniform(0.9, 1.06),
            blur=0 if foreground else 1.6 * SCALE,
            alpha=255 if foreground else 215,
        )

    # Текст логотипа.
    font_history = ImageFont.truetype(FONT_PATH, int(196 * SCALE), index=FONT_ULTRA)
    font_lounge = ImageFont.truetype(FONT_PATH, int(72 * SCALE), index=FONT_LIGHT)

    text_layer = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    draw.text(
        (CENTER, int(W * 0.405)),
        "History",
        font=font_history,
        fill=(247, 243, 236, 255),
        anchor="mm",
    )
    draw_tracking(
        draw,
        "lounge",
        font_lounge,
        16 * SCALE,
        (231, 154, 84, 255),
        CENTER,
        int(W * 0.505),
    )

    glow_text = text_layer.filter(ImageFilter.GaussianBlur(16 * SCALE))
    glow_text.putalpha(glow_text.getchannel("A").point(lambda v: int(v * 0.35)))
    canvas.alpha_composite(glow_text)
    canvas.alpha_composite(text_layer)

    noise = Image.effect_noise((W, W), 22).convert("L")
    noise_rgba = Image.merge(
        "RGBA",
        (noise, noise, noise, Image.new("L", (W, W), 10)),
    )
    canvas.alpha_composite(noise_rgba)

    result = canvas.convert("RGB").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.save(OUT, "JPEG", quality=92, optimize=True)
    print(f"Готово: {OUT} ({OUT.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
