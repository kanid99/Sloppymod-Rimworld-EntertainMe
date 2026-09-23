#!/usr/bin/env python3
"""Rebuilds About/Preview.png from the textures already on disk.

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
    "ShadowLanternTheater": "ShadowLanternTheaterPlay_4.png",
    "SoakingTub": "SoakingTub.png",
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


def main():
    sprites = {}
    for key, filename in SOURCES.items():
        px, w, h = read_png(os.path.join(TEX, filename))
        sprites[key] = (px, w, h)
    preview.build(sprites, os.path.join(ROOT, "About", "Preview.png"))


if __name__ == "__main__":
    main()
