#!/usr/bin/env python3
"""Generates every texture used by Entertaining Ideas.

Run from anywhere:  python3 Source/TextureGen/generate_textures.py
Output lands in Textures/EntertainingIdeas/Buildings/.

Art is drawn top-down to match RimWorld's camera. Rotatable buildings get the
four _north/_east/_south/_west files a Graphic_Multi needs; since these objects
read the same from every side when seen from above, the rotations are true
90-degree turns of the south-facing art rather than redrawn views.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pnglib import Canvas, rotate, write_png  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Buildings")
TERRAIN = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Terrain")

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


def save_terrain(canvas, name):
    os.makedirs(TERRAIN, exist_ok=True)
    canvas.save(os.path.join(TERRAIN, "%s.png" % name))
    print("  Terrain/%s.png  (%dx%d)" % (name, canvas.w, canvas.h))


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
    trailing = x0 - 26 + travel * ((p + 0.5) % 1.0)
    shadow_figure(c, "horse", trailing, y1 - 6, 0.75, shadow)
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
# Cabinet geometry, shared by the static art and the play-frame overlay so the
# ball always lands on the bumpers that are actually painted on the table.
PB_W, PB_H = 160, 320             # 1x2
PB_TOP, PB_BOT = 6, 314
PB_BACKBOX = 92                   # backbox shell ends here
PB_LAMP_Y = 82                    # marquee lamp row
PB_FIELD_BOT = 266                # playfield ends here, lockbar below
PB_FLIP_Y = 252                   # flipper pivots
BUMPERS = [(60, 148, 15), (102, 139, 13), (78, 179, 12)]
BALL_PATH = [(126, 219), (126, 168), (117, 126), (96, 136),
             (66, 147), (76, 176), (60, 218), (98, 247)]


def pinball(name, cab, cab_dark, field, accent, accent2, glass, motif):
    """A 1x2 cabinet: backbox at the far end, playfield, lockbar at the player end."""
    c = Canvas(PB_W, PB_H)
    L, R = 14, 146        # cabinet sides
    TOP, BOT = PB_TOP, PB_BOT
    mid = (L + R) / 2

    c.rect(L - 4, TOP - 4, R + 4, BOT + 4, DARK, 12)           # outline
    c.rect(L, TOP, R, BOT, cab_dark, 10)                       # cabinet
    c.rect(L, TOP, R, PB_BACKBOX, DARK, 10)                    # backbox shell
    c.rect(L + 7, TOP + 6, R - 7, PB_BACKBOX - 8, glass, 6)    # backglass
    c.rect(L + 7, TOP + 6, R - 7, TOP + 34, (255, 255, 255, 46), 6)   # sheen
    motif(c, L, R, TOP + 14)                                   # theme art
    for i in range(6):                                          # marquee lamps
        c.circle(L + 16 + i * 21.6, PB_LAMP_Y, 3.4, (255, 244, 208, 230))

    # Playfield.
    c.rect(L + 5, PB_BACKBOX + 4, R - 5, PB_FIELD_BOT + 3, DARK, 6)
    c.rect(L + 8, PB_BACKBOX + 7, R - 8, PB_FIELD_BOT, field, 5)
    c.rect(L + 8, PB_BACKBOX + 7, R - 8, PB_BACKBOX + 56, (255, 255, 255, 20), 5)

    # Plunger lane and a guide rail sweeping back up the playfield.
    c.line(R - 20, 110, R - 20, 218, (238, 238, 244, 150), 3)
    c.line(L + 18, 116, L + 18, 186, (238, 238, 244, 105), 2.4)

    # Drop target bank.
    for tx in range(3):
        c.rect(L + 30 + tx * 18, 120, L + 43 + tx * 18, 127, accent2, 2)

    # Pop bumpers.
    for bx, by, rr in BUMPERS:
        c.circle(bx, by, rr + 2, DARK)
        c.circle(bx, by, rr, accent)
        c.circle(bx, by, rr * 0.62, (250, 250, 252, 255))
        c.circle(bx, by, rr * 0.34, accent2)
        c.circle(bx - rr * 0.3, by - rr * 0.3, rr * 0.16, (255, 255, 255, 190))

    # Slingshots.
    c.poly([(L + 14, 232), (L + 42, 222), (L + 42, 242)], DARK)
    c.poly([(L + 17, 232), (L + 39, 225), (L + 39, 239)], accent2)
    c.poly([(R - 14, 232), (R - 42, 222), (R - 42, 242)], DARK)
    c.poly([(R - 17, 232), (R - 39, 225), (R - 39, 239)], accent2)

    # Flippers at the player end.
    for sx in (-1, 1):
        x0, x1 = mid + sx * 10, mid + sx * 34
        c.line(x0, PB_FLIP_Y, x1, PB_FLIP_Y - 9, DARK, 12)
        c.line(x0, PB_FLIP_Y, x1, PB_FLIP_Y - 9, accent, 8)
        c.circle(x0, PB_FLIP_Y, 4.2, (236, 236, 240, 255))

    # Ball and shooter rod.
    c.circle(R - 20, 208, 6.5, DARK)
    c.circle(R - 20, 208, 5.2, (226, 228, 236, 255))
    c.circle(R - 21.6, 206.4, 2.0, (255, 255, 255, 220))
    c.rect(R - 14, PB_FIELD_BOT - 2, R - 6, PB_FIELD_BOT + 20, DARK, 3)
    c.circle(R - 10, PB_FIELD_BOT + 20, 6.5, DARK)
    c.circle(R - 10, PB_FIELD_BOT + 20, 5, accent)

    # Lockbar with the flipper buttons.
    c.rect(L, BOT - 44, R, BOT, cab, 10)
    c.rect(L + 5, BOT - 39, R - 5, BOT - 7, cab_dark, 7)
    for bx in (L + 20, R - 20):
        c.circle(bx, BOT - 23, 5.6, DARK)
        c.circle(bx, BOT - 23, 4.2, accent2)
    c.rect(mid - 16, BOT - 30, mid + 16, BOT - 16, (24, 22, 26, 255), 3)   # coin door
    c.circle(mid, BOT - 23, 3.8, accent)

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


def draw_arcade_title(c, frame, total):
    """Attract mode: the cast marches across under the title, coin prompt blinking."""
    from preview import text, text_width          # shared 5x7 bitmap font

    x0, y0, x1, y1 = SCREEN
    # Opaque, so the maze baked into the cabinet art is covered while idle.
    c.rect(x0, y0, x1, y1, SCREEN_BG, 8)

    title = "CHOMPER"
    c.rect(x0, 38, x1, 58, (18, 16, 40, 255))               # title bar glow
    tw = text_width(title, 2)
    text(c, title, 80 - tw / 2.0, 42, 2, (246, 214, 62, 255))

    # The cast walks a lap across the glass, eater in front, ghosts trailing.
    p = float(frame) / total
    span = (x1 - x0) + 40
    for k, col in enumerate(((226, 74, 70, 255), (238, 150, 196, 255),
                             (124, 196, 232, 255), (244, 170, 92, 255))):
        gx = x0 - 20 + ((p * span) + (k + 1) * 17) % span
        draw_ghost(c, gx, 80, col, 1, 0, frame + k)
    ex = x0 - 20 + (p * span) % span
    c.circle(ex, 78, 10, (246, 214, 62, 255))
    mouth = (45, 26, 6, 26)[frame % 4]
    if mouth > 2:
        c.wedge(ex, 78, 11, 0, -mouth, mouth, SCREEN_BG)

    # Pellets ahead of the eater, eaten as it passes.
    for k in range(7):
        px = x0 + 6 + k * 14
        if px > ex + 6:
            c.circle(px, 78, 2.2, (248, 236, 198, 255))

    if (frame // 2) % 2 == 0:                                # coin prompt blinks
        prompt = "INSERT COIN"
        pw = text_width(prompt, 1)
        text(c, prompt, 80 - pw / 2.0, 106, 1, (226, 232, 248, 255))

    c.frame(x0, y0, x1, y1, (86, 92, 118, 220), 2.5, 8)


def cocktail_arcade_title_frames(total=8):
    """Idle overlays; CompAnimatedScreen runs these when nobody is playing."""
    for i in range(total):
        c = Canvas(160, 160)
        draw_arcade_title(c, i, total)
        c.save(os.path.join(OUT, "CocktailArcadeTitle_%d.png" % i))
    print("  CocktailArcadeTitle_0..%d.png  (160x160)" % (total - 1))


# ---------------------------------------------------------------------------
# 7. Massage chair  (industrial, 1x1, pawn sits in it)
#
# The animation frames stay clear of the middle of the seat: a pawn using the
# chair is drawn on top of it, so only the armrests and the air around the
# chair are actually visible while it is running.
# ---------------------------------------------------------------------------
def massage_chair():
    """Shaped like vanilla's armchair: soft rounded upholstery seen from above,
    a tall back, padded arms, and a light neutral palette so the stuff colour
    carries it. The massage side is the roller seams and the control pad."""
    c = Canvas(128, 128)
    pale = (212, 206, 202, 255)        # takes the stuff colour
    pale_lt = (230, 225, 221, 255)
    pale_dk = (176, 170, 166, 255)
    shade = (146, 140, 136, 255)
    seam = (150, 144, 140, 170)

    c.ellipse(64, 74, 47, 44, (0, 0, 0, 55))                 # contact shadow

    # Back, tallest part of the chair, curved at the top.
    c.rect(26, 16, 102, 74, DARK, 20)
    c.rect(29, 19, 99, 72, pale_dk, 18)
    c.rect(34, 24, 94, 66, pale, 15)
    c.ellipse(64, 30, 28, 11, pale_lt)                        # headrest crown
    for y in range(36, 64, 8):                                # roller seams
        c.line(40, y, 88, y, seam, 2.4)

    # Arms: rounded pads either side, sitting proud of the seat.
    for ax in (16, 88):
        c.rect(ax, 52, ax + 24, 104, DARK, 11)
        c.rect(ax + 2, 54, ax + 22, 102, pale_dk, 10)
        c.ellipse(ax + 12, 66, 9, 11, pale)
        c.ellipse(ax + 12, 62, 8, 8, pale_lt)

    # Seat cushion, bulging toward the viewer.
    c.rect(28, 64, 100, 108, DARK, 16)
    c.rect(31, 67, 97, 105, pale_dk, 14)
    c.rect(35, 70, 93, 101, pale, 12)
    c.ellipse(64, 88, 27, 15, pale_lt)
    c.line(40, 96, 88, 96, seam, 2.4)

    # Footrest, folded down at the front - it is a recliner.
    c.rect(40, 102, 88, 120, DARK, 9)
    c.rect(43, 104, 85, 118, pale_dk, 8)
    c.ellipse(64, 110, 18, 5, pale)

    # Control pad on the right arm, and the base shadow under everything.
    c.rect(92, 78, 108, 98, (58, 56, 60, 255), 5)
    for i in range(3):
        c.circle(100, 83 + i * 6, 2.3, (238, 232, 216, 255))
    c.line(30, 112, 98, 112, (146, 140, 136, 60), 1)
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


# ---------------------------------------------------------------------------
# Pinball in play  (one overlay strip shared by all four tables)
#
# Only the ball, its trail and the lamps that just got hit are drawn, all in
# neutral white and silver, so the same frames sit correctly on the red, green,
# steel and violet cabinets.
# ---------------------------------------------------------------------------

def pinball_play_frames(total=8):
    import math
    for i in range(total):
        c = Canvas(PB_W, PB_H)
        bx, by = BALL_PATH[i % len(BALL_PATH)]
        px, py = BALL_PATH[(i - 1) % len(BALL_PATH)]

        # Motion trail back toward the previous position.
        c.line(px, py, bx, by, (226, 232, 248, 70), 7)
        c.line((px + bx) / 2, (py + by) / 2, bx, by, (238, 242, 255, 110), 8)

        # Lamps flare when the ball is on top of them.
        for mx, my, mr in BUMPERS:
            if math.hypot(bx - mx, by - my) < mr + 14:
                c.circle(mx, my, mr + 9, (255, 252, 226, 60))
                c.ring(mx, my, mr + 5, mr + 1, (255, 250, 214, 190))
                c.circle(mx, my, mr * 0.5, (255, 255, 244, 220))

        # Flippers snap up as the ball comes down to them.
        if by > 200:
            for sx in (-1, 1):
                x0, x1 = 80 + sx * 10, 80 + sx * 34
                c.line(x0, PB_FLIP_Y, x1, PB_FLIP_Y - 22, (255, 250, 220, 210), 9)

        # Backglass keeps flashing while the table is live.
        if i % 2 == 0:
            c.rect(21, 12, 139, PB_BACKBOX - 8, (255, 248, 210, 30), 6)
        for k in range(6):
            if (i + k) % 3 == 0:
                c.circle(30 + k * 21.6, PB_LAMP_Y, 4.6, (255, 250, 220, 200))

        c.circle(bx, by, 7.5, (30, 30, 36, 220))
        c.circle(bx, by, 6, (232, 236, 246, 255))
        c.circle(bx - 1.8, by - 1.8, 2.4, (255, 255, 255, 240))
        c.save(os.path.join(OUT, "PinballPlay_%d.png" % i))
    print("  PinballPlay_0..%d.png  (%dx%d)" % (total - 1, PB_W, PB_H))


# ---------------------------------------------------------------------------
# 9. Soaking tub  (medieval, 1x1, wood-fired, pawns get in)
# ---------------------------------------------------------------------------

def draw_tub_water(c, frame=None, total=6):
    """Still water for the cabinet texture itself."""
    import math
    p = 0.0 if frame is None else float(frame) / total
    c.circle(64, 62, 38, (46, 104, 112, 255))
    c.circle(64, 62, 38, (60, 130, 138, 120))
    for k in range(3):
        r = 8 + ((p + k / 3.0) % 1.0) * 28
        alpha = int(130 * (1.0 - (r - 8) / 28.0))
        if alpha > 8:
            c.ring(64, 62, r, r - 2, (186, 232, 236, alpha))


def soaking_tub(name="SoakingTub", electric=False):
    c = Canvas(128, 128)
    c.circle(64, 62, 48, DARK)
    c.circle(64, 62, 45, (112, 78, 48, 255))                    # staves
    for k in range(14):
        import math
        a = k / 14.0 * 2 * math.pi
        c.line(64 + math.cos(a) * 37, 62 + math.sin(a) * 37,
               64 + math.cos(a) * 46, 62 + math.sin(a) * 46, (74, 48, 28, 255), 5)
    band = (150, 162, 178, 255) if electric else (146, 150, 158, 255)
    c.ring(64, 62, 45, 41, band)                                # hoop
    c.ring(64, 62, 40, 38, DARK)
    draw_tub_water(c, None)

    if electric:
        import math
        for k in range(10):                                     # heating element
            a = k / 10.0 * 2 * math.pi
            c.line(64 + math.cos(a) * 26, 62 + math.sin(a) * 26,
                   64 + math.cos(a) * 33, 62 + math.sin(a) * 33, (206, 132, 96, 150), 3)
        c.rect(40, 104, 88, 124, DARK, 6)                       # control box
        c.rect(43, 107, 85, 121, (62, 66, 78, 255), 5)
        for k, col in enumerate(((120, 226, 140, 255), (236, 196, 78, 255), (130, 190, 240, 255))):
            c.circle(53 + k * 11, 114, 3.2, col)
    else:
        c.rect(44, 104, 84, 124, DARK, 6)                       # firebox
        c.rect(47, 107, 81, 121, (52, 44, 40, 255), 5)
        c.circle(64, 114, 6, (226, 120, 52, 235))
        c.circle(64, 114, 3, (255, 196, 110, 255))
    save_single(c, name)
    return c


def soaking_tub_water_frames(total=6):
    """The near half of the tub, drawn OVER the occupant.

    1.6 has a real swimming pose, but it is keyed to Pawn.Swimming, which is
    read-only and comes from the terrain underfoot - a building cannot ask for
    it. Painting the front of the tub back over the occupant's legs gets the
    same read on both 1.5 and 1.6. Everything above the waterline is left clear
    so their head and shoulders still show.
    """
    import math
    for i in range(total):
        c = Canvas(128, 128)
        p = float(i) / total
        # Everything below the waterline, filled scanline by scanline so the
        # line sits where a pawn's chest is rather than halfway up their head.
        waterline = 72
        for y in range(waterline, 102):
            dy = y - 62
            half = math.sqrt(max(0.0, 39.0 * 39.0 - dy * dy))
            if half > 0:
                c.line(64 - half, y, 64 + half, y, (46, 104, 112, 255), 1.4)
        c.line(64 - 36, waterline, 64 + 36, waterline, (96, 176, 184, 200), 2.4)
        for k in range(3):                                      # ripples
            r = 10 + ((p + k / 3.0) % 1.0) * 26
            alpha = int(140 * (1.0 - (r - 10) / 26.0))
            if alpha > 8:
                c.wedge(64, 62, r, r - 2.4, 200, 340, (192, 236, 240, alpha))
        c.wedge(64, 62, 46, 39, 184, 356, (112, 78, 48, 255))   # near rim
        c.wedge(64, 62, 45, 41, 184, 356, (146, 150, 158, 255))  # iron band
        c.wedge(64, 62, 48, 46, 184, 356, DARK)
        c.save(os.path.join(OUT, "SoakingTubWater_%d.png" % i))
    print("  SoakingTubWater_0..%d.png  (128x128)" % (total - 1))


# ---------------------------------------------------------------------------
# 10. Aquarium  (industrial, 2x1, something to watch)
# ---------------------------------------------------------------------------

# Looking down INTO the tank, not through the side of it: the game's camera is
# a steep top-down, so you see the water surface, the gravel through it, plants
# as rosettes, and fish from above. A shallow band of near glass along the
# south edge keeps it from reading as a flat rectangle on the floor.
TANK = (22, 26, 234, 100)          # water surface, in texture pixels
GLASS_BAND = 12                    # near wall visible below the water


def _rot_poly(cx, cy, rx, ry, ang, n=14):
    import math
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * math.cos(ang) - y * math.sin(ang),
                    cy + x * math.sin(ang) + y * math.cos(ang)))
    return pts


def draw_fish_from_above(c, x, y, ang, length, col, wiggle=0.0):
    """A fish seen from directly overhead: slim body, tail kicked to one side."""
    import math
    body_r, body_w = length * 0.5, length * 0.22
    c.poly(_rot_poly(x, y, body_r, body_w, ang), col)

    tail_ang = ang + wiggle
    tx = x - math.cos(ang) * body_r * 0.9
    ty = y - math.sin(ang) * body_r * 0.9
    tip_x = tx - math.cos(tail_ang) * length * 0.42
    tip_y = ty - math.sin(tail_ang) * length * 0.42
    spread = length * 0.2
    c.poly([(tx, ty),
            (tip_x - math.sin(tail_ang) * spread, tip_y + math.cos(tail_ang) * spread),
            (tip_x + math.sin(tail_ang) * spread, tip_y - math.cos(tail_ang) * spread)], col)

    for side in (-1, 1):                                    # pectoral fins
        fx = x + math.cos(ang) * body_r * 0.15
        fy = y + math.sin(ang) * body_r * 0.15
        c.poly([(fx, fy),
                (fx - math.sin(ang) * side * body_w * 2.1 - math.cos(ang) * length * 0.1,
                 fy + math.cos(ang) * side * body_w * 2.1 - math.sin(ang) * length * 0.1),
                (fx - math.cos(ang) * length * 0.18, fy - math.sin(ang) * length * 0.18)],
               col[:3] + (150,))
    # head highlight, so the fish reads as pointing somewhere
    c.circle(x + math.cos(ang) * body_r * 0.55, y + math.sin(ang) * body_r * 0.55,
             body_w * 0.5, (255, 255, 255, 90))


def _swim_point(p, phase, x0, y0, x1, y1):
    """A lazy looping path inside the tank, with the heading along it."""
    import math
    t = 2 * math.pi * ((p + phase) % 1.0)
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    rx, ry = (x1 - x0) * 0.32, (y1 - y0) * 0.26
    x = cx + math.cos(t) * rx
    y = cy + math.sin(t * 2) * ry * 0.6          # figure-eight, reads as wandering
    dx = -math.sin(t) * rx
    dy = math.cos(t * 2) * ry * 1.2
    return x, y, math.atan2(dy, dx)


def draw_tank_contents(c, frame=None, total=8):
    import math
    x0, y0, x1, y1 = TANK
    p = 0.0 if frame is None else float(frame) / total

    # Gravel bed, seen through the water.
    c.rect(x0, y0, x1, y1, (104, 92, 70, 255), 5)
    for k in range(120):
        gx = x0 + 4 + (k * 53) % (x1 - x0 - 8)
        gy = y0 + 4 + (k * 31) % (y1 - y0 - 8)
        shade = (124, 112, 86, 255) if k % 3 else (88, 78, 60, 255)
        c.circle(gx, gy, 2.4, shade)

    # Water over it: deeper in the middle, paler at the rim.
    c.rect(x0, y0, x1, y1, (34, 126, 158, 165), 5)
    c.ellipse((x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) * 0.42, (y1 - y0) * 0.42,
              (18, 96, 134, 105))
    c.frame(x0, y0, x1, y1, (12, 54, 78, 90), 4, 5)          # depth at the walls

    # Planting, seen from overhead as rosettes of blades.
    for px, py, r, col in ((52, 44, 13, (58, 138, 86)), (96, 86, 11, (72, 158, 96)),
                           (170, 48, 12, (54, 128, 80)), (206, 82, 10, (74, 160, 100))):
        sway = 0.5 * math.sin(2 * math.pi * (p + px * 0.01))
        for k in range(9):
            a = k / 9.0 * 2 * math.pi + sway
            c.line(px, py, px + math.cos(a) * r, py + math.sin(a) * r, col + (235,), 3)
        c.circle(px, py, 3, (36, 92, 60, 255))
    for rx, ry, rr in ((132, 40, 7), (74, 74, 5), (196, 40, 4)):    # stones
        c.circle(rx, ry, rr, (92, 96, 104, 255))
        c.circle(rx - rr * 0.3, ry - rr * 0.3, rr * 0.5, (118, 122, 130, 255))

    # No fish here. A frame strip can only move them in whole steps, which is
    # what made them stutter; CompSwimmingFish draws them every rendered frame
    # instead. What is left in this strip - swaying planting, drifting caustics
    # - moves slowly enough that stepping is invisible.

    # Caustics and surface glare drifting across the top.
    for k in range(6):
        cx = x0 + 14 + ((p * 0.4 + k / 6.0) % 1.0) * (x1 - x0 - 28)
        cy = y0 + 12 + (k * 27) % (y1 - y0 - 26)
        for seg in range(3):                                  # wavy, not dashes
            import math as _m
            a = _m.sin(seg * 1.6 + p * 6) * 3
            c.line(cx + seg * 7 - 10, cy + a, cx + seg * 7 - 3, cy - a,
                   (170, 226, 240, 34), 2.4)
    c.rect(x0, y0, x1, y0 + 10, (226, 246, 252, 30), 4)



def aquarium_fish_sprites():
    """One sprite per kind of fish, drawn nose-east so the comp can rotate it
    to whatever heading the fish is swimming."""
    kinds = [
        ("AquariumFish_0", 54, (240, 156, 60)),
        ("AquariumFish_1", 46, (226, 96, 96)),
        ("AquariumFish_2", 38, (244, 214, 96)),
        ("AquariumFish_3", 42, (118, 186, 232)),
    ]
    for name, length, col in kinds:
        c = Canvas(64, 64)
        # A soft shadow baked in slightly off-centre: it travels with the fish
        # and sells the gap between it and the gravel.
        draw_fish_from_above(c, 32 + 2.0, 32 + 2.8, 0.0, length, (14, 40, 60, 80))
        draw_fish_from_above(c, 32, 32, 0.0, length, col + (255,))
        c.save(os.path.join(OUT, "%s.png" % name))
    print("  AquariumFish_0..3.png  (64x64)")

def aquarium():
    c = Canvas(256, 128)
    x0, y0, x1, y1 = TANK

    c.rect(10, 14, 246, y1 + GLASS_BAND + 6, DARK, 10)          # cabinet shell
    c.rect(13, 17, 243, y1 + GLASS_BAND + 3, (62, 66, 80, 255), 8)

    draw_tank_contents(c, None)

    # The bit of near wall the camera can see, below the water line.
    c.rect(x0, y1, x1, y1 + GLASS_BAND, (38, 74, 96, 235), 3)
    c.rect(x0, y1, x1, y1 + 3, (150, 206, 224, 120), 2)
    c.frame(x0 - 3, y0 - 3, x1 + 3, y1 + GLASS_BAND, (176, 200, 214, 110), 2.5, 5)

    c.rect(86, 8, 170, 20, DARK, 5)                              # hood lamp
    c.rect(89, 10, 167, 18, (214, 232, 240, 235), 4)
    save_rotations(c, "Aquarium")
    return c


def aquarium_frames(total=8):
    for i in range(total):
        c = Canvas(256, 128)
        draw_tank_contents(c, i, total)
        c.save(os.path.join(OUT, "AquariumLife_%d.png" % i))
    print("  AquariumLife_0..%d.png  (256x128)" % (total - 1))


# ---------------------------------------------------------------------------
# 11. Skittles lane  (medieval, 1x5, rolled from the near end)
# ---------------------------------------------------------------------------

# Nine pins in a diamond, which is what skittles actually uses; ten in a
# triangle for the bowling lane it eventually turned into.
PIN_ROWS = [(64,), (50, 78), (36, 64, 92), (50, 78), (64,)]
PIN_ROWS_TENPIN = [(64,), (52, 76), (40, 64, 88), (28, 52, 76, 100)]

LANE_RUSTIC = dict(frame=(72, 50, 32, 255), lane=(186, 148, 96, 255),
                   plank=(168, 130, 82, 120), gutter=(54, 38, 24, 255),
                   deck=(198, 164, 112, 255), ball=(58, 62, 78, 255),
                   ball_hi=(128, 134, 156, 255), foul=(150, 60, 50, 220))
LANE_MODERN = dict(frame=(44, 48, 62, 255), lane=(224, 192, 138, 255),
                   plank=(206, 170, 112, 110), gutter=(28, 32, 44, 255),
                   deck=(36, 40, 54, 255), ball=(62, 42, 104, 255),
                   ball_hi=(152, 120, 220, 255), foul=(196, 72, 60, 230))


def draw_skittles(c, frame=None, total=6, modern=False):
    import math
    p = None if frame is None else float(frame) / (total - 1)
    pal = LANE_MODERN if modern else LANE_RUSTIC
    rows = PIN_ROWS_TENPIN if modern else PIN_ROWS

    c.rect(6, 8, 122, 888, DARK, 10)
    c.rect(9, 11, 119, 885, pal["frame"], 8)                    # frame
    c.rect(24, 16, 104, 880, pal["lane"], 4)                    # lane
    for y in range(20, 876, 26):                                 # boards
        c.line(26, y, 102, y, pal["plank"], 1.6)
    c.rect(12, 16, 24, 880, pal["gutter"], 3)                   # gutters
    c.rect(104, 16, 116, 880, pal["gutter"], 3)
    c.rect(24, 16, 104, 190, pal["deck"], 4)                    # pin deck
    c.line(26, 190, 102, 190, (120, 88, 54, 190), 2)
    c.line(26, 812, 102, 812, pal["foul"], 3)                   # foul line

    if modern:
        c.rect(24, 16, 104, 60, (24, 26, 36, 255), 3)           # pinsetter housing
        for k in range(4):
            c.circle(38 + k * 18, 38, 4, (120, 200, 210, 220))
        for k, ax in enumerate((40, 52, 64, 76, 88)):            # aiming arrows
            c.poly([(ax, 700), (ax - 5, 712), (ax + 5, 712)], (188, 146, 92, 200))
        for dx in (36, 50, 64, 78, 92):                          # approach dots
            c.circle(dx, 836, 2.6, (150, 120, 80, 200))
        c.rect(106, 200, 114, 800, (58, 64, 84, 255), 3)        # ball return rail

    scattered = p is not None and p > 0.72
    for row, xs in enumerate(rows):
        py = 46 + row * 27
        for k, px in enumerate(xs):
            if scattered:
                shove = (p - 0.72) / 0.28
                ang = (row * 1.7 + k * 2.3)
                px = px + math.cos(ang) * 26 * shove
                py2 = py + math.sin(ang) * 20 * shove - 6 * shove
                tilt = 5 * shove
            else:
                py2, tilt = py, 0
            c.ellipse(px, py2, 7 + tilt, 9 - tilt * 0.4, DARK)
            c.ellipse(px, py2, 5.5 + tilt, 7.5 - tilt * 0.4, (238, 232, 218, 255))
            c.ellipse(px, py2 - 2, 3.4, 2.6, (196, 62, 54, 255))

    if p is None:
        bx, by = 64, 846
    else:
        by = 846 - min(1.0, p / 0.72) * 640
        bx = 64 + 10 * math.sin(p * 5)
    c.circle(bx, by, 13, DARK)
    c.circle(bx, by, 11, pal["ball"])
    c.circle(bx - 3, by - 3, 3.4, pal["ball_hi"])
    for k in range(3):                                           # finger holes
        c.circle(bx - 3 + k * 3, by + 3, 1.6, (28, 30, 38, 255))
    if p is not None and p > 0.05:
        c.line(bx, by + 18, bx, min(860, by + 72), (255, 255, 255, 50), 10)


def skittles_lane():
    c = Canvas(128, 896)
    draw_skittles(c, None)
    save_rotations(c, "SkittlesLane")
    return c


def skittles_frames(total=6):
    for i in range(total):
        c = Canvas(128, 896)
        draw_skittles(c, i, total)
        c.save(os.path.join(OUT, "SkittlesLaneRoll_%d.png" % i))
    print("  SkittlesLaneRoll_0..%d.png  (128x896)" % (total - 1))


def bowling_lane():
    c = Canvas(128, 896)
    draw_skittles(c, None, modern=True)
    save_rotations(c, "BowlingLane")
    return c


def bowling_frames(total=6):
    for i in range(total):
        c = Canvas(128, 896)
        draw_skittles(c, i, total, modern=True)
        c.save(os.path.join(OUT, "BowlingLaneRoll_%d.png" % i))
    print("  BowlingLaneRoll_0..%d.png  (128x896)" % (total - 1))


# ---------------------------------------------------------------------------
# 12. Karaoke machine  (industrial, 1x1, a crowd gathers)
# ---------------------------------------------------------------------------

def karaoke_machine():
    c = Canvas(128, 128)
    c.rect(14, 14, 114, 116, DARK, 12)
    c.rect(17, 17, 111, 113, (48, 44, 62, 255), 10)
    c.rect(26, 24, 102, 66, (14, 16, 26, 255), 6)               # screen
    c.frame(26, 24, 102, 66, (120, 130, 170, 140), 2, 6)
    for k in range(5):                                           # idle lyric bars
        c.rect(32, 32 + k * 7, 32 + (18 + (k * 13) % 44), 36 + k * 7,
               (86, 132, 196, 200), 2)
    for sx in (24, 88):                                          # speakers
        c.circle(sx + 8, 90, 15, DARK)
        c.circle(sx + 8, 90, 12.5, (34, 32, 44, 255))
        c.ring(sx + 8, 90, 9, 7.5, (78, 74, 96, 255))
        c.circle(sx + 8, 90, 4, (96, 92, 116, 255))
    c.rect(54, 78, 74, 104, DARK, 5)                            # mic cradle
    c.rect(57, 81, 71, 101, (62, 58, 76, 255), 4)
    c.circle(64, 86, 6, (196, 198, 210, 255))
    c.circle(64, 86, 4, (120, 124, 140, 255))
    c.rect(58, 92, 70, 100, (40, 38, 50, 255), 3)
    for k in range(3):
        c.circle(61 + k * 3, 108, 2, (226, 182, 78, 255))
    save_rotations(c, "KaraokeMachine")
    return c


def karaoke_frames(total=6):
    import math
    for i in range(total):
        c = Canvas(128, 128)
        p = float(i) / total

        c.rect(26, 24, 102, 66, (14, 16, 26, 255), 6)           # screen redraw
        for k in range(5):                                       # bouncing lyrics
            lit = (i + k) % 5
            width = 16 + ((k * 13 + i * 7) % 46)
            col = (250, 226, 120, 235) if lit < 2 else (86, 132, 196, 210)
            c.rect(32, 32 + k * 7, 32 + width, 36 + k * 7, col, 2)
        bounce = 30 + 44 * ((p * 2) % 1.0)                        # bouncing ball
        c.circle(bounce, 28, 3.2, (255, 244, 200, 240))

        for sx in (24, 88):                                      # speaker pulse
            pulse = 1.0 + 0.25 * math.sin(2 * math.pi * (p * 2 + (0 if sx < 50 else 0.5)))
            c.ring(sx + 8, 90, 11 * pulse, 8.5 * pulse, (152, 146, 190, 180))
            c.circle(sx + 8, 90, 4 * pulse, (206, 198, 246, 200))

        for k in range(3):                                       # notes drifting off
            t = (p + k / 3.0) % 1.0
            nx = 64 + (k - 1) * 22 + 6 * math.sin(2 * math.pi * t)
            ny = 80 - t * 58
            a = int(210 * (1 - t))
            c.circle(nx, ny, 3.4, (250, 232, 150, a))
            c.rect(nx + 2, ny - 12, nx + 4, ny, (250, 232, 150, a), 1)
        c.circle(64, 86, 3, (250, 120, 110, 180 + int(60 * math.sin(2 * math.pi * p))))
        c.save(os.path.join(OUT, "KaraokeMachineSing_%d.png" % i))
    print("  KaraokeMachineSing_0..%d.png  (128x128)" % (total - 1))


# ---------------------------------------------------------------------------
# 13. Gravball court  (ultra, 3x3, played from the edges)
#
# The play overlay is a small texture drawn over the middle of the court, so a
# 3x3 building does not need 3x3 animation frames.
# ---------------------------------------------------------------------------

def gravball_court():
    import math
    c = Canvas(384, 384)
    mid = 192

    c.rect(10, 10, 374, 374, DARK, 22)
    c.rect(16, 16, 368, 368, (26, 30, 46, 255), 18)             # court floor
    c.frame(16, 16, 368, 368, (92, 214, 226, 70), 3, 18)
    for k in range(1, 4):                                        # floor grid
        c.line(16 + k * 88, 22, 16 + k * 88, 362, (72, 90, 120, 60), 2)
        c.line(22, 16 + k * 88, 362, 16 + k * 88, (72, 90, 120, 60), 2)

    c.ring(mid, mid, 96, 92, (104, 224, 232, 120))              # centre circle
    c.ring(mid, mid, 34, 30, (104, 224, 232, 150))
    c.line(22, mid, 362, mid, (104, 224, 232, 70), 3)

    for gy in (54, 330):                                         # goal rings
        c.ring(mid, gy, 40, 33, DARK)
        c.ring(mid, gy, 38, 35, (126, 236, 240, 220))
        c.ring(mid, gy, 33, 31, (70, 140, 168, 200))
    for cx, cy in ((44, 44), (340, 44), (44, 340), (340, 340)):  # emitter posts
        c.circle(cx, cy, 20, DARK)
        c.circle(cx, cy, 16, (58, 66, 86, 255))
        c.circle(cx, cy, 9, (140, 240, 244, 210))
        c.circle(cx, cy, 4.5, (236, 252, 252, 240))
    save_rotations(c, "GravballCourt")
    return c


def gravball_frames(total=6):
    """Small overlay: the ball on its orbit, plus the goal flashing on a score."""
    import math
    for i in range(total):
        c = Canvas(160, 160)
        p = float(i) / total
        mid = 80
        a = 2 * math.pi * p
        bx = mid + math.cos(a) * 44
        by = mid + math.sin(a) * 30

        for k in range(5):                                       # trail
            ta = a - k * 0.26
            tx = mid + math.cos(ta) * 44
            ty = mid + math.sin(ta) * 30
            c.circle(tx, ty, 7 - k, (150, 240, 246, int(110 - k * 20)))
        c.circle(bx, by, 13, (140, 238, 244, 70))
        c.circle(bx, by, 8.5, (232, 252, 252, 240))
        c.circle(bx - 2, by - 2, 3, (255, 255, 255, 255))
        if i % 3 == 0:                                           # score flash
            c.ring(mid, 12, 26, 20, (236, 252, 252, 150))
        c.save(os.path.join(OUT, "GravballPlay_%d.png" % i))
    print("  GravballPlay_0..%d.png  (160x160)" % (total - 1))



# ---------------------------------------------------------------------------
# 19-21. Orreries  (clockwork, three sizes, always turning)
# ---------------------------------------------------------------------------

BRASS = (198, 154, 74, 255)
BRASS_HI = (238, 206, 132, 255)
BRASS_DK = (128, 94, 40, 255)
ORR_WOOD = (110, 78, 50, 255)
ORR_WOOD_DK = (74, 50, 32, 255)


def ell_ring(c, cx, cy, rx, ry, w, color, steps=240):
    """Thin elliptical band, stamped as overlapping dots. pnglib has no
    elliptical ring and no way to erase, so the band is drawn, not carved."""
    for i in range(steps):
        a = 2 * math.pi * i / steps
        c.circle(cx + math.cos(a) * rx, cy + math.sin(a) * ry, w / 2.0, color)


def orbiting_planet(c, cx, cy, r, body, rim=None):
    c.circle(cx, cy, r + 1.4, DARK)
    c.circle(cx, cy, r, body)
    c.circle(cx - r * 0.3, cy - r * 0.32, r * 0.34, (255, 255, 255, 110))
    if rim:
        ell_ring(c, cx, cy, r * 2.0, r * 0.8, 1.8, rim)


# Orbit radius, planet radius, colour, ring colour, laps per animation cycle.
# Inner planets go round more often, as they should.
TABLETOP_ORBITS = [
    (20, 4.0, (188, 150, 120, 255), None, 3),
    (30, 5.2, (96, 142, 186, 255), None, 2),
    (40, 6.4, (206, 150, 96, 255), BRASS_HI, 1),
]
GRAND_ORBITS = [
    (32, 5.0, (186, 148, 118, 255), None, 5),
    (50, 6.4, (214, 178, 122, 255), None, 4),
    (68, 7.6, (92, 140, 190, 255), None, 3),
    (86, 10.0, (208, 152, 98, 255), BRASS_HI, 2),
    (104, 8.4, (178, 190, 214, 255), None, 1),
]


def tabletop_orrery_body(c, phase=None):
    """phase None draws the static cabinet; a number draws only the planets."""
    cx = cy = 80
    if phase is None:
        c.rect(18, 18, 142, 142, DARK, 10)
        c.rect(21, 21, 139, 139, ORR_WOOD, 9)
        c.rect(26, 26, 134, 134, ORR_WOOD_DK, 7)
        c.frame(26, 26, 134, 134, (255, 255, 255, 30), 2, 7)
        for fx, fy in ((30, 30), (130, 30), (30, 130), (130, 130)):
            c.circle(fx, fy, 5, BRASS_DK)
            c.circle(fx, fy, 3.2, BRASS)
        c.circle(cx, cy, 44, (30, 26, 24, 190))
        for orbit, _, _, _, _ in TABLETOP_ORBITS:
            c.ring(cx, cy, orbit + 1.2, orbit - 1.2, BRASS_DK)
            c.ring(cx, cy, orbit + 0.6, orbit - 0.6, BRASS)
        c.circle(cx, cy, 11, (232, 170, 52, 255))
        c.circle(cx, cy, 8, (252, 220, 120, 255))
        c.circle(cx, cy, 4, (255, 248, 216, 255))
        c.rect(136, 74, 152, 86, DARK, 4)                 # hand crank
        c.rect(138, 76, 150, 84, BRASS, 3)
        c.circle(152, 80, 6, DARK)
        c.circle(152, 80, 4.4, BRASS_HI)
        return

    for k, (orbit, pr, col, rim, laps) in enumerate(TABLETOP_ORBITS):
        a = 2 * math.pi * (phase * laps + k * 0.31)
        orbiting_planet(c, cx + math.cos(a) * orbit, cy + math.sin(a) * orbit, pr, col, rim)


def tabletop_orrery():
    c = Canvas(160, 160)
    tabletop_orrery_body(c, None)
    tabletop_orrery_body(c, 0.0)      # a still frame for the build menu
    save_single(c, "TabletopOrrery")
    return c


def tabletop_orrery_frames(total=12):
    for i in range(total):
        c = Canvas(160, 160)
        tabletop_orrery_body(c, float(i) / total)
        c.save(os.path.join(OUT, "TabletopOrreryTurn_%d.png" % i))
    print("  TabletopOrreryTurn_0..%d.png  (160x160)" % (total - 1))


def grand_orrery_body(c, phase=None):
    cx = cy = 160
    if phase is None:
        for r, col in ((152, DARK), (146, (58, 48, 44, 255)), (134, ORR_WOOD_DK)):
            c.poly([(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r)
                    for a in range(22, 382, 45)], col)
        c.ring(cx, cy, 132, 118, BRASS_DK)                # engraved zodiac band
        c.ring(cx, cy, 130, 120, BRASS)
        for i in range(24):
            a = math.radians(i * 15)
            c.line(cx + math.cos(a) * 120, cy + math.sin(a) * 120,
                   cx + math.cos(a) * 130, cy + math.sin(a) * 130, BRASS_DK, 2)
        c.circle(cx, cy, 116, (22, 20, 30, 210))          # night under the dome
        for orbit, _, _, _, _ in GRAND_ORBITS:
            c.ring(cx, cy, orbit + 1.6, orbit - 1.6, BRASS_DK)
            c.ring(cx, cy, orbit + 0.8, orbit - 0.8, BRASS)
        c.circle(cx, cy, 18, (230, 160, 44, 255))         # gilded sun
        c.circle(cx, cy, 13, (250, 214, 110, 255))
        c.circle(cx, cy, 6, (255, 250, 228, 255))
        for i in range(16):
            a = math.radians(i * 22.5 + 8)
            c.line(cx + math.cos(a) * 18, cy + math.sin(a) * 18,
                   cx + math.cos(a) * 26, cy + math.sin(a) * 26, (250, 210, 120, 150), 2.4)
        c.ring(cx, cy, 116, 110, (208, 232, 246, 60))     # glass dome edge
        c.ellipse(cx - 46, cy - 60, 40, 26, (255, 255, 255, 26))
        for fx, fy in ((44, 44), (276, 44), (44, 276), (276, 276)):
            c.circle(fx, fy, 13, DARK)                    # corner pillars
            c.circle(fx, fy, 10, BRASS_DK)
            c.circle(fx, fy, 6.5, BRASS)
        return

    for k, (orbit, pr, col, rim, laps) in enumerate(GRAND_ORBITS):
        a = 2 * math.pi * (phase * laps + k * 0.23)
        px, py = cx + math.cos(a) * orbit, cy + math.sin(a) * orbit
        orbiting_planet(c, px, py, pr, col, rim)
        if k == 2:                                        # a moon on its own arm
            ma = 2 * math.pi * (phase * 9 + 0.5)
            c.circle(px + math.cos(ma) * 14, py + math.sin(ma) * 14, 3.0, DARK)
            c.circle(px + math.cos(ma) * 14, py + math.sin(ma) * 14, 2.0, (222, 222, 230, 255))


def grand_orrery():
    c = Canvas(320, 320)
    grand_orrery_body(c, None)
    grand_orrery_body(c, 0.0)
    save_single(c, "GrandOrrery")
    return c


def grand_orrery_frames(total=16):
    for i in range(total):
        c = Canvas(320, 320)
        grand_orrery_body(c, float(i) / total)
        c.save(os.path.join(OUT, "GrandOrreryTurn_%d.png" % i))
    print("  GrandOrreryTurn_0..%d.png  (320x320)" % (total - 1))


def armillary_body(c, phase=None):
    """The rings themselves turn, so the sphere reads as slowly precessing."""
    cx = cy = 80
    if phase is None:
        for a in (90, 210, 330):                          # tripod legs
            ax = math.radians(a)
            x, y = cx + math.cos(ax) * 56, cy + math.sin(ax) * 56
            c.line(cx, cy, x, y, DARK, 9)
            c.line(cx, cy, x, y, ORR_WOOD, 6)
            c.circle(x, y, 8, DARK)
            c.circle(x, y, 6, BRASS_DK)
            c.circle(x, y, 3.6, BRASS)
        c.ring(cx, cy, 60, 54, DARK)                      # fixed horizon ring
        c.ring(cx, cy, 59, 55, BRASS)
        for i in range(36):
            a = math.radians(i * 10)
            c.line(cx + math.cos(a) * 55, cy + math.sin(a) * 55,
                   cx + math.cos(a) * 59, cy + math.sin(a) * 59, BRASS_DK, 1.4)
        return

    # Seen from above, a ring turning about the vertical axis reads as an
    # ellipse whose width breathes between edge-on and full circle.
    t = 2 * math.pi * phase
    for k, (base, col) in enumerate(((46, BRASS_HI), (36, BRASS), (44, (226, 186, 104, 255)))):
        w = abs(math.cos(t + k * math.pi / 3.0))
        rx = max(4.0, base * (0.12 + 0.88 * w))
        ell_ring(c, cx, cy, rx, base, 4.4, DARK)
        ell_ring(c, cx, cy, rx, base, 2.8, col)
    ell_ring(c, cx, cy, 46, 46, 5.2, DARK)                # equatorial, fixed
    ell_ring(c, cx, cy, 46, 46, 3.4, BRASS_HI)
    c.line(cx, cy - 52, cx, cy + 52, DARK, 5)             # polar axis
    c.line(cx, cy - 52, cx, cy + 52, BRASS_DK, 3)
    c.circle(cx, cy, 13, DARK)                            # the world, gilded
    c.circle(cx, cy, 11, (92, 132, 174, 255))
    c.poly([(cx - 7, cy - 2), (cx - 1, cy - 7), (cx + 5, cy - 1), (cx - 2, cy + 5)],
           (108, 152, 96, 255))
    c.circle(cx - 3.5, cy - 4, 3.2, (255, 255, 255, 90))


def armillary_sphere():
    c = Canvas(160, 160)
    armillary_body(c, None)
    armillary_body(c, 0.0)
    save_single(c, "ArmillarySphere")
    return c


def armillary_sphere_frames(total=12):
    for i in range(total):
        c = Canvas(160, 160)
        armillary_body(c, float(i) / total)
        c.save(os.path.join(OUT, "ArmillarySphereTurn_%d.png" % i))
    print("  ArmillarySphereTurn_0..%d.png  (160x160)" % (total - 1))


# ---------------------------------------------------------------------------
# 22. Swimming pool: two terrains and the filtration unit that fills them
# ---------------------------------------------------------------------------

def _tile_grid(c, size, tile, grout, colors, seed=1):
    """Seamless square-tile pattern. Wraps because the grid divides the size."""
    n = size // tile
    state = seed
    c.rect(0, 0, size, size, grout)
    for gy in range(n):
        for gx in range(n):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            col = colors[state % len(colors)]
            x0, y0 = gx * tile, gy * tile
            c.rect(x0 + 1.5, y0 + 1.5, x0 + tile - 1.5, y0 + tile - 1.5, col, 2)


def pool_basin_terrain():
    c = Canvas(256, 256, ss=2)
    _tile_grid(c, 256, 32, (150, 156, 158, 255),
               [(214, 220, 222, 255), (206, 213, 216, 255),
                (219, 226, 228, 255), (200, 208, 212, 255)], seed=7)
    save_terrain(c, "PoolBasin")
    return c


def pool_water_terrain():
    c = Canvas(256, 256, ss=2)
    # The same tiling, read through water: darker, bluer, with caustics on top.
    _tile_grid(c, 256, 32, (28, 84, 108, 255),
               [(56, 134, 164, 255), (48, 124, 154, 255),
                (62, 142, 172, 255), (44, 118, 148, 255)], seed=7)
    c.rect(0, 0, 256, 256, (40, 130, 180, 90))
    state = 99
    for _ in range(90):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        x = state % 256
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        y = state % 256
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        r = 5 + state % 11
        # Drawn four times so a blob crossing an edge comes back on the other.
        for ox in (0, 256, -256):
            for oy in (0, 256, -256):
                if abs(x + ox - 128) < 128 + r and abs(y + oy - 128) < 128 + r:
                    c.ring(x + ox, y + oy, r, r - 2.2, (196, 236, 250, 46))
    save_terrain(c, "PoolWater")
    return c


def pool_filter():
    """1x2 plant room: pump, sand filter, and a gauge you can read."""
    c = Canvas(160, 320)
    L, R, TOP, BOT = 12, 148, 8, 312
    mid = (L + R) / 2

    c.rect(L - 4, TOP - 4, R + 4, BOT + 4, DARK, 10)
    c.rect(L, TOP, R, BOT, (96, 104, 112, 255), 8)         # housing
    c.rect(L + 6, TOP + 6, R - 6, BOT - 6, (74, 82, 92, 255), 6)

    c.circle(mid, TOP + 78, 50, DARK)                      # sand filter tank
    c.circle(mid, TOP + 78, 46, (128, 136, 146, 255))
    c.ring(mid, TOP + 78, 46, 38, (152, 160, 170, 255))
    c.ring(mid, TOP + 78, 30, 26, (60, 66, 76, 255))
    c.circle(mid, TOP + 78, 24, (46, 52, 62, 255))
    c.circle(mid - 12, TOP + 62, 9, (255, 255, 255, 40))

    c.circle(mid, BOT - 96, 34, DARK)                      # pump volute
    c.circle(mid, BOT - 96, 30, (108, 116, 126, 255))
    c.ring(mid, BOT - 96, 30, 22, (140, 148, 158, 255))
    for i in range(6):
        a = math.radians(i * 60 + 12)
        c.line(mid, BOT - 96, mid + math.cos(a) * 20, BOT - 96 + math.sin(a) * 20,
               (58, 64, 74, 255), 4)
    c.circle(mid, BOT - 96, 7, (44, 50, 60, 255))

    for px in (L + 18, R - 18):                            # inlet and outlet
        c.rect(px - 9, TOP + 128, px + 9, BOT - 120, DARK, 5)
        c.rect(px - 6, TOP + 131, px + 6, BOT - 123, (86, 132, 156, 255), 4)
    c.rect(L + 8, BOT - 52, R - 8, BOT - 16, DARK, 5)      # gauge plate
    c.rect(L + 12, BOT - 48, R - 12, BOT - 20, (40, 46, 56, 255), 4)
    c.circle(L + 34, BOT - 34, 11, (26, 30, 38, 255))
    c.circle(L + 34, BOT - 34, 9, (210, 222, 232, 255))
    c.line(L + 34, BOT - 34, L + 40, BOT - 41, (190, 60, 52, 255), 2.4)
    for i in range(4):
        c.rect(mid + 2 + i * 16, BOT - 42, mid + 12 + i * 16, BOT - 26,
               (96, 214, 160, 255) if i < 3 else (58, 66, 78, 255), 2)
    save_rotations(c, "PoolFilter")
    return c


# ---------------------------------------------------------------------------
# 23. Hammock  (1x2, stuffable, a pawn lies in it)
# ---------------------------------------------------------------------------

def hammock():
    """Near-neutral, because the stuff colour tints the whole sprite."""
    c = Canvas(160, 320)
    mid = 80

    for py in (26, 294):                                   # end posts
        c.rect(mid - 26, py - 9, mid + 26, py + 9, DARK, 6)
        c.rect(mid - 23, py - 6, mid + 23, py + 6, (118, 104, 92, 255), 5)
        c.circle(mid - 23, py, 5, DARK)
        c.circle(mid - 23, py, 3.4, (150, 136, 122, 255))
        c.circle(mid + 23, py, 5, DARK)
        c.circle(mid + 23, py, 3.4, (150, 136, 122, 255))

    for sx in (-1, 1):                                     # gathered cords
        for k in range(5):
            x = mid + sx * (6 + k * 4)
            c.line(x, 42, mid + sx * 52, 96, (86, 78, 70, 255), 2.2)
            c.line(x, 278, mid + sx * 52, 224, (86, 78, 70, 255), 2.2)

    # The bed itself: a slack sheet, wider in the middle than at the ends.
    body = (206, 198, 186, 255)
    for y in range(96, 225):
        t = (y - 96) / 128.0
        w = 40 + 26 * math.sin(math.pi * t)
        c.rect(mid - w, y, mid + w, y + 1, body)
    c.poly([(mid - 40, 96), (mid + 40, 96), (mid + 52, 96), (mid - 52, 96)], body)

    for k in range(9):                                     # weave, following the sag
        t = (k + 0.5) / 9.0
        y = 96 + t * 128
        w = 40 + 26 * math.sin(math.pi * t)
        c.line(mid - w + 3, y, mid + w - 3, y, (176, 168, 156, 255), 2.0)
    c.line(mid, 100, mid, 220, (188, 180, 168, 255), 2.0)

    for sx in (-1, 1):                                     # selvedge
        for y in range(96, 225, 2):
            t = (y - 96) / 128.0
            w = 40 + 26 * math.sin(math.pi * t)
            c.circle(mid + sx * w, y, 2.6, (150, 142, 130, 255))

    c.rect(mid - 20, 150, mid + 20, 176, (222, 216, 206, 255), 8)   # cushion
    c.line(mid - 14, 163, mid + 14, 163, (196, 190, 180, 255), 2)
    save_rotations(c, "Hammock")
    return c

BUILDERS = {}


def _register(name, fn):
    BUILDERS[name] = fn


def main():
    import sys

    os.makedirs(OUT, exist_ok=True)
    wanted = [a.lower() for a in sys.argv[1:]]
    if wanted and wanted[0] in ("-h", "--help"):
        print("usage: generate_textures.py [%s]" % " | ".join(sorted(BUILDERS)))
        print("  no arguments redraws everything and rebuilds About/Preview.png")
        return

    unknown = [w for w in wanted if w not in BUILDERS]
    if unknown:
        print("unknown: %s\nknown: %s" % (", ".join(unknown), " ".join(sorted(BUILDERS))))
        raise SystemExit(2)

    print("Writing textures to %s" % OUT)
    made = {}
    for name in (wanted or sorted(BUILDERS)):
        result = BUILDERS[name]()
        if isinstance(result, dict):
            made.update(result)

    if wanted:
        print("Done (partial). Run Source/TextureGen/build_preview.py to refresh the preview.")
        return

    import preview
    about = os.path.join(ROOT, "About")
    os.makedirs(about, exist_ok=True)
    preview.build({k: (v.pixels(), v.w, v.h) for k, v in made.items()},
                  os.path.join(about, "Preview.png"))
    print("Done.")


def _build_knucklebone():
    return {"KnuckleboneMat": knucklebone_mat()}


def _build_shadowtheater():
    canvas = shadow_lantern_theater()
    shadow_theater_frames()
    return {"ShadowLanternTheater": canvas}


def _build_pinball():
    made = {}
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
    pinball_play_frames()
    return made


def _build_cocktail():
    canvas = cocktail_arcade()
    cocktail_arcade_frames()
    cocktail_arcade_title_frames()
    return {"CocktailArcade": canvas}


def _build_hologamepod():
    return {"HologamePod": hologame_pod()}


def _build_holotheater():
    canvas = dreamloop_holotheater()
    sample = dreamloop_projection_frames()
    return {"DreamloopHolotheater": canvas, "DreamloopProjection": sample}


def _build_vistapanel():
    made = {"VistaPanel": vista_panel()}
    made.update(("Vista" + k, v) for k, v in vista_panel_frames().items())
    return made


def _build_massagechair():
    canvas = massage_chair()
    massage_chair_frames()
    return {"MassageChair": canvas}


def _build_soakingtub():
    canvas = soaking_tub()
    electric = soaking_tub("SoakingTubElectric", electric=True)
    soaking_tub_water_frames()
    return {"SoakingTub": canvas, "SoakingTubElectric": electric}


def _build_skittles():
    canvas = skittles_lane()
    skittles_frames()
    return {"SkittlesLane": canvas}


def _build_bowling():
    canvas = bowling_lane()
    bowling_frames()
    return {"BowlingLane": canvas}


def _build_karaoke():
    canvas = karaoke_machine()
    karaoke_frames()
    return {"KaraokeMachine": canvas}


def _build_gravball():
    canvas = gravball_court()
    gravball_frames()
    return {"GravballCourt": canvas}


def _build_aquarium():
    canvas = aquarium()
    aquarium_frames()
    aquarium_fish_sprites()
    return {"Aquarium": canvas}


_register("knucklebone", _build_knucklebone)
_register("shadowtheater", _build_shadowtheater)
_register("pinball", _build_pinball)
_register("cocktail", _build_cocktail)
_register("massagechair", _build_massagechair)
_register("hologamepod", _build_hologamepod)
_register("vistapanel", _build_vistapanel)
_register("holotheater", _build_holotheater)
_register("soakingtub", _build_soakingtub)
_register("aquarium", _build_aquarium)
_register("skittles", _build_skittles)
_register("bowling", _build_bowling)
_register("karaoke", _build_karaoke)
def _build_orreries():
    made = {}
    made["TabletopOrrery"] = tabletop_orrery()
    tabletop_orrery_frames()
    made["GrandOrrery"] = grand_orrery()
    grand_orrery_frames()
    made["ArmillarySphere"] = armillary_sphere()
    armillary_sphere_frames()
    return made


def _build_pool():
    pool_basin_terrain()
    pool_water_terrain()
    return {"PoolFilter": pool_filter()}


def _build_hammock():
    return {"Hammock": hammock()}


_register("gravball", _build_gravball)
_register("orreries", _build_orreries)
_register("pool", _build_pool)
_register("hammock", _build_hammock)


if __name__ == "__main__":
    main()
