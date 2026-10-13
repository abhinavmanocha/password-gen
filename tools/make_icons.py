#!/usr/bin/env python3
"""Draw the app icons (web PWA + Android mipmaps).

Run with the interpreter that has Pillow:  python tools/make_icons.py
Android mipmaps are only written when ../mobile/android exists.
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB_ICONS = os.path.join(ROOT, "icons")

TOP = (126, 152, 255)     # #7e98ff
BOTTOM = (74, 92, 214)    # #4a5cd6
INK = (255, 255, 255, 255)
SS = 4                    # supersample factor for smooth edges


def lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def keyhole(size: int, span: float) -> Image.Image:
    """Transparent tile with a white keyhole, art occupying `span` of the canvas."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size * span
    cx = cy = size / 2
    r = s * 0.155
    head_y = cy - s * 0.085
    d.ellipse([cx - r, head_y - r, cx + r, head_y + r], fill=INK)
    top_w, bot_w = r * 0.5, r * 1.1
    bot_y = cy + s * 0.23
    d.polygon([(cx - top_w, head_y + r * 0.2), (cx + top_w, head_y + r * 0.2),
               (cx + bot_w, bot_y), (cx - bot_w, bot_y)], fill=INK)
    return img


def tile(size: int, radius_ratio: float = 0.22) -> Image.Image:
    """Rounded square with the brand gradient and the keyhole centred on it."""
    big = size * SS
    bg = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    grad = Image.new("RGBA", (big, big))
    gd = ImageDraw.Draw(grad)
    for y in range(big):
        t = y / (big - 1)
        gd.line([(0, y), (big, y)], fill=(lerp(TOP[0], BOTTOM[0], t),
                                          lerp(TOP[1], BOTTOM[1], t),
                                          lerp(TOP[2], BOTTOM[2], t), 255))
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, big - 1, big - 1],
                                           radius=int(big * radius_ratio), fill=255)
    bg.paste(grad, (0, 0), mask)
    bg.alpha_composite(keyhole(big, 0.66))
    return bg.resize((size, size), Image.LANCZOS)


def foreground(size: int) -> Image.Image:
    """Adaptive-icon foreground: keyhole only, inside the 66% safe zone."""
    big = size * SS
    img = keyhole(big, 0.42)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    os.makedirs(WEB_ICONS, exist_ok=True)
    tile(192).save(os.path.join(WEB_ICONS, "icon-192.png"))
    tile(512).save(os.path.join(WEB_ICONS, "icon-512.png"))

    # maskable icons get cropped to a circle: keep the art inside the safe zone
    big = 512 * SS
    maskable = Image.new("RGBA", (big, big), BOTTOM + (255,))
    maskable.alpha_composite(keyhole(big, 0.40))
    maskable.resize((512, 512), Image.LANCZOS).save(
        os.path.join(WEB_ICONS, "icon-maskable-512.png"))
    print("wrote", WEB_ICONS)

    res = os.path.join(ROOT, "mobile", "android", "app", "src", "main", "res")
    if not os.path.isdir(res):
        print("no android project at", res, "- skipping mipmaps")
        return

    # (folder, legacy launcher px, adaptive foreground px)
    densities = [("mdpi", 48, 108), ("hdpi", 72, 162), ("xhdpi", 96, 216),
                 ("xxhdpi", 144, 324), ("xxxhdpi", 192, 432)]
    for folder, legacy_px, fg_px in densities:
        out = os.path.join(res, "mipmap-" + folder)
        os.makedirs(out, exist_ok=True)
        icon = tile(legacy_px)
        icon.save(os.path.join(out, "ic_launcher.png"))
        icon.save(os.path.join(out, "ic_launcher_round.png"))
        foreground(fg_px).save(os.path.join(out, "ic_launcher_foreground.png"))
        print("wrote", out)

    # adaptive-icon background colour (referenced by mipmap-anydpi-v26/ic_launcher.xml)
    values = os.path.join(res, "values")
    os.makedirs(values, exist_ok=True)
    with open(os.path.join(values, "ic_launcher_background.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<resources>\n'
                 '    <color name="ic_launcher_background">#4a5cd6</color>\n'
                 '</resources>\n')
    print("wrote", os.path.join(values, "ic_launcher_background.xml"))


if __name__ == "__main__":
    if sys.version_info < (3, 9):
        sys.exit("needs Python 3.9+")
    main()
