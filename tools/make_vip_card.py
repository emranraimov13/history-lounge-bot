"""VIP-карта History Lounge.

Запуск:  .venv/bin/python tools/make_vip_card.py

Результат:
  assets/vip_card_front.png      — лицо карты, 600 dpi
  assets/vip_card_back.png       — оборот карты, 600 dpi
  assets/vip_card_print.pdf      — 2 страницы для типографии, 600 dpi + вылеты
  assets/vip_card_mockup.jpg     — презентационный макет
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_qr import (  # noqa: E402
    BRASS,
    BRASS_LIGHT,
    CREAM,
    FONT_LIGHT,
    FONT_MEDIUM,
    FONT_PATH,
    LIGHT_INK,
    LIGHT_OLIVE,
    LIGHT_PAPER,
    MUTED_ON_CREAM,
    MUTED_ON_DARK,
    SERIF_PATH,
    draw_qr,
    draw_tracking,
    find_coeffs,
    make_light_background,
    mm,
    perspective_paste,
    pt,
    radial_glow,
    vertical_gradient,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

CARD_W = 85.6
CARD_H = 54.0
BLEED = 3.0
PAGE_W = CARD_W + BLEED * 2
PAGE_H = CARD_H + BLEED * 2

W = mm(PAGE_W)
H = mm(PAGE_H)
TX = mm(BLEED)
TY = mm(BLEED)
TW = mm(CARD_W)
TH = mm(CARD_H)
CX = TX + TW / 2
CY = TY + TH / 2
CORNER_R = mm(3.18)

DARK_TOP = (64, 60, 46)
DARK_BOTTOM = (28, 27, 21)
CARD_BRASS = (183, 149, 96)
CARD_BRASS_LIGHT = (211, 181, 128)
CARD_INK = (47, 44, 33)
CARD_MUTED = (188, 179, 160)
BACK_BG = (246, 240, 229)

URL = "https://t.me/loungeHistory_bot"


def tracking_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
) -> float:
    return sum(draw.textlength(char, font=font) for char in text) + tracking * (
        len(text) - 1
    )


def draw_tracking_at(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
    fill: tuple,
    x: float,
    y: float,
    *,
    anchor: str = "lm",
) -> None:
    total = tracking_width(draw, text, font, tracking)
    if anchor == "rm":
        x -= total
    elif anchor == "mm":
        x -= total / 2
    for char in text:
        draw.text((x, y), char, font=font, fill=fill, anchor="lm")
        x += draw.textlength(char, font=font) + tracking


def add_card_frame(
    canvas: Image.Image,
    inset_mm: float,
    width_mm: float,
    alpha: int,
    color: tuple,
) -> None:
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    inset = mm(inset_mm)
    draw.rounded_rectangle(
        (TX + inset, TY + inset, TX + TW - inset, TY + TH - inset),
        radius=mm(2.4),
        outline=(*color, alpha),
        width=max(1, mm(width_mm)),
    )
    canvas.alpha_composite(layer)


def make_front() -> Image.Image:
    canvas = vertical_gradient(W, H, DARK_TOP, DARK_BOTTOM).convert("RGBA")

    glow = radial_glow(int(max(W, H) * 0.9), CARD_BRASS, 0.13)
    canvas.alpha_composite(
        glow, ((W - glow.width) // 2, int(H * 0.35) - glow.height // 2)
    )

    # Тонкий гильош на правой стороне.
    guilloche = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(guilloche)
    gx = TX + TW * 0.82
    gy = CY
    for index in range(24):
        rx = mm(8 + index * 1.55)
        ry = rx * 0.64
        gd.ellipse(
            (gx - rx, gy - ry, gx + rx, gy + ry),
            outline=(*CARD_BRASS, 13),
            width=max(1, mm(0.07)),
        )
    canvas.alpha_composite(guilloche)

    # Крупная литера H — водяной знак.
    font_h = ImageFont.truetype(SERIF_PATH, pt(108), index=0)
    watermark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(watermark)
    wd.text(
        (TX + TW * 0.82, CY + mm(1.0)),
        "H",
        font=font_h,
        fill=(*CARD_BRASS, 24),
        anchor="mm",
    )
    canvas.alpha_composite(watermark)

    noise = Image.effect_noise((W, H), 14).convert("L")
    canvas.alpha_composite(
        Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 4)))
    )

    add_card_frame(canvas, 4.0, 0.22, 155, CARD_BRASS)
    add_card_frame(canvas, 5.0, 0.15, 75, CARD_BRASS)

    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    font_micro = ImageFont.truetype(FONT_PATH, pt(5.0), index=FONT_LIGHT)
    font_vip = ImageFont.truetype(SERIF_PATH, pt(47), index=0)
    font_member = ImageFont.truetype(FONT_PATH, pt(5.4), index=FONT_LIGHT)
    font_label = ImageFont.truetype(FONT_PATH, pt(4.2), index=FONT_LIGHT)
    font_value = ImageFont.truetype(FONT_PATH, pt(6.4), index=FONT_MEDIUM)

    draw_tracking_at(
        td,
        "HISTORY LOUNGE",
        font_micro,
        pt(5.0) * 0.28,
        (*CREAM, 255),
        TX + mm(7),
        TY + mm(8.5),
    )
    draw_tracking_at(
        td,
        "TASHKENT",
        font_micro,
        pt(5.0) * 0.28,
        (*CARD_BRASS_LIGHT, 255),
        TX + TW - mm(7),
        TY + mm(8.5),
        anchor="rm",
    )

    vip_x = TX + TW * 0.35
    draw_tracking_at(
        td,
        "VIP",
        font_vip,
        pt(47) * 0.10,
        (*CARD_BRASS_LIGHT, 255),
        vip_x,
        CY - mm(0.5),
        anchor="mm",
    )
    line_half = mm(13.5)
    td.line(
        (vip_x - line_half, CY + mm(7.6), vip_x + line_half, CY + mm(7.6)),
        fill=(*CARD_BRASS, 190),
        width=max(1, mm(0.20)),
    )
    draw_tracking_at(
        td,
        "MEMBER CARD",
        font_member,
        pt(5.4) * 0.32,
        (*CREAM, 235),
        vip_x,
        CY + mm(10.6),
        anchor="mm",
    )

    bottom_y = TY + TH - mm(7.6)
    label_y = TY + TH - mm(11.4)

    draw_tracking_at(
        td,
        "CARDHOLDER",
        font_label,
        pt(4.2) * 0.20,
        (*CARD_BRASS, 230),
        TX + mm(7),
        label_y,
    )
    td.text(
        (TX + mm(7), bottom_y),
        "А. КАРИМОВ",
        font=font_value,
        fill=(*CREAM, 255),
        anchor="lm",
    )

    draw_tracking_at(
        td,
        "CARD NO.",
        font_label,
        pt(4.2) * 0.20,
        (*CARD_BRASS, 230),
        TX + TW * 0.53,
        label_y,
        anchor="mm",
    )
    td.text(
        (TX + TW * 0.53, bottom_y),
        "0001",
        font=font_value,
        fill=(*CREAM, 255),
        anchor="mm",
    )

    draw_tracking_at(
        td,
        "MEMBER SINCE",
        font_label,
        pt(4.2) * 0.20,
        (*CARD_BRASS, 230),
        TX + TW - mm(7),
        label_y,
        anchor="rm",
    )
    td.text(
        (TX + TW - mm(7), bottom_y),
        "2026",
        font=font_value,
        fill=(*CREAM, 255),
        anchor="rm",
    )

    canvas.alpha_composite(text)
    return canvas


def make_back() -> Image.Image:
    canvas = make_light_background(W, H)
    add_card_frame(canvas, 4.0, 0.22, 125, LIGHT_OLIVE)
    add_card_frame(canvas, 5.0, 0.15, 55, LIGHT_OLIVE)

    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text)

    font_micro = ImageFont.truetype(FONT_PATH, pt(5.0), index=FONT_LIGHT)
    font_title = ImageFont.truetype(FONT_PATH, pt(9.2), index=FONT_LIGHT)
    font_benefit = ImageFont.truetype(FONT_PATH, pt(6.7), index=FONT_LIGHT)
    font_small = ImageFont.truetype(FONT_PATH, pt(4.8), index=FONT_LIGHT)
    font_tiny = ImageFont.truetype(FONT_PATH, pt(4.4), index=FONT_LIGHT)

    draw_tracking_at(
        td,
        "HISTORY LOUNGE",
        font_micro,
        pt(5.0) * 0.28,
        (*LIGHT_OLIVE, 255),
        TX + mm(7),
        TY + mm(8.5),
    )
    draw_tracking_at(
        td,
        "VIP",
        font_micro,
        pt(5.0) * 0.28,
        (*BRASS, 255),
        TX + TW - mm(7),
        TY + mm(8.5),
        anchor="rm",
    )

    draw_tracking_at(
        td,
        "ПРИВИЛЕГИИ",
        font_title,
        pt(9.2) * 0.24,
        (*LIGHT_INK, 255),
        TX + mm(7),
        TY + mm(15),
    )

    benefits = [
        "Приоритетная бронь стола",
        "Комплимент от шефа",
        "Персональный менеджер",
        "Закрытые мероприятия",
        "Специальные условия на банкеты",
    ]
    start_y = TY + mm(21.3)
    step = mm(3.7)
    diamond_r = mm(0.65)

    for index, item in enumerate(benefits):
        y = start_y + index * step
        td.polygon(
            [
                (TX + mm(8), y - diamond_r),
                (TX + mm(8) + diamond_r, y),
                (TX + mm(8), y + diamond_r),
                (TX + mm(8) - diamond_r, y),
            ],
            fill=(*BRASS, 220),
        )
        td.text(
            (TX + mm(11.5), y),
            item,
            font=font_benefit,
            fill=(*LIGHT_OLIVE, 255),
            anchor="lm",
        )

    # QR для связи.
    qr_size = mm(19)
    qr_x = TX + TW - mm(7) - mm(21)
    qr_y = TY + mm(19.5)
    qr_panel = (qr_x, qr_y, qr_x + mm(21), qr_y + mm(21))
    panel = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle(
        qr_panel,
        radius=mm(1.4),
        fill=(*LIGHT_PAPER, 255),
        outline=(*BRASS, 120),
        width=max(1, mm(0.18)),
    )
    canvas.alpha_composite(panel)
    draw_qr(
        canvas,
        (qr_x + mm(1), qr_y + mm(1), qr_x + mm(1) + qr_size, qr_y + mm(1) + qr_size),
        ink=CARD_INK,
        paper=LIGHT_PAPER,
        logo=None,
    )
    # Панель уже нарисована поверх фона, QR — поверх панели.
    draw_tracking_at(
        td,
        "СВЯЗАТЬСЯ С НАМИ",
        font_tiny,
        pt(4.4) * 0.18,
        (*MUTED_ON_CREAM, 255),
        qr_x + mm(10.5),
        qr_y + mm(22.2),
        anchor="mm",
    )

    line_y = TY + TH - mm(10.8)
    td.line(
        (TX + mm(7), line_y, TX + TW - mm(7), line_y),
        fill=(*BRASS, 75),
        width=max(1, mm(0.12)),
    )

    contact_y = TY + TH - mm(8.2)
    td.text(
        (TX + mm(7), contact_y),
        "+998 77 131-11-11",
        font=font_small,
        fill=(*LIGHT_OLIVE, 255),
        anchor="lm",
    )
    td.text(
        (TX + TW - mm(7), contact_y),
        "@history.lounge",
        font=font_small,
        fill=(*BRASS, 255),
        anchor="rm",
    )

    draw_tracking_at(
        td,
        "VIP-СТАТУС ПРИ РАСХОДАХ ОТ 25 000 000 СУМ",
        font_tiny,
        pt(4.4) * 0.12,
        (*MUTED_ON_CREAM, 235),
        CX,
        TY + TH - mm(5.4),
        anchor="mm",
    )

    canvas.alpha_composite(text)
    return canvas


def make_preview(canvas: Image.Image) -> Image.Image:
    trim = canvas.crop((TX, TY, TX + TW, TY + TH))
    mask = Image.new("L", trim.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle(
        (0, 0, trim.width - 1, trim.height - 1),
        radius=CORNER_R,
        fill=255,
    )
    trim.putalpha(mask)
    return trim


def make_mockup(front: Image.Image, back: Image.Image) -> Image.Image:
    width, height = 1800, 1200
    canvas = vertical_gradient(width, height, (48, 44, 33), (14, 13, 10)).convert(
        "RGBA"
    )

    glow = radial_glow(1500, CARD_BRASS, 0.16)
    canvas.alpha_composite(glow, (120, -260))

    rng = random.Random(31)
    bokeh = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bokeh)
    for _ in range(34):
        x = rng.randint(-80, width + 80)
        y = rng.randint(-40, 760)
        radius = rng.randint(20, 120)
        color = rng.choice([(195, 153, 92), (147, 128, 82), (225, 188, 126)])
        bd.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(*color, rng.randint(7, 24)),
        )
    bokeh = bokeh.filter(ImageFilter.GaussianBlur(30))
    canvas.alpha_composite(bokeh)

    noise = Image.effect_noise((width, height), 16).convert("L")
    canvas.alpha_composite(
        Image.merge(
            "RGBA", (noise, noise, noise, Image.new("L", (width, height), 6))
        )
    )

    back_quad = [
        (940.0, 370.0),
        (1590.0, 342.0),
        (1615.0, 765.0),
        (965.0, 793.0),
    ]
    front_quad = [
        (190.0, 392.0),
        (890.0, 362.0),
        (915.0, 807.0),
        (215.0, 837.0),
    ]

    def paste_card(card: Image.Image, quad: list[tuple[float, float]]) -> None:
        shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle(
            (0, 0, card.width - 1, card.height - 1),
            radius=CORNER_R,
            fill=(0, 0, 0, 125),
        )
        shadow_quad = [(x + 8, y + 22) for x, y in quad]
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        perspective_paste(shadow_layer, shadow, shadow_quad)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(26))
        canvas.alpha_composite(shadow_layer)
        perspective_paste(canvas, card, quad)

    paste_card(back, back_quad)
    paste_card(front, front_quad)

    # Мягкий блик по верхним кромкам.
    highlight = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.line([front_quad[0], front_quad[1]], fill=(241, 226, 198, 75), width=2)
    hd.line([back_quad[0], back_quad[1]], fill=(241, 226, 198, 55), width=2)
    highlight = highlight.filter(ImageFilter.GaussianBlur(1.5))
    canvas.alpha_composite(highlight)

    # Подпись презентации.
    caption = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    cd = ImageDraw.Draw(caption)
    font_caption = ImageFont.truetype(FONT_PATH, 22, index=FONT_LIGHT)
    font_sub = ImageFont.truetype(FONT_PATH, 13, index=FONT_LIGHT)
    draw_tracking_at(
        cd,
        "HISTORY LOUNGE",
        font_caption,
        9,
        (*CARD_BRASS_LIGHT, 235),
        width / 2,
        1065,
        anchor="mm",
    )
    cd.line((width / 2 - 180, 1090, width / 2 + 180, 1090), fill=(*BRASS, 90), width=1)
    draw_tracking_at(
        cd,
        "VIP CARD · 25 000 000+",
        font_sub,
        4,
        (*CREAM, 185),
        width / 2,
        1115,
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
            outline=int(85 * t**2),
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

    front_path = ASSETS / "vip_card_front.png"
    front.save(front_path, "PNG", optimize=True)

    back_path = ASSETS / "vip_card_back.png"
    back.save(back_path, "PNG", optimize=True)

    pdf_path = ASSETS / "vip_card_print.pdf"
    front_canvas.convert("RGB").save(
        pdf_path,
        "PDF",
        resolution=600,
        save_all=True,
        append_images=[back_canvas.convert("RGB")],
    )

    mockup = make_mockup(front, back)
    mockup_path = ASSETS / "vip_card_mockup.jpg"
    mockup.save(mockup_path, "JPEG", quality=94, optimize=True)

    for path in (front_path, back_path, pdf_path, mockup_path):
        print(f"Готово: {path} ({path.stat().st_size // 1024} КБ)")


if __name__ == "__main__":
    main()
