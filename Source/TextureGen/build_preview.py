#!/usr/bin/env python3
"""Rebuilds the texture overview, promo/TexturePreview.png, from the textures
already on disk.

This used to be the mod's About/Preview.png. That is now the banner in
Source/Promo, so this writes to promo/ (gitignored) instead of over it.
Much faster than generate_textures.py, which redraws everything from scratch.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pnglib import read_png  # noqa: E402
import preview  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEX = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Buildings")

# Preview slot -> the texture that represents it.
SOURCES = {
    "KnuckleboneMat": "KnuckleboneMat.png",
    "ShadowLanternTheater": "ShadowLanternTheaterPlaySouth_4.png",
    "SoakingTub": "SoakingTub_south.png",
    "KaraokeMachine": "KaraokeMachine_south.png",
    "Aquarium": "Aquarium_south.png",
    "GravballCourt": "GravballCourt_south.png",
    "SkittlesLane": "SkittlesLane_south.png",
    "CocktailArcade": "CocktailArcade_south.png",
    "MassageChair": "MassageChair_south.png",
    "HologamePod": "HologamePod_south.png",
    "VistaDay": "VistaPanel3Day_2.png",
    "PinballClassic": "PinballClassic_south.png",
    "PinballBoomalope": "PinballBoomalope_south.png",
    "PinballMechRampage": "PinballMechRampage_south.png",
    "PinballArchotech": "PinballArchotech_south.png",
    "DreamloopHolotheater": "DreamloopHolotheater_south.png",
    "DreamloopProjection": "DreamloopProjection_4.png",
}


def trim_sides(px, w, h):
    """Drop fully transparent columns either side. The pinball textures are
    saved square so the side views can stand taller than their footprint, which
    leaves the end views centred between empty margins."""
    def empty(x):
        return all(px[(y * w + x) * 4 + 3] == 0 for y in range(h))
    x0, x1 = 0, w
    while x0 < x1 - 1 and empty(x0):
        x0 += 1
    while x1 - 1 > x0 and empty(x1 - 1):
        x1 -= 1
    out = bytearray()
    for y in range(h):
        out += px[(y * w + x0) * 4:(y * w + x1) * 4]
    return out, x1 - x0, h


def main():
    sprites = {}
    for key, filename in SOURCES.items():
        px, w, h = read_png(os.path.join(TEX, filename))
        if key.startswith("Pinball"):
            px, w, h = trim_sides(px, w, h)
        sprites[key] = (px, w, h)
    out = os.path.join(ROOT, "promo")
    os.makedirs(out, exist_ok=True)
    preview.build(sprites, os.path.join(out, "TexturePreview.png"))


if __name__ == "__main__":
    main()
