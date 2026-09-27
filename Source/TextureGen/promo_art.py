#!/usr/bin/env python3
"""Builds the promo graphics used for release posts, from the shipped textures.

    python3 Source/TextureGen/promo_art.py [output_dir]

Output defaults to promo/ in the repo root, which is gitignored - these are
marketing images, not mod content. Everything is composed from the PNGs the
game actually loads, so a promo image can never show art the mod does not have.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pnglib import Canvas, read_png, rotate  # noqa: E402
import preview  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEX = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Buildings")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "promo")
BG, PANEL, INK, DIM, GOLD = (28,30,38,255), (38,41,51,255), (238,236,242,255), (150,156,172,255), (232,198,78,255)

def img(name):
    return read_png(os.path.join(TEX, name))

def place(c, name, x, y, box_w, box_h, overlay=None, oscale=None):
    px, w, h = img(name)
    s = min(box_w / float(w), box_h / float(h))
    dx, dy = x + (box_w - w*s)/2, y + (box_h - h*s)/2
    preview.blit(c, px, w, h, dx, dy, s)
    if overlay:
        op, ow, oh = img(overlay)
        os_ = s if oscale is None else s * oscale
        preview.blit(c, op, ow, oh, x + (box_w - ow*os_)/2, y + (box_h - oh*os_)/2, os_)
    return s

def header(c, W, title, sub):
    c.rect(0, 0, W, 104, (22,24,31,255))
    c.rect(0, 102, W, 106, GOLD)
    preview.text(c, title, (W - preview.text_width(title, 5))/2, 22, 5, INK)
    preview.text(c, sub, (W - preview.text_width(sub, 2))/2, 72, 2, DIM)

def section(c, W, y, label):
    c.rect(20, y, W-20, y+22, PANEL, 4)
    c.rect(20, y, 24, y+22, GOLD, 2)
    preview.text(c, label, 36, y+5, 2, INK)
    return y + 30

# ---------------------------------------------------------------- 1. lineup
def lineup():
    W = 1200
    c = Canvas(W, 760, ss=1)
    c.rect(0, 0, W, 760, BG)
    header(c, W, "ENTERTAINING IDEAS", "13 RECREATION IDEAS - 17 BUILDINGS - NEOLITHIC TO ARCHOTECH")

    rows = [
        ("NEOLITHIC AND MEDIEVAL - NO POWER NO RESEARCH",
         [("KnuckleboneMat.png", "KNUCKLEBONES"), ("ShadowLanternTheaterPlaySouth_4.png", "SHADOW THEATER"),
          ("SoakingTub_south.png", "SOAKING TUB"), ("SkittlesLane_south.png", "SKITTLES LANE")]),
        ("INDUSTRIAL",
         [("PinballClassic_south.png", "PINBALL"), ("PinballBoomalope_south.png", "BOOMALOPE BLITZ"),
          ("PinballMechRampage_south.png", "MECH RAMPAGE"), ("CocktailArcade_south.png", "COCKTAIL ARCADE"),
          ("MassageChair_south.png", "MASSAGE CHAIR"), ("Aquarium_south.png", "AQUARIUM"),
          ("KaraokeMachine_south.png", "KARAOKE"), ("SoakingTubElectric_south.png", "HEATED TUB")]),
        ("SPACER AND ULTRA",
         [("PinballArchotech_south.png", "DREAMTABLE"), ("HologamePod_south.png", "HOLOGAME POD"),
          ("VistaPanel3Day_2.png", "VISTA PANEL"), ("DreamloopHolotheater_south.png", "HOLOTHEATER"),
          ("GravballCourt_south.png", "GRAVBALL COURT")]),
    ]
    y = 120
    for label, items in rows:
        y = section(c, W, y, label)
        slot = (W - 40) / float(len(items))
        for i, (fname, cap) in enumerate(items):
            x = 20 + i * slot
            place(c, fname, x, y, slot - 12, 148)
            preview.text(c, cap, x + (slot - preview.text_width(cap, 1))/2, y + 152, 1, DIM)
        y += 182
    c.save(os.path.join(OUT, 'post_1_lineup.png'))
    print("post_1_lineup.png")

# ------------------------------------------------------------- 2. animation
def animation():
    W = 1200
    c = Canvas(W, 1085, ss=1)
    c.rect(0, 0, W, 1085, BG)
    header(c, W, "IT MOVES WHILE YOU PLAY IT",
           "ANIMATION RUNS ONLY WHILE A COLONIST IS USING IT AND THE POWER IS ON")

    y = section(c, W, 120, "PINBALL - THE BALL, ITS TRAIL, AND THE LAMPS IT JUST HIT")
    for i, f in enumerate(("0", "2", "4", "6")):
        place(c, "PinballClassic_south.png", 20 + i*140, y, 124, 290, overlay="PinballPlay_%s.png" % f)
    preview.text(c, "ARCADE TABLE - THE MAZE GAME RUNS DURING PLAY", 610, y + 6, 1, DIM)
    for i, f in enumerate(("0", "5", "10", "15")):
        place(c, "CocktailArcade_south.png", 610 + i*145, y + 26, 132, 132,
              overlay="CocktailArcadeScreenSouth_%s.png" % f)
    preview.text(c, "KARAOKE - LYRICS SCROLL, SPEAKERS PULSE", 610, y + 176, 1, DIM)
    for i, f in enumerate(("0", "2", "4")):
        place(c, "KaraokeMachine_south.png", 610 + i*130, y + 196, 118, 118,
              overlay="KaraokeMachineSingSouth_%s.png" % f)
    preview.text(c, "GRAVBALL - THE BALL ORBITS", 1000, y + 176, 1, DIM)
    for i, f in enumerate(("0", "3")):
        place(c, "GravballCourt_south.png", 1000 + i*100, y + 196, 95, 118,
              overlay="GravballPlay_%s.png" % f, oscale=0.42)

    y += 330
    y = section(c, W, y, "SKITTLES - NINE PINS, SEVEN TILES, THE BALL ROLLS THE LENGTH OF IT")
    # The lane is 1x7, so show it lying on its side the way it looks in game.
    captions = ("PINS STANDING, BALL WAITING", "BALL MID LANE", "PINS SCATTERED")
    for i, frame in enumerate(("0", "3", "5")):
        base, bw, bh = img("SkittlesLane_east.png")
        ov, ow, oh = img("SkittlesLaneRoll_%s.png" % frame)
        ov, ow, oh = rotate(ov, ow, oh, 3)      # south strip -> east, as the comp does
        s_ = (W - 60) / float(bw)
        yy = y + i * 172
        preview.blit(c, base, bw, bh, 30, yy, s_)
        preview.blit(c, ov, ow, oh, 30, yy, s_)
        preview.text(c, captions[i], 34, yy + 148, 1, DIM)
    c.save(os.path.join(OUT, 'post_2_animation.png'))
    print("post_2_animation.png")


# ----------------------------------------------------------------- 3. vista
def vista():
    W = 1200
    c = Canvas(W, 545, ss=1)
    c.rect(0, 0, W, 545, BG)
    header(c, W, "A WINDOW THAT IS NOT A WINDOW", "THE VISTA PANEL FOLLOWS THE LOCAL CLOCK AND EASES CABIN FEVER FOR THE ROOM")
    y = section(c, W, 120, "SAME PANEL - DAWN - DAYLIGHT - SUNSET - NIGHT")
    for i, (f, cap) in enumerate((("VistaPanel3Dawn_0.png", "DAWN"), ("VistaPanel3Day_2.png", "DAYLIGHT"),
                                  ("VistaPanel3Dusk_2.png", "SUNSET"), ("VistaPanel3Night_1.png", "NIGHT"))):
        x = 20 + i * 292
        place(c, f, x, y, 280, 100)
        preview.text(c, cap, x + 6, y + 104, 1, DIM)
    y += 150
    y = section(c, W, y, "DREAMLOOP HOLOTHEATER - FINDS A WALL AHEAD AND PROJECTS ONTO IT")
    place(c, "DreamloopHolotheater_south.png", 40, y, 420, 150)
    preview.text(c, "THE EMITTER", 40, y + 152, 1, DIM)
    for i, f in enumerate(("DreamloopProjection_0.png", "DreamloopProjection_6.png")):
        place(c, f, 520 + i*330, y, 310, 150)
    preview.text(c, "WHAT LANDS ON THE WALL", 520, y + 152, 1, DIM)
    c.save(os.path.join(OUT, 'post_3_vista.png'))
    print("post_3_vista.png")

# ------------------------------------------------------------------- 4. tub
def tub():
    W = 1000
    c = Canvas(W, 470, ss=1)
    c.rect(0, 0, W, 470, BG)
    header(c, W, "COLONISTS GET IN", "THE TUB PAINTS ITS WATERLINE OVER WHOEVER IS IN IT")
    y = 130
    def pawn_stack(x, mask, label):
        px, w, h = img('SoakingTub_south.png')
        s = 1.7
        preview.blit(c, px, w, h, x, y, s)
        p = Canvas(128, 128, ss=1)
        p.ellipse(64, 72, 17, 26, (86, 106, 156, 255))
        p.circle(64, 42, 15, (226, 186, 150, 255))
        p.rect(50, 94, 78, 116, (86, 106, 156, 255), 4)
        preview.blit(c, p.pixels(), 128, 128, x, y, s)
        if mask:
            for f in ('SoakingTubWaterSouth_2.png', 'SoakingTubSteam_2.png'):
                op, ow, oh = img(f)
                preview.blit(c, op, ow, oh, x, y, s)
        preview.text(c, label, x, y + 224, 1, DIM)
    pawn_stack(70, False, "WITHOUT THE WATERLINE")
    pawn_stack(330, True, "WITH IT")
    place(c, "SoakingTubElectric_south.png", 640, y, 200, 200)
    preview.text(c, "ELECTRIC VERSION", 640, y + 224, 1, DIM)
    for i, line in enumerate(["HOLDS ONE SOAK - A COLONIST CARRIES WATER OUT BETWEEN USES",
                              "PLUMB IT INTO DUBS BAD HYGIENE AND IT FILLS ITSELF",
                              "WOOD FIRED OR ELECTRIC - BOTH WARM THE ROOM"]):
        preview.text(c, line, 70, 392 + i*22, 1, INK if i == 0 else DIM)
    c.save(os.path.join(OUT, 'post_4_tub.png'))
    print("post_4_tub.png")

def main():
    os.makedirs(OUT, exist_ok=True)
    lineup()
    animation()
    vista()
    tub()
    print("Wrote promo images to %s" % OUT)


if __name__ == "__main__":
    main()
