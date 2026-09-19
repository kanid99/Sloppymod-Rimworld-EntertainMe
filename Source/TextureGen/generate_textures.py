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
# 2. Shadow lantern theater  (medieval, 2x1, watched by a crowd)
#
# Frames redraw the whole building rather than just the cloth, so the figures
# can walk off the edge of the screen without spilling onto the woodwork.
# ---------------------------------------------------------------------------

CLOTH = (26, 44, 230, 112)        # lit screen area


def shadow_figure(c, kind, x, base_y, scale, col):
    """Silhouettes cast on the cloth, drawn only where they overlap it."""
    import math
    x0, y0, x1, y1 = CLOTH
    if x < x0 - 30 or x > x1 + 30:
        return

    def body(px, py, rx, ry):
        left, right = max(px - rx, x0 + 1), min(px + rx, x1 - 1)
        if right <= left:
            return
        c.ellipse((left + right) / 2.0, py, (right - left) / 2.0, ry, col)

    if kind == "horse":
        body(x, base_y - 14 * scale, 15 * scale, 7 * scale)
        for i, dx in enumerate((-10, -4, 5, 11)):
            sway = math.sin(x * 0.12 + i) * 2.5 * scale
            c.line(x + dx * scale, base_y - 10 * scale,
                   x + dx * scale + sway, base_y, col, 3 * scale)
        c.line(x + 12 * scale, base_y - 18 * scale,
               x + 20 * scale, base_y - 26 * scale, col, 5 * scale)      # neck
        body(x + 22 * scale, base_y - 28 * scale, 6 * scale, 4 * scale)  # head
        c.line(x - 15 * scale, base_y - 18 * scale,
               x - 22 * scale, base_y - 24 * scale, col, 3 * scale)      # tail
    elif kind == "rider":
        body(x, base_y - 30 * scale, 5 * scale, 7 * scale)
        body(x, base_y - 40 * scale, 4 * scale, 4 * scale)
        c.line(x, base_y - 32 * scale, x + 9 * scale, base_y - 36 * scale, col, 3 * scale)
    else:  # bird
        c.line(x - 9 * scale, base_y, x, base_y - 5 * scale, col, 3 * scale)
        c.line(x, base_y - 5 * scale, x + 9 * scale, base_y, col, 3 * scale)
        body(x, base_y - 4 * scale, 3 * scale, 2 * scale)


def draw_shadow_theater(c, frame=None, total=10):
    import math
    x0, y0, x1, y1 = CLOTH
    step = 0 if frame is None else frame
    p = 0.0 if frame is None else float(frame) / total

    c.rect(4, 14, 252, 122, DARK, 10)                       # outer frame
    c.rect(7, 17, 249, 119, (104, 74, 46, 255), 8)

    flicker = 0 if frame is None else int(10 * math.sin(2 * math.pi * p * 3))
    cloth = (243 + flicker // 3, 222 + flicker // 2, 172 + flicker, 255)
    c.rect(x0, y0, x1, y1, (168, 140, 96, 255), 5)          # cloth, in its frame
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, cloth, 4)
    for gy in range(y0 + 4, y1 - 2, 6):                     # weave
        c.line(x0 + 3, gy, x1 - 3, gy, (214, 190, 142, 90), 1.6)

    # The procession: a horse and rider with birds above, walking right.
    shadow = (38, 26, 20, 235)
    travel = (x1 - x0) + 56
    lead = x0 - 26 + travel * p
    shadow_figure(c, "horse", lead, y1 - 8, 1.0, shadow)
    shadow_figure(c, "rider", lead + 4, y1 - 8, 1.0, shadow)
    shadow_figure(c, "horse", lead - 62, y1 - 8, 0.75, shadow)
    for k in range(2):
        bx = x0 - 20 + travel * ((p + 0.4 + k * 0.25) % 1.0)
        shadow_figure(c, "bird", bx, y0 + 22 + 5 * math.sin(2 * math.pi * (p * 2 + k)), 1.0, shadow)

    # Lantern housing behind the cloth, and the timber that holds it all up.
    c.rect(96, 6, 160, 30, DARK, 8)
    c.rect(100, 9, 156, 27, (74, 52, 34, 255), 6)
    lamp = (255, 214, 130, 200 + (0 if frame is None else int(40 * math.sin(2 * math.pi * p * 3))))
    c.circle(128, 18, 8, (255, 232, 176, min(255, lamp[3])))
    c.circle(128, 18, 13, (255, 206, 120, 70))
    for px in (14, 242):                                    # posts
        c.rect(px - 6, 14, px + 6, 122, DARK, 5)
        c.rect(px - 4, 16, px + 4, 120, (86, 60, 38, 255), 4)
    c.rect(20, 118, 236, 126, DARK, 4)                      # foot rail


def shadow_lantern_theater():
    c = Canvas(256, 128)
    draw_shadow_theater(c, None)
    save_rotations(c, "ShadowLanternTheater")
    return c


def shadow_theater_frames(total=10):
    for i in range(total):
        c = Canvas(256, 128)
        draw_shadow_theater(c, i, total)
        c.save(os.path.join(OUT, "ShadowLanternTheaterPlay_%d.png" % i))
    print("  ShadowLanternTheaterPlay_0..%d.png  (256x128)" % (total - 1))


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
#
# The screen is drawn by one function so the static cabinet texture and the
# animation frames can never drift apart. Frame None means attract mode: a full
# maze with the eater parked, which is what the cabinet shows when nobody is on
# it. The animated frames are screen-only overlays on a transparent canvas,
# drawn over the cabinet at the same draw size by CompAnimatedScreen.
# ---------------------------------------------------------------------------

SCREEN = (30, 30, 130, 130)       # glass bounds inside the bezel
RING = (46, 46, 114, 114)         # corridor the eater and ghosts run
MAZE = (70, 104, 226, 255)
SCREEN_BG = (10, 10, 16, 255)
PELLETS = 24


def ring_point(p):
    """Position and heading a fraction p clockwise around the corridor."""
    x0, y0, x1, y1 = RING
    w, h = x1 - x0, y1 - y0
    d = (p % 1.0) * 2 * (w + h)
    if d < w:
        return x0 + d, y0, 1, 0
    d -= w
    if d < h:
        return x1, y0 + d, 0, 1
    d -= h
    if d < w:
        return x1 - d, y1, -1, 0
    return x0, y1 - (d - w), 0, -1


def draw_ghost(c, gx, gy, col, dx, dy, wobble):
    import math
    c.ellipse(gx, gy - 2, 9, 9, col)
    c.rect(gx - 9, gy - 2, gx + 9, gy + 7, col)
    for i in range(3):                                  # skirt, alternating
        off = 3 if (i + wobble) % 2 else 0
        c.circle(gx - 6 + i * 6, gy + 7 - off, 3, col)
    for i in (-1, 1):                                   # eyes track heading
        ex, ey = gx + i * 4, gy - 3
        c.circle(ex, ey, 3.2, (246, 246, 252, 255))
        c.circle(ex + dx * 1.4, ey + dy * 1.4, 1.7, (36, 44, 120, 255))


def draw_arcade_screen(c, frame=None, total=16):
    import math
    x0, y0, x1, y1 = SCREEN
    c.rect(x0, y0, x1, y1, SCREEN_BG, 8)

    # Maze: outer wall, four blocks, and the ghost pen in the middle.
    c.frame(37, 37, 123, 123, MAZE, 2.5, 5)
    c.frame(48, 48, 78, 68, MAZE, 2.5, 3)
    c.frame(84, 48, 112, 68, MAZE, 2.5, 3)
    c.frame(48, 92, 78, 112, MAZE, 2.5, 3)
    c.frame(84, 92, 112, 112, MAZE, 2.5, 3)
    c.rect(72, 74, 90, 86, MAZE, 3)
    c.rect(75, 77, 87, 83, SCREEN_BG, 2)

    p = 0.0 if frame is None else float(frame) / total
    step = frame if frame is not None else 0

    # Pellets vanish behind the eater and come back at the top of each lap.
    for k in range(PELLETS):
        pk = float(k) / PELLETS
        if frame is not None and pk <= p:
            continue
        px, py, _, _ = ring_point(pk)
        c.circle(px, py, 2.2, (248, 236, 198, 255))

    # Power pellets in the corners, blinking the way the real ones do.
    if frame is None or (step // 2) % 2 == 0:
        for corner in (0.0, 0.25, 0.5, 0.75):
            if frame is not None and corner <= p:
                continue
            px, py, _, _ = ring_point(corner + 0.0001)
            c.circle(px, py, 4.6, (250, 228, 160, 255))

    # Two ghosts chasing around the same corridor, a third waiting in the pen.
    for lead, col in ((0.30, (226, 74, 70, 255)), (0.58, (238, 150, 196, 255))):
        gx, gy, gdx, gdy = ring_point(p + lead)
        draw_ghost(c, gx, gy, col, gdx, gdy, step)
    draw_ghost(c, 81, 78, (124, 196, 232, 255), 0, 1, step + 1)

    # The eater, mouth chomping open and shut as it goes.
    ex, ey, edx, edy = ring_point(p)
    c.circle(ex, ey, 10, (246, 214, 62, 255))
    mouth = (45, 26, 6, 26)[step % 4] if frame is not None else 38
    if mouth > 2:
        heading = math.degrees(math.atan2(-edy, edx))
        c.wedge(ex, ey, 11, 0, heading - mouth, heading + mouth, SCREEN_BG)

    # Bezel last, so an overlay frame lands exactly on the cabinet's own glass.
    c.frame(x0, y0, x1, y1, (86, 92, 118, 220), 2.5, 8)


def cocktail_arcade():
    c = Canvas(160, 160)
    cx = cy = 80

    c.rect(10, 10, 150, 150, DARK, 20)
    c.rect(14, 14, 146, 146, (52, 48, 58, 255), 18)        # vinyl-edged table
    c.rect(20, 20, 140, 140, (34, 32, 40, 255), 14)
    c.frame(20, 20, 140, 140, (150, 146, 168, 70), 2, 14)

    draw_arcade_screen(c, None)                            # attract mode

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


def cocktail_arcade_frames(total=16):
    """Screen-only overlays; CompAnimatedScreen cycles them while in use."""
    for i in range(total):
        c = Canvas(160, 160)
        draw_arcade_screen(c, i, total)
        c.save(os.path.join(OUT, "CocktailArcadeScreen_%d.png" % i))
    print("  CocktailArcadeScreen_0..%d.png  (160x160)" % (total - 1))


# ---------------------------------------------------------------------------
# 7. Massage chair  (industrial, 1x1, pawn sits in it)
#
# The animation frames stay clear of the middle of the seat: a pawn using the
# chair is drawn on top of it, so only the armrests and the air around the
# chair are actually visible while it is running.
# ---------------------------------------------------------------------------
def massage_chair():
    c = Canvas(128, 128)
    leather = (128, 46, 44, 255)
    leather_dark = (96, 32, 32, 255)
    frame_col = (66, 68, 78, 255)

    c.rect(22, 16, 106, 118, DARK, 14)                  # chassis
    c.rect(25, 19, 103, 115, frame_col, 12)

    c.rect(30, 20, 98, 62, DARK, 12)                    # backrest
    c.rect(33, 23, 95, 60, leather, 10)
    c.rect(38, 26, 90, 40, leather_dark, 8)             # headrest panel
    for y in range(30, 58, 7):                          # upholstery seams
        c.line(36, y, 92, y, (72, 24, 24, 160), 2)

    c.rect(32, 58, 96, 96, DARK, 10)                    # seat
    c.rect(35, 60, 93, 94, leather, 8)
    for y in range(68, 92, 8):
        c.line(40, y, 88, y, (72, 24, 24, 140), 2)

    c.rect(38, 96, 90, 116, DARK, 9)                    # footrest
    c.rect(41, 98, 87, 114, leather_dark, 7)

    for ax in (22, 92):                                 # armrests
        c.rect(ax, 56, ax + 14, 100, DARK, 7)
        c.rect(ax + 2, 58, ax + 12, 98, leather_dark, 6)
    c.rect(94, 62, 104, 80, (28, 28, 34, 255), 4)       # control pad
    for i in range(3):
        c.circle(99, 67 + i * 6, 2.2, (236, 176, 64, 255))
    save_rotations(c, "MassageChair")
    return c


def massage_chair_frames(total=8):
    """Roller sweep up the backrest, vibration arcs, pulsing control light."""
    import math
    for i in range(total):
        c = Canvas(128, 128)
        phase = float(i) / total

        # Rollers travelling up the backrest, wrapping at the top.
        for roller in (0.0, 0.5):
            t = (phase + roller) % 1.0
            y = 58 - t * 32
            glow = int(150 * math.sin(math.pi * t) + 40)
            c.rect(37, y - 3, 91, y + 3, (255, 214, 150, max(0, min(220, glow))), 3)

        # Vibration arcs off the armrests, where a seated pawn will not hide them.
        for side, sx in ((-1, 26), (1, 102)):
            for ring in range(3):
                t = (phase + ring / 3.0) % 1.0
                r = 5 + t * 13
                alpha = int(150 * (1.0 - t))
                if alpha > 6:
                    c.wedge(sx, 78, r, r - 2.2, 90 + side * 30, 90 + side * 150,
                            (250, 222, 180, alpha))

        # Control pad light pulsing through its three lamps.
        lamp = i % 3
        c.circle(99, 67 + lamp * 6, 3.4, (255, 214, 120, 235))
        c.circle(99, 67 + lamp * 6, 5.6, (255, 196, 96, 70))
        c.save(os.path.join(OUT, "MassageChairRollers_%d.png" % i))
    print("  MassageChairRollers_0..%d.png  (128x128)" % (total - 1))


# ---------------------------------------------------------------------------
# Dreamloop wall projection  (drawn onto a wall by CompWallProjection)
# ---------------------------------------------------------------------------
def dreamloop_projection_frames(total=12):
    sample = None
    """A moving picture, 3 cells wide, thrown onto whatever wall is in front."""
    import math
    for i in range(total):
        c = Canvas(384, 128)
        p = float(i) / total

        c.rect(6, 8, 378, 120, (150, 124, 226, 60), 10)        # spill
        c.rect(12, 14, 372, 114, (46, 34, 84, 205), 8)          # picture
        for band in range(5):                                    # sky
            y0 = 16 + band * 9
            a = 150 - band * 22 + int(18 * math.sin(2 * math.pi * (p + band * 0.1)))
            c.rect(14, y0, 370, y0 + 9, (128, 110, 214, max(30, a)), 0)

        sun_x = 80 + 224 * ((p + 0.15) % 1.0)                    # drifting sun
        c.circle(sun_x, 48, 13, (250, 238, 210, 200))
        c.circle(sun_x, 48, 20, (250, 232, 200, 60))

        c.poly([(12, 88), (90, 62), (150, 84), (220, 58), (300, 86), (372, 66),
                (372, 114), (12, 114)], (28, 20, 54, 230))       # hills
        c.rect(14, 86, 370, 90, (196, 176, 250, 120), 0)         # horizon glow

        for k in range(3):                                        # drifting flyers
            fx = 20 + ((p * 1.6 + k * 0.33) % 1.0) * 344
            fy = 36 + 7 * math.sin(2 * math.pi * (p * 2 + k))
            c.line(fx - 6, fy, fx, fy - 3, (232, 226, 255, 190), 2)
            c.line(fx, fy - 3, fx + 6, fy, (232, 226, 255, 190), 2)

        sweep = 14 + ((p * 2) % 1.0) * 100                        # scanline sweep
        c.rect(14, sweep, 370, sweep + 5, (226, 216, 255, 55), 0)
        for y in range(16, 114, 4):                               # fine scanlines
            c.rect(14, y, 370, y + 1, (16, 10, 32, 55), 0)

        c.frame(12, 14, 372, 114, (208, 194, 255, 120), 2, 8)
        c.save(os.path.join(OUT, "DreamloopProjection_%d.png" % i))
        if i == 3:
            sample = c
    print("  DreamloopProjection_0..%d.png  (384x128)" % (total - 1))
    return sample


# ---------------------------------------------------------------------------
# 8. Vista panel  (spacer, 3x1 wall display)
#
# Four scenes on the same frame, picked by the local clock: night, dawn,
# daylight, dusk. The base texture is the panel switched off.
# ---------------------------------------------------------------------------

VISTA_SKY = {
    "Dawn": dict(top=(86, 102, 170), bottom=(250, 178, 132), body=(255, 228, 176),
                 body_x=0.24, body_y=0.66, hills=(44, 42, 70), glow=(255, 206, 150),
                 stars=0, birds=2),
    "Day": dict(top=(96, 158, 226), bottom=(186, 220, 246), body=(255, 252, 226),
                body_x=0.58, body_y=0.24, hills=(50, 84, 62), glow=(255, 250, 220),
                stars=0, birds=3),
    "Dusk": dict(top=(68, 62, 124), bottom=(244, 138, 88), body=(255, 186, 116),
                 body_x=0.78, body_y=0.68, hills=(38, 34, 56), glow=(255, 176, 110),
                 stars=0, birds=1),
    "Night": dict(top=(12, 16, 40), bottom=(34, 44, 86), body=(228, 234, 248),
                  body_x=0.68, body_y=0.28, hills=(16, 18, 36), glow=(190, 206, 246),
                  stars=34, birds=0),
}


def vista_bezel(c):
    c.rect(2, 4, 382, 124, DARK, 10)
    c.rect(5, 7, 379, 121, (78, 82, 94, 255), 8)
    c.frame(5, 7, 379, 121, (146, 152, 170, 90), 2, 8)
    c.rect(12, 14, 372, 114, (10, 12, 20, 255), 5)          # glass


def draw_vista_scene(c, name, frame, total):
    import math
    sky = VISTA_SKY[name]
    x0, y0, x1, y1 = 12, 14, 372, 114
    p = float(frame) / total

    vista_bezel(c)

    # Sky, blended top to horizon in bands.
    bands = 18
    for b in range(bands):
        t = b / float(bands - 1)
        col = tuple(int(sky["top"][k] + (sky["bottom"][k] - sky["top"][k]) * t) for k in range(3))
        c.rect(x0, y0 + t * 68, x1, y0 + (b + 1) * 68.0 / bands + 1, col + (255,), 0)

    if sky["stars"]:
        for k in range(sky["stars"]):
            sx = x0 + 6 + (k * 61) % (x1 - x0 - 12)
            sy = y0 + 4 + (k * 37) % 56
            twinkle = 120 + int(120 * math.sin(2 * math.pi * (p * 2 + k * 0.17)))
            c.circle(sx, sy, 1.5, (240, 244, 255, max(40, min(255, twinkle))))

    # Sun or moon, drifting a little across the loop so the view is never still.
    bx = x0 + (x1 - x0) * (sky["body_x"] + 0.03 * math.sin(2 * math.pi * p))
    by = y0 + 82 * sky["body_y"]
    c.circle(bx, by, 22, sky["glow"] + (45,))
    c.circle(bx, by, 13, sky["body"] + (255,))
    if name == "Night":
        c.circle(bx + 5, by - 4, 11, (34, 44, 86, 255))     # crescent bite

    # Clouds drifting left to right, wrapping off the edges.
    cloud_col = (250, 250, 255, 150) if name == "Day" else (255, 214, 190, 120)
    if name == "Night":
        cloud_col = (120, 132, 180, 90)
    for k in range(3):
        cx = x0 - 40 + ((p + k * 0.34) % 1.0) * (x1 - x0 + 80)
        cy = y0 + 18 + k * 13
        for dx, dy, r in ((-16, 2, 8), (-4, -2, 11), (10, 2, 8), (20, 3, 6)):
            c.ellipse(cx + dx, cy + dy, r, r * 0.62, cloud_col)

    # Birds, a long way off.
    for k in range(sky["birds"]):
        fx = x0 + 20 + ((p * 0.8 + k * 0.3) % 1.0) * (x1 - x0 - 40)
        fy = y0 + 30 + 6 * math.sin(2 * math.pi * (p * 2 + k))
        c.line(fx - 5, fy, fx, fy - 2.5, (40, 40, 56, 190), 1.8)
        c.line(fx, fy - 2.5, fx + 5, fy, (40, 40, 56, 190), 1.8)

    # Land: a far ridge and a near one, so there is some depth to look at.
    far = tuple(min(255, v + 26) for v in sky["hills"])
    c.poly([(x0, 92), (70, 74), (130, 88), (210, 70), (280, 86), (340, 76), (x1, 88),
            (x1, y1), (x0, y1)], far + (255,))
    c.poly([(x0, 100), (60, 88), (120, 101), (200, 86), (270, 100), (330, 92), (x1, 102),
            (x1, y1), (x0, y1)], sky["hills"] + (255,))
    c.rect(x0, 106, x1, y1, tuple(max(0, v - 8) for v in sky["hills"]) + (255,), 0)

    # Scanlines and a faint sheen, to keep it reading as a screen.
    for y in range(y0, y1, 4):
        c.rect(x0, y, x1, y + 1, (8, 10, 18, 40), 0)
    c.rect(x0, y0, x1, y0 + 14, (255, 255, 255, 18), 0)
    c.frame(12, 14, 372, 114, (150, 160, 190, 90), 1.5, 5)


def vista_panel():
    """Panel with nothing on it: what you see when the power is out."""
    c = Canvas(384, 128)
    vista_bezel(c)
    c.rect(16, 18, 368, 110, (22, 26, 36, 255), 4)
    c.rect(16, 18, 368, 52, (255, 255, 255, 10), 4)
    for i in range(3):
        c.circle(28 + i * 12, 118, 2.6, (54, 58, 70, 255))
    save_rotations(c, "VistaPanel")
    return c


def vista_panel_frames(total=6):
    made = {}
    for name in ("Dawn", "Day", "Dusk", "Night"):
        for i in range(total):
            c = Canvas(384, 128)
            draw_vista_scene(c, name, i, total)
            c.save(os.path.join(OUT, "VistaPanel%s_%d.png" % (name, i)))
            if i == 0:
                made[name] = c
        print("  VistaPanel%s_0..%d.png  (384x128)" % (name, total - 1))
    return made


def main():
    os.makedirs(OUT, exist_ok=True)
    print("Writing textures to %s" % OUT)
    made = {}
    made["KnuckleboneMat"] = knucklebone_mat()
    made["ShadowLanternTheater"] = shadow_lantern_theater()
    shadow_theater_frames()
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
    cocktail_arcade_frames()
    made["HologamePod"] = hologame_pod()
    made["DreamloopHolotheater"] = dreamloop_holotheater()
    made["DreamloopProjection"] = dreamloop_projection_frames()
    made["VistaPanel"] = vista_panel()
    made.update(("Vista" + k, v) for k, v in vista_panel_frames().items())
    made["MassageChair"] = massage_chair()
    massage_chair_frames()

    import preview
    about = os.path.join(ROOT, "About")
    os.makedirs(about, exist_ok=True)
    preview.build({k: (v.pixels(), v.w, v.h) for k, v in made.items()},
                  os.path.join(about, "Preview.png"))
    print("Done.")


if __name__ == "__main__":
    main()
