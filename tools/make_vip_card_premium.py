"""Премиальная VIP-карта History Lounge.

Тёмный металл, золотая фольга, тонкая гравировка и минимум текста.
Запуск:  .venv/bin/python tools/make_vip_card_premium.py

Результат:
  assets/vip_card_premium_front.png
  assets/vip_card_premium_back.png
  assets/vip_card_premium_print.pdf
  assets/vip_card_premium_mockup.jpg
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_qr import (  # noqa: E402
    FONT_LIGHT,
    FONT_PATH,
    FONT_ULTRA,
    SERIF_PATH,
    draw_qr,
    mm,
    perspective_paste,
    pt,
    radial_glow,
    vertical_gradient,
)
from make_vip_card import (  # noqa: E402
    CORNER_R,
    CX,
    CY,
    H,
    TH,
    TW,
    TX,
    TY,
    W,
    draw_tracking_at,
    make_preview,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

NOIR_TOP = (30, 31, 24)
NOIR_BOTTOM = (9, 9, 7)
GOLD_MID = (193, 151, 90)
GOLD_LIGHT = (242, 215, 160)
GOLD_PALE = (255, 238, 198)
IVORY = (244, 238, 226)
MUTED = (178, 168, 148)
CREAM_QR = (246, 240, 229)

URL = "https://t.me/loungeHistory_bot"


def draw_gold_text(
    canvas: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    xy: tuple[float, float],
    *,
    anchor: str = "mm",
) -> None:
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255, anchor=anchor)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.65)))
    canvas.alpha_composite(shadow, (0, 2))

    bbox = mask.getbbox()
    if not bbox:
        return
    x0, y0, x1, y1 = bbox
    gold = vertical_gradient(x1 - x0, y1 - y0, GOLD_MID, GOLD_PALE).convert("RGBA")
    gold.putalpha(mask.crop(bbox))
    canvas.alpha_composite(gold, (x0, y0))


def draw_circular_text(
    layer: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    center: tuple[float, float],
    radius: float,
    start_deg: float,
    end_deg: float,
    fill: tuple,
) -> None:
    """Текст по дуге — для печати-медальона."""
    draw = ImageDraw.Draw(layer)
    widths = [draw.textlength(char, font=font) for char in text]
    arc_length = math.radians(end_deg - start_deg) * radius
    gap = (arc_length - sum(widths)) / max(1, len(text) - 1)
    gap = max(0.0, gap)
    angle = start_deg
    for char, width in zip(text, widths):
        mid_angle = angle + math.degrees((width / 2) / radius)
        radians = math.radians(mid_angle)
        x = center[0] + radius * math.cos(radians)
        y = center[1] + radius * math.sin(radians)

        box = 64
        char_image = Image.new("RGBA", (box, box), (0, 0, 0, 0))
        ImageDraw.Draw(char_image).text(
            (box / 2, box / 2),
            char,
            font=font,
            fill=fill,
            anchor="mm",
        )
        rotated = char_image.rotate(
            -(mid_angle + 90),
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )
        layer.alpha_composite(
            rotated,
            (int(x - rotated.width / 2), int(y - rotated.height / 2)),
        )
        angle += math.degrees((width + gap) / radius)


def draw_seal(canvas: Image.Image, cx: float, cy: float) -> None:
    """Круглая печать частного клуба: тонкие кольца и текст по дуге."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    outer = mm(10.0)
    inner = mm(7.55)

    draw.ellipse(
        (cx - outer, cy - outer, cx + outer, cy + outer),
        outline=(*GOLD_MID, 115),
        width=max(1, mm(0.13)),
    )
    draw.ellipse(
        (cx - inner, cy - inner, cx + inner, cy + inner),
        outline=(*GOLD_MID, 55),
        width=max(1, mm(0.08)),
    )

    font_ring = ImageFont.truetype(FONT_PATH, pt(2.0), index=FONT_LIGHT)
    draw_circular_text(
        layer,
        "HISTORY LOUNGE · PRIVATE MEMBER",
        font_ring,
        (cx, cy),
        mm(8.8),
        200,
        340,
        (*GOLD_MID, 145),
    )

    # Маленький ромб в нижней точке печати.
    r = mm(0.7)
    draw.polygon(
        [
            (cx, cy + mm(9.15) - r),
            (cx + r, cy + mm(9.15)),
            (cx, cy + mm(9.15) + r),
            (cx - r, cy + mm(9.15)),
        ],
        fill=(*GOLD_MID, 165),
    )
    canvas.alpha_composite(layer)

    font_monogram = ImageFont.truetype(SERIF_PATH, pt(13), index=0)
    draw_gold_text(
        canvas,
        "HL",
        font_monogram,
        (cx, cy - mm(1.2)),
        anchor="mm",
    )

    inside = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    inside_draw = ImageDraw.Draw(inside)
    font_tiny = ImageFont.truetype(FONT_PATH, pt(1.7), index=FONT_LIGHT)
    draw_tracking_at(
        inside_draw,
        "TASHKENT",
        font_tiny,
        pt(1.7) * 0.28,
        (*GOLD_MID, 175),
        cx,
        cy + mm(4.8),
        anchor="mm",
    )
    canvas.alpha_composite(inside)


def make_noir_background() -> Image.Image:
    canvas = vertical_gradient(W, H, NOIR_TOP, NOIR_BOTTOM).convert("RGBA")

    glow = radial_glow(int(max(W, H) * 0.95), (176, 146, 96), 0.10)
    canvas.alpha_composite(glow, (-int(W * 0.25), -int(H * 0.35)))

    rng = random.Random(43)
    brushed = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(brushed)
    for y in range(0, H, 2):
        alpha = rng.randint(2, 7)
        color = GOLD_PALE if rng.random() < 0.5 else (0, 0, 0)
        bd.line((0, y, W, y), fill=(*color, alpha), width=1)
    brushed = brushed.filter(ImageFilter.GaussianBlur(0.6))
    canvas.alpha_composite(brushed)

    sheen = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sheen)
    sd.polygon(
        [
            (-int(W * 0.2), int(H * 0.12)),
            (int(W * 0.62), -int(H * 0.18)),
            (int(W * 1.05), int(H * 0.58)),
            (int(W * 0.25), int(H * 1.12)),
        ],
        fill=22,
    )
    sheen = sheen.filter(ImageFilter.GaussianBlur(mm(14)))
    light = Image.new("RGBA", (W, H), (255, 245, 223, 255))
    light.putalpha(sheen)
    canvas.alpha_composite(light)

    noise = Image.effect_noise((W, H), 13).convert("L")
    canvas.alpha_composite(
        Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 4)))
    )

    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    for index in range(50):
        t = index / 50
        inset = int(t * min(W, H) * 0.34)
        vd.rounded_rectangle(
            (inset, inset, W - inset, H - inset),
            radius=mm(3),
            outline=int(90 * t**2),
            width=max(2, mm(0.8)),
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(mm(4)))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(vignette)
    canvas.alpha_composite(black)
    return canvas


def add_gold_frame(canvas: Image.Image, inset_mm: float, width_mm: float, alpha: int) -> None:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    inset = mm(inset_mm)
    draw.rounded_rectangle(
        (TX + inset, TY + inset, TX + TW - inset, TY + TH - inset),
        radius=mm(2.2),
        outline=(*GOLD_MID, alpha),
        width=max(1, mm(width_mm)),
    )
    canvas.alpha_composite(layer)


def make_front() -> Image.Image:
    canvas = make_noir_background()
    add_gold_frame(canvas, 3.6, 0.16, 155)
    add_gold_frame(canvas, 4.35, 0.10, 55)

    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    font_micro = ImageFont.truetype(FONT_PATH, pt(4.0), index=FONT_LIGHT)
    font_history = ImageFont.truetype(FONT_PATH, pt(30), index=FONT_ULTRA)
    font_lounge = ImageFont.truetype(FONT_PATH, pt(7.5), index=FONT_LIGHT)
    font_member = ImageFont.truetype(FONT_PATH, pt(4.0), index=FONT_LIGHT)
    font_label = ImageFont.truetype(FONT_PATH, pt(3.6), index=FONT_LIGHT)
    font_value = ImageFont.truetype(FONT_PATH, pt(6.0), index=FONT_LIGHT)
    font_microline = ImageFont.truetype(FONT_PATH, pt(1.55), index=FONT_LIGHT)

    top_y = TY + mm(8.2)
    draw_tracking_at(
        td,
        "PRIVATE CLIENT",
        font_micro,
        pt(4.0) * 0.30,
        (*GOLD_MID, 230),
        TX + mm(7),
        top_y,
    )
    draw_tracking_at(
        td,
        "EST. 2026",
        font_label,
        pt(3.6) * 0.28,
        (*GOLD_MID, 190),
        CX,
        top_y,
        anchor="mm",
    )
    draw_tracking_at(
        td,
        "TASHKENT",
        font_micro,
        pt(4.0) * 0.30,
        (*GOLD_MID, 230),
        TX + TW - mm(7),
        top_y,
        anchor="rm",
    )

    word_x = TX + mm(8.0)
    draw_gold_text(
        canvas,
        "History",
        font_history,
        (word_x, CY - mm(5.0)),
        anchor="lm",
    )
    draw_tracking_at(
        td,
        "lounge",
        font_lounge,
        pt(7.5) * 0.52,
        (*GOLD_LIGHT, 245),
        word_x + mm(0.7),
        CY + mm(1.7),
    )
    td.line(
        (word_x + mm(0.7), CY + mm(5.1), word_x + mm(29.0), CY + mm(5.1)),
        fill=(*GOLD_MID, 95),
        width=max(1, mm(0.12)),
    )
    draw_tracking_at(
        td,
        "VIP MEMBER",
        font_member,
        pt(4.0) * 0.52,
        (*GOLD_LIGHT, 235),
        word_x + mm(0.7),
        CY + mm(8.3),
    )

    draw_seal(canvas, TX + TW * 0.80, CY + mm(1.0))

    label_y = TY + TH - mm(12.2)
    value_y = TY + TH - mm(9.2)

    draw_tracking_at(
        td,
        "MEMBER",
        font_label,
        pt(3.6) * 0.22,
        (*GOLD_MID, 220),
        TX + mm(7),
        label_y,
    )
    draw_tracking_at(
        td,
        "А. КАРИМОВ",
        font_value,
        pt(6.0) * 0.10,
        (*IVORY, 242),
        TX + mm(7),
        value_y,
    )

    draw_tracking_at(
        td,
        "CARD NO.",
        font_label,
        pt(3.6) * 0.22,
        (*GOLD_MID, 220),
        TX + TW * 0.55,
        label_y,
        anchor="mm",
    )
    draw_tracking_at(
        td,
        "0001",
        font_value,
        pt(6.0) * 0.12,
        (*IVORY, 242),
        TX + TW * 0.55,
        value_y,
        anchor="mm",
    )

    draw_tracking_at(
        td,
        "MEMBER SINCE",
        font_label,
        pt(3.6) * 0.22,
        (*GOLD_MID, 220),
        TX + TW - mm(7),
        label_y,
        anchor="rm",
    )
    draw_tracking_at(
        td,
        "2026",
        font_value,
        pt(6.0) * 0.12,
        (*IVORY, 242),
        TX + TW - mm(7),
        value_y,
        anchor="rm",
    )

    draw_tracking_at(
        td,
        "HISTORY LOUNGE  ·  PRIVATE MEMBERSHIP  ·  TASHKENT",
        font_microline,
        pt(1.55) * 0.18,
        (*GOLD_MID, 115),
        CX,
        TY + TH - mm(5.0),
        anchor="mm",
    )

    canvas.alpha_composite(text)
    return canvas


def make_back() -> Image.Image:
    canvas = make_noir_background()
    add_gold_frame(canvas, 3.6, 0.16, 155)
    add_gold_frame(canvas, 4.35, 0.10, 55)

    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    font_logo = ImageFont.truetype(FONT_PATH, pt(4.4), index=FONT_LIGHT)
    font_micro = ImageFont.truetype(FONT_PATH, pt(4.0), index=FONT_LIGHT)
    font_title = ImageFont.truetype(FONT_PATH, pt(6.2), index=FONT_LIGHT)
    font_benefit = ImageFont.truetype(FONT_PATH, pt(5.4), index=FONT_LIGHT)
    font_small = ImageFont.truetype(FONT_PATH, pt(4.4), index=FONT_LIGHT)
    font_tiny = ImageFont.truetype(FONT_PATH, pt(3.4), index=FONT_LIGHT)

    top_y = TY + mm(8.2)
    draw_tracking_at(
        td,
        "HISTORY LOUNGE",
        font_logo,
        pt(4.4) * 0.46,
        (*GOLD_LIGHT, 255),
        CX,
        top_y,
        anchor="mm",
    )
    draw_tracking_at(
        td,
        "VIP",
        font_micro,
        pt(4.0) * 0.32,
        (*GOLD_MID, 240),
        TX + TW - mm(7),
        top_y,
        anchor="rm",
    )

    draw_tracking_at(
        td,
        "ПРИВИЛЕГИИ",
        font_title,
        pt(6.2) * 0.30,
        (*GOLD_LIGHT, 235),
        TX + mm(7),
        TY + mm(14.9),
    )
    td.line(
        (TX + mm(7), TY + mm(18.5), TX + mm(24.0), TY + mm(18.5)),
        fill=(*GOLD_MID, 70),
        width=max(1, mm(0.10)),
    )

    benefits = [
        "Персональный менеджер",
        "Приоритетная бронь",
        "Комплимент от шефа",
        "Закрытые мероприятия",
    ]
    start_y = TY + mm(21.0)
    step = mm(4.0)
    diamond_r = mm(0.55)

    for index, item in enumerate(benefits):
        y = start_y + index * step
        td.polygon(
            [
                (TX + mm(8), y - diamond_r),
                (TX + mm(8) + diamond_r, y),
                (TX + mm(8), y + diamond_r),
                (TX + mm(8) - diamond_r, y),
            ],
            fill=(*GOLD_MID, 235),
        )
        td.text(
            (TX + mm(11.4), y),
            item,
            font=font_benefit,
            fill=(*IVORY, 245),
            anchor="lm",
        )

    # QR консьержа на кремовой панели.
    qr_size = mm(13.5)
    qr_x = TX + TW - mm(7) - mm(16)
    qr_y = TY + mm(20.0)
    panel = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(
        (qr_x, qr_y, qr_x + mm(16), qr_y + mm(16)),
        radius=mm(1.1),
        fill=(*CREAM_QR, 255),
        outline=(*GOLD_MID, 150),
        width=max(1, mm(0.14)),
    )
    canvas.alpha_composite(panel)
    draw_qr(
        canvas,
        (qr_x + mm(1.25), qr_y + mm(1.25), qr_x + mm(14.75), qr_y + mm(14.75)),
        ink=(30, 29, 22),
        paper=CREAM_QR,
        logo=None,
    )
    draw_tracking_at(
        td,
        "CONCIERGE",
        font_tiny,
        pt(3.4) * 0.28,
        (*GOLD_MID, 225),
        qr_x + mm(8.0),
        qr_y + mm(18.2),
        anchor="mm",
    )

    line_y = TY + TH - mm(10.4)
    td.line(
        (TX + mm(7), line_y, TX + TW - mm(7), line_y),
        fill=(*GOLD_MID, 75),
        width=max(1, mm(0.11)),
    )

    contact_y = TY + TH - mm(7.6)
    td.text(
        (TX + mm(7), contact_y),
        "+998 77 131-11-11",
        font=font_small,
        fill=(*IVORY, 230),
        anchor="lm",
    )
    td.text(
        (TX + TW - mm(7), contact_y),
        "@history.lounge",
        font=font_small,
        fill=(*GOLD_MID, 245),
        anchor="rm",
    )

    draw_tracking_at(
        td,
        "PRIVATE CLIENT  ·  TASHKENT",
        font_tiny,
        pt(3.4) * 0.22,
        (*MUTED, 205),
        CX,
        TY + TH - mm(4.8),
        anchor="mm",
    )

    canvas.alpha_composite(text)
    return canvas


def make_mockup(front: Image.Image, back: Image.Image) -> Image.Image:
    width, height = 1800, 1200
    canvas = vertical_gradient(width, height, (52, 51, 45), (12, 12, 10)).convert(
        "RGBA"
    )

    glow = radial_glow(1700, (184, 152, 100), 0.16)
    canvas.alpha_composite(glow, (-280, -470))

    halo = radial_glow(1500, (158, 148, 126), 0.09)
    canvas.alpha_composite(halo, (150, 120))

    cool = radial_glow(1200, (88, 94, 98), 0.055)
    canvas.alpha_composite(cool, (980, 520))

    # Тёмный камень: редкие прожилки и мелкая крошка.
    rng = random.Random(52)
    veins = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veins)
    for _ in range(18):
        y0 = rng.randint(-60, height + 60)
        amplitude = rng.uniform(8, 30)
        phase = rng.uniform(0, math.tau)
        frequency = rng.uniform(130, 430)
        color = rng.choice([(154, 144, 124), (62, 60, 52), (108, 100, 84)])
        alpha = rng.randint(4, 10)
        points = [
            (
                x,
                y0
                + math.sin(x / frequency + phase) * amplitude
                + math.sin(x / (frequency * 0.31) + phase) * amplitude * 0.25,
            )
            for x in range(-20, width + 40, 24)
        ]
        vd.line(points, fill=(*color, alpha), width=rng.randint(1, 3))
    veins = veins.filter(ImageFilter.GaussianBlur(2.0))
    canvas.alpha_composite(veins)

    specks = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(specks)
    for _ in range(650):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        radius = rng.choice([1, 1, 1, 2])
        color = rng.choice([(204, 184, 147), (124, 118, 102), (66, 64, 57)])
        sd.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(*color, rng.randint(4, 12)),
        )
    specks = specks.filter(ImageFilter.GaussianBlur(0.8))
    canvas.alpha_composite(specks)

    noise = Image.effect_noise((width, height), 14).convert("L")
    canvas.alpha_composite(
        Image.merge(
            "RGBA", (noise, noise, noise, Image.new("L", (width, height), 4))
        )
    )

    # Мягкая тень под картами — они лежат на камне, а не висят в воздухе.
    ground = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ground)
    gd.ellipse((80, 790, 1715, 1015), fill=(0, 0, 0, 145))
    ground = ground.filter(ImageFilter.GaussianBlur(58))
    canvas.alpha_composite(ground)

    back_quad = [
        (940.0, 370.0),
        (1590.0, 342.0),
        (1615.0, 782.0),
        (965.0, 810.0),
    ]
    front_quad = [
        (175.0, 392.0),
        (885.0, 362.0),
        (912.0, 820.0),
        (202.0, 850.0),
    ]

    def paste_card(card: Image.Image, quad: list[tuple[float, float]]) -> None:
        # Тень.
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        sdw = ImageDraw.Draw(shadow)
        sdw.rounded_rectangle(
            (0, 0, card.width - 1, card.height - 1),
            radius=CORNER_R,
            fill=(0, 0, 0, 165),
        )
        shadow_quad = [(x + 9, y + 24) for x, y in quad]
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        perspective_paste(shadow_layer, shadow, shadow_quad)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(22))
        canvas.alpha_composite(shadow_layer)

        # Тёмный торец.
        thickness_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        td = ImageDraw.Draw(thickness_layer)
        td.polygon([(x + 4, y + 7) for x, y in quad], fill=(6, 6, 5, 245))
        thickness_layer = thickness_layer.filter(ImageFilter.GaussianBlur(1.1))
        canvas.alpha_composite(thickness_layer)

        # Тонкая золотая кромка рисуется прямо на карте, поэтому сидит идеально.
        card_with_edge = card.copy().convert("RGBA")
        edge_draw = ImageDraw.Draw(card_with_edge)
        inset = max(1, mm(0.45))
        edge_draw.rounded_rectangle(
            (inset, inset, card.width - inset, card.height - inset),
            radius=CORNER_R - inset,
            outline=(*GOLD_MID, 235),
            width=max(1, mm(0.17)),
        )
        perspective_paste(canvas, card_with_edge, quad)

        # Лёгкий блик по верхней кромке.
        highlight = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        hd = ImageDraw.Draw(highlight)
        hd.line([quad[0], quad[1]], fill=(*GOLD_PALE, 65), width=2)
        highlight = highlight.filter(ImageFilter.GaussianBlur(1.2))
        canvas.alpha_composite(highlight)

    paste_card(back, back_quad)
    paste_card(front, front_quad)

    caption = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cd = ImageDraw.Draw(caption)
    font_caption = ImageFont.truetype(FONT_PATH, 22, index=FONT_LIGHT)
    font_sub = ImageFont.truetype(FONT_PATH, 12, index=FONT_LIGHT)
    draw_tracking_at(
        cd,
        "HISTORY LOUNGE",
        font_caption,
        10,
        (*GOLD_LIGHT, 245),
        width / 2,
        1065,
        anchor="mm",
    )
    cd.line((width / 2 - 180, 1091, width / 2 + 180, 1091), fill=(*GOLD_MID, 100), width=1)
    draw_tracking_at(
        cd,
        "PRIVATE MEMBERSHIP  ·  TASHKENT",
        font_sub,
        4,
        (*IVORY, 175),
        width / 2,
        1117,
        anchor="mm",
    )
    canvas.alpha_composite(caption)

    vignette = Image.new("L", (width, height), 0)
    vd = ImageDraw.Draw(vignette)
    for index in range(60):
        t = index / 60
        inset = int(t * 480)
        vd.rectangle(
            (inset, inset, width - inset, height - inset),
            outline=int(95 * t**2),
            width=24,
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(65))
    black = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    black.putalpha(vignette)
    canvas.alpha_composite(black)

    return canvas.convert("RGB")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    front_canvas = make_front()
    back_canvas = make_back()

    front = make_preview(front_canvas)
    back = make_preview(back_canvas)

    front_path = ASSETS / "vip_card_premium_front.png"
    front.save(front_path, "PNG", optimize=True)

    back_path = ASSETS / "vip_card_premium_back.png"
    back.save(back_path, "PNG", optimize=True)

    pdf_path = ASSETS / "vip_card_premium_print.pdf"
    front_canvas.convert("RGB").save(
        pdf_path,
        "PDF",
        resolution=600,
        save_all=True,
        append_images=[back_canvas.convert("RGB")],
    )

    mockup = make_mockup(front, back)
    mockup_path = ASSETS / "vip_card_premium_mockup.jpg"
    mockup.save(mockup_path, "JPEG", quality=94, optimize=True)

    for path in (front_path, back_path, pdf_path, mockup_path):
        print(f"Готово: {path} ({path.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
