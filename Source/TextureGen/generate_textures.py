#!/usr/bin/env python3
"""Generates every texture used by Entertaining Ideas.

Run from anywhere:  python3 Source/TextureGen/generate_textures.py
Output lands in Textures/EntertainingIdeas/Buildings/.

Art is drawn top-down to match RimWorld's camera. Rotatable buildings get the
four _north/_east/_south/_west files a Graphic_Multi needs; since these objects
read the same from every side when seen from above, the rotations are true
90-degree turns of the south-facing art rather than redrawn views.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pnglib import Canvas, rotate, write_png  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Buildings")

DARK = (26, 22, 20, 255)          # shared outline colour


def save_rotations(canvas, name):
    """Write _south/_east/_north/_west from one south-facing drawing."""
    px, w, h = canvas.pixels(), canvas.w, canvas.h
    for turns, suffix in ((0, "south"), (1, "west"), (2, "north"), (3, "east")):
        rp, rw, rh = rotate(px, w, h, turns)
        write_png(os.path.join(OUT, "%s_%s.png" % (name, suffix)), rw, rh, rp)
    print("  %s_{north,east,south,west}.png  (%dx%d)" % (name, w, h))


def save_single(canvas, name):
    canvas.save(os.path.join(OUT, "%s.png" % name))
    print("  %s.png  (%dx%d)" % (name, canvas.w, canvas.h))


# ---------------------------------------------------------------------------
# 1. Knucklebone mat  (neolithic, 1x1, non-rotatable)
# ---------------------------------------------------------------------------
def knucklebone_mat():
    c = Canvas(128, 128)
    hide = (150, 118, 84, 255)
    hide_dark = (118, 90, 62, 255)

    # Ragged hide, built from overlapping ellipses so the edge isn't a circle.
    c.ellipse(64, 66, 52, 46, DARK)
    for cx, cy, rx, ry in ((44, 52, 26, 22), (86, 58, 24, 21), (60, 92, 30, 20)):
        c.ellipse(cx, cy, rx + 2, ry + 2, DARK)
    c.ellipse(64, 66, 49, 43, hide_dark)
    for cx, cy, rx, ry in ((44, 52, 24, 20), (86, 58, 22, 19), (60, 92, 28, 18)):
        c.ellipse(cx, cy, rx, ry, hide_dark)
    c.ellipse(64, 64, 44, 39, hide)

    # Stitched border.
    for i in range(22):
        import math
        a = i / 22.0 * 2 * math.pi
        c.line(64 + math.cos(a) * 44, 64 + math.sin(a) * 39,
               64 + math.cos(a) * 40, 64 + math.sin(a) * 35, (92, 68, 46, 210), 2.4)

    # Scattered knucklebones: a shaft with a knob at each end.
    bones = ((48, 52, 18), (72, 46, -24), (58, 74, 40), (82, 70, 8), (66, 92, -12))
    for bx, by, ang in bones:
        import math
        r = math.radians(ang)
        dx, dy = math.cos(r) * 9, math.sin(r) * 9
        c.line(bx - dx, by - dy, bx + dx, by + dy, DARK, 9)
        c.circle(bx - dx, by - dy, 5.5, DARK)
        c.circle(bx + dx, by + dy, 5.5, DARK)
        c.line(bx - dx, by - dy, bx + dx, by + dy, (238, 230, 209, 255), 6)
        c.circle(bx - dx, by - dy, 4.2, (238, 230, 209, 255))
        c.circle(bx + dx, by + dy, 4.2, (238, 230, 209, 255))
        c.circle(bx + dx - 1, by + dy - 1, 1.6, (176, 166, 146, 255))

    # Two wager stones.
    for sx, sy in ((36, 82), (92, 88)):
        c.circle(sx, sy, 6.5, DARK)
        c.circle(sx, sy, 5.2, (122, 122, 128, 255))
        c.circle(sx - 1.4, sy - 1.4, 2.4, (158, 158, 164, 255))
    save_single(c, "KnuckleboneMat")
    return c


# ---------------------------------------------------------------------------
# 2. Dartboard  (medieval, 1x1, rotatable)
# ---------------------------------------------------------------------------
def dartboard():
    c = Canvas(128, 128)
    cx, cy = 64, 60

    # Timber backing board.
    c.rect(18, 14, 110, 106, DARK, 6)
    c.rect(21, 17, 107, 103, (104, 74, 48, 255), 5)
    for x in range(26, 106, 13):
        c.line(x, 18, x, 102, (88, 62, 40, 190), 1.6)

    c.circle(cx, cy, 43, DARK)
    c.circle(cx, cy, 40, (24, 22, 24, 255))

    cream, black = (232, 216, 178, 255), (32, 30, 32, 255)
    red, green = (176, 44, 42, 255), (44, 126, 66, 255)
    for i in range(20):
        a0, a1 = i * 18, (i + 1) * 18
        base = cream if i % 2 == 0 else black
        c.wedge(cx, cy, 38, 24, a0, a1, base)
        c.wedge(cx, cy, 24, 8, a0, a1, base)
        c.wedge(cx, cy, 40, 38, a0, a1, red if i % 2 == 0 else green)   # doubles
        c.wedge(cx, cy, 25, 23, a0, a1, red if i % 2 == 0 else green)   # trebles
    c.circle(cx, cy, 8, green)
    c.circle(cx, cy, 4, red)
    c.ring(cx, cy, 40, 38.2, (14, 13, 14, 120))

    # Three darts, flights toward the player (south).
    for dx, dy, fx, fy, col in ((-9, -6, -26, 18, (214, 76, 62, 255)),
                                (6, -12, 22, 12, (76, 152, 206, 255)),
                                (11, 7, 30, 30, (232, 198, 78, 255))):
        c.line(cx + dx, cy + dy, cx + fx, cy + fy, DARK, 6)
        c.line(cx + dx, cy + dy, cx + fx, cy + fy, (198, 198, 206, 255), 3.4)
        c.poly([(cx + fx, cy + fy), (cx + fx - 7, cy + fy + 3),
                (cx + fx - 2, cy + fy + 10), (cx + fx + 5, cy + fy + 6)], DARK)
        c.poly([(cx + fx, cy + fy + 1), (cx + fx - 5, cy + fy + 3.5),
                (cx + fx - 2, cy + fy + 8), (cx + fx + 3.5, cy + fy + 5)], col)

    # Floor stand legs.
    c.rect(48, 104, 80, 114, DARK, 3)
    c.rect(50, 106, 78, 112, (86, 60, 38, 255), 2)
    save_rotations(c, "Dartboard")
    return c


# ---------------------------------------------------------------------------
# 3. Pinball machines  (four themed tables, 1x1 footprint, rotatable)
# ---------------------------------------------------------------------------
def pinball(name, cab, cab_dark, field, accent, accent2, glass, motif):
    """A 1x3 cabinet: backbox at the far end, playfield, lockbar at the player end."""
    c = Canvas(160, 480)
    L, R = 14, 146        # cabinet sides
    TOP, BOT = 8, 472
    mid = (L + R) / 2

    c.rect(L - 4, TOP - 4, R + 4, BOT + 4, DARK, 12)           # outline
    c.rect(L, TOP, R, BOT, cab_dark, 10)                       # cabinet
    c.rect(L, TOP, R, 120, DARK, 10)                           # backbox shell
    c.rect(L + 7, TOP + 8, R - 7, 112, glass, 6)               # backglass
    c.rect(L + 7, TOP + 8, R - 7, 44, (255, 255, 255, 46), 6)  # glass sheen
    motif(c, L, R, 28)                                         # theme art
    for i in range(6):                                          # marquee lamps
        c.circle(L + 16 + i * 21.6, 106, 3.4, (255, 244, 208, 230))

    # Playfield.
    c.rect(L + 5, 126, R - 5, BOT - 56, DARK, 6)
    c.rect(L + 8, 129, R - 8, BOT - 59, field, 5)
    c.rect(L + 8, 129, R - 8, 200, (255, 255, 255, 20), 5)

    # Plunger lane and a guide rail sweeping back up the playfield.
    c.line(R - 20, 142, R - 20, 330, (238, 238, 244, 150), 3)
    c.line(L + 18, 150, L + 18, 268, (238, 238, 244, 105), 2.4)

    # Drop target bank.
    for tx in range(3):
        c.rect(L + 30 + tx * 18, 156, L + 43 + tx * 18, 163, accent2, 2)

    # Pop bumpers.
    for bx, by, rr in ((mid - 20, 212, 17), (mid + 22, 196, 15), (mid - 2, 268, 14)):
        c.circle(bx, by, rr + 2, DARK)
        c.circle(bx, by, rr, accent)
        c.circle(bx, by, rr * 0.62, (250, 250, 252, 255))
        c.circle(bx, by, rr * 0.34, accent2)
        c.circle(bx - rr * 0.3, by - rr * 0.3, rr * 0.16, (255, 255, 255, 190))

    # Slingshots.
    c.poly([(L + 14, 372), (L + 42, 360), (L + 42, 382)], DARK)
    c.poly([(L + 17, 372), (L + 39, 363), (L + 39, 379)], accent2)
    c.poly([(R - 14, 372), (R - 42, 360), (R - 42, 382)], DARK)
    c.poly([(R - 17, 372), (R - 39, 363), (R - 39, 379)], accent2)

    # Flippers at the player end.
    for sx in (-1, 1):
        x0, x1 = mid + sx * 10, mid + sx * 36
        c.line(x0, 400, x1, 390, DARK, 13)
        c.line(x0, 400, x1, 390, accent, 9)
        c.circle(x0, 400, 4.5, (236, 236, 240, 255))

    # Ball and shooter rod.
    c.circle(R - 20, 348, 6.5, DARK)
    c.circle(R - 20, 348, 5.2, (226, 228, 236, 255))
    c.circle(R - 21.6, 346.4, 2.0, (255, 255, 255, 220))
    c.rect(R - 14, BOT - 60, R - 6, BOT - 34, DARK, 3)
    c.circle(R - 10, BOT - 34, 6.5, DARK)
    c.circle(R - 10, BOT - 34, 5, accent)

    # Lockbar with the flipper buttons.
    c.rect(L, BOT - 54, R, BOT, cab, 10)
    c.rect(L + 5, BOT - 48, R - 5, BOT - 8, cab_dark, 7)
    for bx in (L + 20, R - 20):
        c.circle(bx, BOT - 28, 6, DARK)
        c.circle(bx, BOT - 28, 4.4, accent2)
    c.rect(mid - 16, BOT - 36, mid + 16, BOT - 20, (24, 22, 26, 255), 3)   # coin door
    c.circle(mid, BOT - 28, 4, accent)

    # Side-rail highlight.
    c.frame(L, TOP, R, BOT, (255, 255, 255, 36), 2.5, 10)
    save_rotations(c, name)
    return c


def motif_classic(c, L, R, TOP):
    c.circle((L + R) / 2, TOP + 32, 20, (238, 232, 216, 255))
    c.circle((L + R) / 2, TOP + 32, 13, (198, 58, 52, 255))
    c.circle((L + R) / 2, TOP + 32, 6, (238, 232, 216, 255))
    for i in range(5):
        c.line(L + 14 + i * 5, TOP + 14, L + 8 + i * 5, TOP + 52, (255, 255, 255, 60), 3)
        c.line(R - 14 - i * 5, TOP + 14, R - 8 - i * 5, TOP + 52, (255, 255, 255, 60), 3)


def motif_boomalope(c, L, R, TOP):
    cx = (L + R) / 2
    c.circle(cx, TOP + 34, 22, (248, 176, 54, 220))
    c.circle(cx, TOP + 34, 14, (252, 226, 120, 240))
    c.ellipse(cx - 24, TOP + 36, 13, 9, (108, 158, 82, 255))   # boomalope body
    c.ellipse(cx - 33, TOP + 32, 6, 5, (128, 178, 96, 255))    # head
    c.circle(cx - 35, TOP + 31, 1.6, DARK)
    for i in range(8):                                          # blast rays
        import math
        a = math.radians(i * 45 + 12)
        c.line(cx + math.cos(a) * 22, TOP + 34 + math.sin(a) * 22,
               cx + math.cos(a) * 32, TOP + 34 + math.sin(a) * 32, (252, 214, 98, 190), 3)


def motif_mech(c, L, R, TOP):
    cx = (L + R) / 2
    c.poly([(cx, TOP + 12), (cx + 26, TOP + 34), (cx, TOP + 56), (cx - 26, TOP + 34)],
           (196, 62, 54, 230))
    c.rect(cx - 16, TOP + 24, cx + 16, TOP + 44, (72, 78, 88, 255), 3)   # mech chassis
    for i in (-1, 1):
        c.circle(cx + i * 8, TOP + 32, 4.4, (236, 92, 72, 255))          # eyes
        c.line(cx + i * 16, TOP + 44, cx + i * 24, TOP + 52, (72, 78, 88, 255), 5)
    c.rect(cx - 20, TOP + 46, cx + 20, TOP + 50, (48, 52, 60, 255), 2)


def motif_archotech(c, L, R, TOP):
    cx = (L + R) / 2
    for r, a in ((26, 70), (19, 110), (12, 160)):
        c.ring(cx, TOP + 34, r, r - 3, (128, 232, 226, a))
    c.circle(cx, TOP + 34, 8, (206, 250, 246, 235))
    c.poly([(cx, TOP + 10), (cx + 30, TOP + 34), (cx, TOP + 58), (cx - 30, TOP + 34)],
           (168, 116, 232, 90))
    for i in range(6):
        import math
        a = math.radians(i * 60)
        c.line(cx, TOP + 34, cx + math.cos(a) * 28, TOP + 34 + math.sin(a) * 28,
               (196, 246, 240, 70), 2)


# ---------------------------------------------------------------------------
# 4. Hologame pod  (spacer, 1x1, rotatable)
# ---------------------------------------------------------------------------
def hologame_pod():
    c = Canvas(256, 256)
    cx, cy = 128, 128

    c.circle(cx, cy, 104, DARK)
    c.circle(cx, cy, 100, (62, 68, 82, 255))            # plinth
    c.ring(cx, cy, 100, 86, (86, 94, 112, 255))
    c.ring(cx, cy, 88, 84, (40, 44, 54, 255))
    for i in range(12):                                  # vents
        import math
        a = math.radians(i * 30 + 15)
        c.line(cx + math.cos(a) * 86, cy + math.sin(a) * 86,
               cx + math.cos(a) * 98, cy + math.sin(a) * 98, (34, 38, 46, 255), 6)

    c.circle(cx, cy, 82, (22, 26, 34, 255))              # emitter well
    c.circle(cx, cy, 74, (30, 92, 104, 255))
    c.circle(cx, cy, 62, (58, 168, 178, 235))
    c.circle(cx, cy, 44, (126, 226, 230, 220))

    # Projected game board hovering above the well.
    c.poly([(cx, cy - 46), (cx + 46, cy), (cx, cy + 46), (cx - 46, cy)], (220, 252, 252, 120))
    for i in (-1, 1):
        c.poly([(cx + i * 16, cy - 20), (cx + i * 34, cy), (cx + i * 16, cy + 20), (cx - i * 2, cy)],
               (236, 255, 255, 150))
    c.circle(cx, cy, 9, (255, 255, 255, 230))
    for i in range(8):
        import math
        a = math.radians(i * 45)
        c.circle(cx + math.cos(a) * 56, cy + math.sin(a) * 56, 4.5, (198, 248, 250, 200))

    # Control shelf on the south face, where the pawn stands.
    c.rect(cx - 40, cy + 84, cx + 40, cy + 112, DARK, 8)
    c.rect(cx - 36, cy + 88, cx + 36, cy + 108, (74, 82, 98, 255), 6)
    for i in range(4):
        c.circle(cx - 24 + i * 16, cy + 98, 4.6, (128, 226, 228, 245))
    save_rotations(c, "HologamePod")
    return c


# ---------------------------------------------------------------------------
# 5. Dreamloop holotheater  (ultratech, 3x1, rotatable)
# ---------------------------------------------------------------------------
def dreamloop_holotheater():
    c = Canvas(384, 128)

    c.rect(10, 30, 374, 104, DARK, 12)
    c.rect(14, 34, 370, 100, (48, 46, 66, 255), 10)     # housing
    c.rect(14, 34, 370, 58, (66, 62, 90, 255), 10)
    c.frame(14, 34, 370, 100, (150, 140, 196, 60), 2.5, 10)

    # Emitter lenses along the front edge.
    for i in range(5):
        lx = 58 + i * 68
        c.ellipse(lx, 72, 22, 17, DARK)
        c.ellipse(lx, 72, 19, 14, (30, 30, 46, 255))
        c.ellipse(lx, 72, 14, 10, (122, 96, 210, 235))
        c.ellipse(lx, 72, 7, 5, (216, 206, 255, 245))
        c.ellipse(lx - 3, 69, 3, 2, (255, 255, 255, 220))

    # Projection spilling south, toward the viewers.
    c.poly([(40, 100), (344, 100), (368, 126), (16, 126)], (148, 122, 226, 70))
    c.poly([(84, 100), (300, 100), (316, 122), (68, 122)], (190, 172, 246, 70))
    for i in range(7):
        x = 56 + i * 46
        c.line(x, 102, x - 8, 126, (226, 216, 255, 55), 5)

    # Status strip and heat fins on the back.
    c.rect(150, 40, 234, 50, (26, 26, 40, 255), 4)
    for i in range(6):
        c.circle(162 + i * 12, 45, 3.2, (150, 226, 236, 230))
    for i in range(10):
        c.line(30 + i * 34, 36, 30 + i * 34, 44, (32, 32, 48, 200), 4)
    save_rotations(c, "DreamloopHolotheater")
    return c


# ---------------------------------------------------------------------------
# 6. Cocktail arcade table  (industrial, 1x1, two seats)
# ---------------------------------------------------------------------------
def cocktail_arcade():
    c = Canvas(160, 160)
    cx = cy = 80

    c.rect(10, 10, 150, 150, DARK, 20)
    c.rect(14, 14, 146, 146, (52, 48, 58, 255), 18)        # vinyl-edged table
    c.rect(20, 20, 140, 140, (34, 32, 40, 255), 14)
    c.frame(20, 20, 140, 140, (150, 146, 168, 70), 2, 14)

    # Glass screen, face up.
    c.rect(30, 30, 130, 130, (10, 10, 16, 255), 8)
    c.frame(30, 30, 130, 130, (86, 92, 118, 220), 2.5, 8)

    maze = (70, 104, 226, 255)
    c.frame(37, 37, 123, 123, maze, 2.5, 5)                # maze walls
    c.frame(48, 48, 78, 68, maze, 2.5, 3)
    c.frame(84, 48, 112, 68, maze, 2.5, 3)
    c.frame(48, 92, 78, 112, maze, 2.5, 3)
    c.frame(84, 92, 112, 112, maze, 2.5, 3)
    c.rect(72, 74, 90, 86, maze, 3)                        # ghost pen
    c.rect(75, 77, 87, 83, (10, 10, 16, 255), 2)

    for x in range(43, 122, 11):                           # pellets
        for y in (42, 118):
            c.circle(x, y, 2.2, (248, 236, 198, 255))
    for y in range(53, 112, 11):
        for x in (42, 118):
            c.circle(x, y, 2.2, (248, 236, 198, 255))
    for px, py in ((42, 42), (118, 42), (42, 118), (118, 118)):
        c.circle(px, py, 4.6, (250, 228, 160, 255))        # power pellets

    # The muncher, mouth open toward the pellets.
    c.circle(58, 80, 11, (246, 214, 62, 255))
    c.poly([(58, 80), (70, 73), (70, 87)], (10, 10, 16, 255))

    # Two ghosts.
    for gx, gy, col in ((96, 62, (226, 74, 70, 255)), (104, 96, (238, 150, 196, 255))):
        c.ellipse(gx, gy - 2, 9, 9, col)
        c.rect(gx - 9, gy - 2, gx + 9, gy + 7, col)
        for i in range(3):
            c.circle(gx - 6 + i * 6, gy + 7, 3, col)
        for i in (-1, 1):
            c.circle(gx + i * 4, gy - 3, 3.2, (246, 246, 252, 255))
            c.circle(gx + i * 4 + i, gy - 3, 1.6, (36, 44, 120, 255))

    # Control clusters on the two seating sides (north and south).
    for sy in (24, 136):
        c.rect(cx - 26, sy - 7, cx + 26, sy + 7, DARK, 6)
        c.rect(cx - 23, sy - 5, cx + 23, sy + 5, (68, 64, 78, 255), 5)
        c.circle(cx - 12, sy, 4.6, (28, 26, 32, 255))      # joystick ball
        c.circle(cx - 12, sy, 3.2, (214, 70, 62, 255))
        for i in range(2):
            c.circle(cx + 6 + i * 11, sy, 3.4, (236, 196, 76, 255))
    c.rect(cx + 44, cy - 10, cx + 52, cy + 10, (28, 26, 32, 255), 3)   # coin slot
    save_single(c, "CocktailArcade")
    return c


def main():
    os.makedirs(OUT, exist_ok=True)
    print("Writing textures to %s" % OUT)
    made = {}
    made["KnuckleboneMat"] = knucklebone_mat()
    made["Dartboard"] = dartboard()
    made["PinballClassic"] = pinball(
        "PinballClassic",
        cab=(178, 52, 48, 255), cab_dark=(126, 36, 34, 255), field=(28, 62, 96, 255),
        accent=(232, 198, 78, 255), accent2=(214, 76, 62, 255), glass=(46, 40, 72, 255),
        motif=motif_classic)
    made["PinballBoomalope"] = pinball(
        "PinballBoomalope",
        cab=(96, 142, 72, 255), cab_dark=(66, 100, 52, 255), field=(34, 58, 38, 255),
        accent=(248, 176, 54, 255), accent2=(226, 106, 44, 255), glass=(40, 56, 34, 255),
        motif=motif_boomalope)
    made["PinballMechRampage"] = pinball(
        "PinballMechRampage",
        cab=(96, 102, 114, 255), cab_dark=(64, 70, 80, 255), field=(30, 32, 40, 255),
        accent=(214, 74, 62, 255), accent2=(236, 154, 60, 255), glass=(34, 38, 48, 255),
        motif=motif_mech)
    made["PinballArchotech"] = pinball(
        "PinballArchotech",
        cab=(74, 58, 112, 255), cab_dark=(48, 38, 78, 255), field=(22, 20, 38, 255),
        accent=(126, 232, 226, 255), accent2=(186, 138, 246, 255), glass=(30, 24, 56, 255),
        motif=motif_archotech)
    made["CocktailArcade"] = cocktail_arcade()
    made["HologamePod"] = hologame_pod()
    made["DreamloopHolotheater"] = dreamloop_holotheater()

    import preview
    about = os.path.join(ROOT, "About")
    os.makedirs(about, exist_ok=True)
    preview.build({k: (v.pixels(), v.w, v.h) for k, v in made.items()},
                  os.path.join(about, "Preview.png"))
    print("Done.")


if __name__ == "__main__":
    main()
