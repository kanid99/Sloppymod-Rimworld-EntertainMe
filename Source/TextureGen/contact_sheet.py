#!/usr/bin/env python3
"""Lays every shipped texture out on one labelled sheet, for eyeballing the art
without launching the game.

    python3 Source/TextureGen/contact_sheet.py [output.png]

Reads the PNGs in Textures/ as they are, so what you see is what the game gets.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pnglib import Canvas, read_png  # noqa: E402
import preview  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEX = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Buildings")

# (heading, [filenames]) - animation strips are sampled, not shown in full.
SECTIONS = [
    ("KNUCKLEBONE MAT  NEOLITHIC", ["KnuckleboneMat.png"]),
    ("SHADOW LANTERN THEATER  MEDIEVAL  2X1",
     ["ShadowLanternTheater_south.png", "ShadowLanternTheater_east.png"]),
    ("SHADOW THEATER  SHADOWS WALKING",
     ["ShadowLanternTheaterPlaySouth_0.png", "ShadowLanternTheaterPlaySouth_3.png",
      "ShadowLanternTheaterPlaySouth_6.png", "ShadowLanternTheaterPlaySouth_9.png"]),
    ("PINBALL CABINETS  1X3  INDUSTRIAL TO SPACER",
     ["PinballClassic_south.png", "PinballBoomalope_south.png",
      "PinballMechRampage_south.png", "PinballArchotech_south.png",
      "PinballClassic_east.png"]),
    ("COCKTAIL ARCADE TABLE  INDUSTRIAL  SEATS TWO", ["CocktailArcade_south.png"]),
    ("ARCADE SCREEN  RUNS WHILE PLAYED",
     ["CocktailArcadeScreenSouth_0.png", "CocktailArcadeScreenSouth_4.png",
      "CocktailArcadeScreenSouth_8.png", "CocktailArcadeScreenSouth_12.png"]),
    ("MASSAGE CHAIR  INDUSTRIAL  PAWNS SIT IN IT",
     ["MassageChair_south.png", "MassageChair_east.png",
      "MassageChairRollers_0.png", "MassageChairRollers_4.png"]),
    ("HOLOGAME POD  SPACER", ["HologamePod_south.png", "HologamePod_east.png"]),
    ("VISTA PANEL  SPACER  3X1  OFF AND BY TIME OF DAY",
     ["VistaPanel3_south.png", "VistaPanel3Dawn_0.png", "VistaPanel3Day_2.png",
      "VistaPanel3Dusk_2.png", "VistaPanel3Night_1.png"]),
    ("DREAMLOOP HOLOTHEATER  ULTRA  3X1",
     ["DreamloopHolotheater_south.png", "DreamloopHolotheater_east.png"]),
    ("SOAKING TUB  MEDIEVAL  WOOD FIRED  PAWNS GET IN",
     ["SoakingTub.png", "SoakingTubSteam_1.png", "SoakingTubSteam_4.png"]),
    ("AQUARIUM  INDUSTRIAL  2X1",
     ["Aquarium_south.png", "AquariumLife_0.png", "AquariumLife_4.png"]),
    ("SKITTLES LANE  MEDIEVAL  1X5",
     ["SkittlesLane_south.png", "SkittlesLaneRoll_2.png", "SkittlesLaneRoll_5.png"]),
    ("KARAOKE MACHINE  INDUSTRIAL  A CROWD GATHERS",
     ["KaraokeMachine_south.png", "KaraokeMachineSing_1.png", "KaraokeMachineSing_4.png"]),
    ("GRAVBALL COURT  ULTRA  3X3",
     ["GravballCourt_south.png", "GravballPlay_0.png", "GravballPlay_3.png"]),
    ("PINBALL IN PLAY  BALL AND LAMPS  SHARED BY ALL FOUR TABLES",
     ["PinballPlay_0.png", "PinballPlay_3.png", "PinballPlay_5.png", "PinballPlay_7.png"]),
    ("DREAMLOOP  PICTURE THROWN ON A WALL",
     ["DreamloopProjection_0.png", "DreamloopProjection_4.png",
      "DreamloopProjection_8.png"]),
]

WIDTH = 1180
PAD = 18
CELL_H = 132            # tallest a sprite is drawn
LABEL_H = 22


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "contact_sheet.png")

    loaded = []
    for heading, names in SECTIONS:
        sprites = []
        for name in names:
            path = os.path.join(TEX, name)
            if not os.path.isfile(path):
                print("  missing: %s" % name)
                continue
            sprites.append((name, read_png(path)))
        if sprites:
            loaded.append((heading, sprites))

    height = PAD
    for _, sprites in loaded:
        height += LABEL_H + CELL_H + PAD

    c = Canvas(WIDTH, height, ss=1)
    c.rect(0, 0, WIDTH, height, (26, 28, 35, 255))

    y = PAD
    for heading, sprites in loaded:
        c.rect(0, y - 6, WIDTH, y + LABEL_H - 8, (34, 37, 46, 255))
        c.rect(0, y - 6, 4, y + LABEL_H - 8, (232, 198, 78, 255))
        preview.text(c, heading, 14, y - 2, 2, (226, 224, 232, 255))
        y += LABEL_H

        x = 14
        for name, (px, sw, sh) in sprites:
            scale = min(CELL_H / float(sh), 300.0 / sw)
            w, h = sw * scale, sh * scale
            c.rect(x - 4, y - 2, x + w + 4, y + h + 2, (18, 19, 24, 255), 5)
            preview.blit(c, px, sw, sh, x, y + (CELL_H - h) / 2 - 2, scale)
            x += w + 26
        y += CELL_H + PAD

    c.save(out_path)
    print("Wrote %s (%dx%d)" % (out_path, WIDTH, height))


if __name__ == "__main__":
    main()
