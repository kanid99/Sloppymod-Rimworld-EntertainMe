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
from views import blit_quad, blit_rect  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Buildings")
TERRAIN = os.path.join(ROOT, "Textures", "EntertainingIdeas", "Terrain")

DARK = (26, 22, 20, 255)          # shared outline colour



# ---------------------------------------------------------------------------
# Outlines
#
# RimWorld draws an object with one bold line around the whole silhouette and
# nothing like it inside: interior divisions are a darker tint of the fill at a
# fraction of the weight. pnglib has no mask and no way to erase, so the way to
# get that from stacked shapes is two passes - every piece oversized in the
# outline colour, then every piece again at true size in its fill, which buries
# the outline wherever two pieces touch and leaves it showing only around the
# outside.
#
# A piece is a tuple: ("rect", x0, y0, x1, y1, radius), ("circle", cx, cy, r),
# ("ellipse", cx, cy, rx, ry) or ("poly", [(x, y), ...]).
# ---------------------------------------------------------------------------


def darker(color, factor=0.55, alpha=None):
    """A darker tint of a colour, for interior lines and separations.

    Interior detail in RimWorld art is a shade of the thing it divides, not the
    black used around the outside. This is what produces that shade."""
    r, g, b = color[0], color[1], color[2]
    a = color[3] if len(color) > 3 else 255
    return (int(r * factor), int(g * factor), int(b * factor),
            a if alpha is None else alpha)


def _grow_poly(points, grow):
    """Push a polygon's points out from its own centre."""
    if not points:
        return points
    cx = sum(x for x, _ in points) / float(len(points))
    cy = sum(y for _, y in points) / float(len(points))
    out = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy) or 1.0
        out.append((x + dx / d * grow, y + dy / d * grow))
    return out


def draw_pieces(c, pieces, grow=0.0, color=None):
    """Draw every piece, optionally grown and forced to one colour."""
    for piece in pieces:
        kind = piece[0]
        fill = color if color is not None else piece[-1]
        if kind == "rect":
            _, x0, y0, x1, y1, r = piece[:6]
            c.rect(x0 - grow, y0 - grow, x1 + grow, y1 + grow, fill, max(0.0, r + grow))
        elif kind == "circle":
            _, cx, cy, r = piece[:4]
            c.circle(cx, cy, r + grow, fill)
        elif kind == "ellipse":
            _, cx, cy, rx, ry = piece[:5]
            c.ellipse(cx, cy, rx + grow, ry + grow, fill)
        elif kind == "poly":
            _, pts = piece[:2]
            c.poly(_grow_poly(pts, grow), fill)
        else:
            raise ValueError("unknown piece %r" % (kind,))


def silhouette(c, pieces, outline=4.0):
    """One bold line around the union of the pieces, then the pieces on top."""
    draw_pieces(c, pieces, outline, DARK)
    draw_pieces(c, pieces, 0.0)


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
    c.ellipse(64, 66, 53, 47, DARK)
    for cx, cy, rx, ry in ((44, 52, 26, 22), (86, 58, 24, 21), (60, 92, 30, 20)):
        c.ellipse(cx, cy, rx + 3.5, ry + 3.5, DARK)
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

    c.rect(3, 13, 253, 123, DARK, 10)                       # outer frame
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


def draw_shadow_theater_back(c, frame=None, total=10):
    """Facing north, from behind: the same frame and cloth, the procession
    walking the other way, and the lantern on this side of the cloth -
    nearest the eye, at the bottom - with the puppets' rods running to it."""
    import math
    x0, y0, x1, y1 = CLOTH
    p = 0.0 if frame is None else float(frame) / total
    c.rect(3, 13, 253, 123, DARK, 10)
    c.rect(7, 17, 249, 119, (104, 74, 46, 255), 8)
    flicker = 0 if frame is None else int(10 * math.sin(2 * math.pi * p * 3))
    cloth = (236 + flicker // 3, 212 + flicker // 2, 160 + flicker, 255)
    c.rect(x0, y0, x1, y1, (168, 140, 96, 255), 5)
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, cloth, 4)
    for gy in range(y0 + 4, y1 - 2, 6):
        c.line(x0 + 3, gy, x1 - 3, gy, (214, 190, 142, 90), 1.6)

    # The puppets themselves, flat cut-outs on rods, seen from their back.
    m = MirrorCanvas(c)
    shadow = (58, 40, 28, 245)
    travel = (x1 - x0) + 56
    lead = x0 - 26 + travel * p
    shadow_figure(m, "horse", lead, y1 - 8, 1.0, shadow)
    shadow_figure(m, "rider", lead + 4, y1 - 8, 1.0, shadow)
    trailing = x0 - 26 + travel * ((p + 0.5) % 1.0)
    shadow_figure(m, "horse", trailing, y1 - 6, 0.75, shadow)
    for k in range(2):
        bx = x0 - 20 + travel * ((p + 0.4 + k * 0.25) % 1.0)
        shadow_figure(m, "bird", bx, y0 + 22 + 5 * math.sin(2 * math.pi * (p * 2 + k)), 1.0, shadow)
    for fx in (lead, trailing):
        if x0 < fx < x1:
            m.line(fx, y1 - 14, fx + 10, 126, (70, 48, 30, 230), 1.6)

    wood = (86, 60, 38, 255)
    for px in (14, 242):                                    # posts
        c.rect(px - 6, 14, px + 6, 122, DARK, 5)
        c.rect(px - 4, 16, px + 4, 120, wood, 4)
    c.rect(20, 118, 236, 126, DARK, 4)                      # foot rail
    c.rect(100, 96, 156, 124, DARK, 8)                      # lantern, this side
    c.rect(104, 99, 152, 121, (74, 52, 34, 255), 6)
    lamp = 230 + (0 if frame is None else int(25 * math.sin(2 * math.pi * p * 3)))
    c.circle(128, 106, 14, (255, 206, 120, 80))
    c.circle(128, 106, 8, (255, 232, 176, lamp))
    c.rect(118, 96, 138, 101, darker((74, 52, 34, 255), 0.6), 2)


def draw_shadow_theater_side(c, frame=None, total=10):
    """Facing east (and mirrored for west): the whole front - frame, cloth,
    posts, the show on it - tipped back a little, so it reads as a narrowed
    strip running up the picture. Its top leans toward the lantern, which
    peeks out behind; its foot is toward the audience, where the light falls."""
    import math
    p = 0.0 if frame is None else float(frame) / total
    lamp = 1.0 if frame is None else 0.85 + 0.15 * math.sin(2 * math.pi * p * 3)
    if frame is not None:                                   # light on the floor in front
        for d in range(0, 40, 2):
            t = d / 40.0
            c.rect(96 + d, 20 - 10 * t, 98 + d, 236 + 10 * t,
                   (255, 214, 140, int(70 * lamp * (1 - t) ** 1.4)), 0)
    c.rect(14, 110, 42, 146, DARK, 6)                       # the lantern, behind
    c.rect(17, 113, 39, 143, (74, 52, 34, 255), 5)
    c.circle(30, 128, 6, (255, 232, 176, int(220 * lamp)))
    c.circle(30, 128, 12, (255, 206, 120, int(60 * lamp)))
    front = Canvas(256, 128)
    draw_shadow_theater(front, frame, total)
    depth = 52
    blit_quad(c, front.pixels(), 256, 128, (3, 6, 253, 127), (44 + depth, 250), (0, -244), (-depth, 0))


def _theater_views(frame=None, total=10):
    south = Canvas(256, 128)
    draw_shadow_theater(south, frame, total)
    north = Canvas(256, 128)
    draw_shadow_theater_back(north, frame, total)
    east = Canvas(128, 256)
    draw_shadow_theater_side(east, frame, total)
    return {"south": south, "north": north, "east": east, "west": mirrored(east)}


def mirrored(canvas):
    """A finished canvas flipped left to right, as a new canvas."""
    px, w, h = canvas.pixels(), canvas.w, canvas.h
    out = Canvas(w, h, ss=1)
    for y in range(h):
        for x in range(w):
            si = (y * w + x) * 4
            di = (y * w + (w - 1 - x)) * 4
            out.buf[di:di + 4] = px[si:si + 4]
    return out


def shadow_lantern_theater():
    views = _theater_views()
    for facing, view in views.items():
        view.save(os.path.join(OUT, "ShadowLanternTheater_%s.png" % facing))
    print("  ShadowLanternTheater_{north,east,south,west}.png")
    return views["south"]


def shadow_theater_frames(total=10):
    """One strip per facing (CompAnimatedScreen perFacing). The frames redraw
    the whole building, so each is its facing's view at that moment."""
    for i in range(total):
        for facing, view in _theater_views(i, total).items():
            view.save(os.path.join(OUT, "ShadowLanternTheaterPlay%s_%d.png" % (facing.capitalize(), i)))
    print("  ShadowLanternTheaterPlay{North,East,South,West}_0..%d.png" % (total - 1))


# ---------------------------------------------------------------------------
# 3. Pinball machines  (four themed tables, 1x2 footprint, rotatable)
#
# Each facing is its own drawing rather than a turn of one picture. RimWorld
# looks down at a slant from the south, so anything upright shows the face that
# points south and rises up the screen from where it stands:
#
#   south   the player's end is nearest. The backbox stands at the far end,
#           against the wall, showing its backglass; the front apron, coin
#           door and legs show at the bottom.
#   north   the backbox is nearest and shows its plain back panel, hiding the
#           back of the playfield; the flippers are at the far end.
#   east/west  side-on: legs, a cabinet sloping down toward the player, and
#           the backbox standing up at the back.
#
# Turning the south drawing instead put the backglass flat on the floor, upside
# down facing north, and sideways on the side views.
#
# Everything on the playfield is placed in (u, v): u runs from the back of the
# playfield (0) to the flippers (1), v across it from the player's left (0) to
# their right (1). Each view projects (u, v) onto its own canvas, and the play
# overlay goes through the same projection, which is what keeps the ball on
# the bumpers painted on every facing.
# ---------------------------------------------------------------------------
# The machine is drawn bigger than its 1x2 footprint (drawSize 2x2), because a
# pinball side-on is about as tall as it is long: squeezed into a 2x1 strip it
# read as a low bench. Seen from the ends it still fits its own two tiles and
# is drawn 160 wide, then centred in the square; side-on it stands on the
# south edge of its footprint and rises over the tile behind, the way tall
# furniture does.
PB_W, PB_H = 160, 320             # north and south, before centring
PB_SIDE_SQ = 320                  # east and west, before centring
# Facing south, the backbox stands up off the back of the footprint and over
# the tile behind - against the wall, when there is one - the way a tall
# cabinet does, rather than squeezed inside the footprint in front of it. The
# south drawing is that much taller, and every texture is a square big enough
# for it: 160 px to a tile throughout, so the other facings only gain margin.
PB_S_RISE = 96                    # how far the south backbox rises past the footprint
PB_SQ = PB_H + PB_S_RISE          # every saved texture, square: drawSize 2.6
PB_FOOT_Y = 238                   # side-on: the near feet, at the footprint's south edge
PB_METAL = (158, 162, 172, 255)
PB_CHROME = (212, 214, 222, 255)

# (u, v, radius as a share of the playfield's width)
PB_BUMPERS = [(0.30, 0.33, 0.13), (0.24, 0.69, 0.112), (0.48, 0.48, 0.103)]
PB_TARGETS_U = (0.13, 0.17)
PB_TARGETS_V = [(0.19, 0.30), (0.345, 0.455), (0.50, 0.61)]
PB_LANE = (0.90, 0.07, 0.71)      # shooter lane: v, from u, to u
PB_RAIL = (0.09, 0.10, 0.52)      # guide rail on the left
PB_SLING = (0.05, 0.29, 0.75, 0.80, 0.86)   # outer v, inner v, top/tip/bottom u
PB_FLIP_U, PB_FLIP_TIP_U, PB_FLIP_UP_U = 0.915, 0.865, 0.75
PB_FLIPPERS = [(0.414, 0.207), (0.586, 0.793)]   # (pivot v, tip v), left then right
PB_BALL_REST = (0.65, 0.90)
PB_BALL_PATH = [(0.72, 0.90), (0.415, 0.90), (0.165, 0.82), (0.225, 0.64),
                (0.29, 0.38), (0.46, 0.47), (0.71, 0.33), (0.885, 0.655)]

# The same machine seen four ways has to keep its proportions, so heights are
# shared: legs PB_LEG, the cabinet body PB_BODY deep at the player's end, and
# the backbox standing PB_BOX_RISE above the playfield with a PB_LID lid.
PB_LEG = 36
PB_BODY = 30
PB_BOX_RISE = 96
PB_LID = 15
PB_BOX_THICK = 30                 # side-on, back to front
# South: the backbox and its glass, the lockbar and the apron below it.
PB_BOX_TOP, PB_BOX_BOT = 4, 98
PB_GLASS = (20, 24, 140, 86)
PB_SCORE_TOP = 66
PB_LAMP_Y = 92
PB_CAB_BOT = 316 - 4 - PB_LEG     # cabinet underside, both end views
PB_LOCKBAR = PB_CAB_BOT - PB_BODY - 10
# North: where the backbox's back panel starts hiding the playfield.
PB_NORTH_BOX_TOP = 170
PB_NORTH_BOX_BOT = PB_CAB_BOT - 12
# East/west: the cabinet runs from x 24 to x 298, its top sloping down toward
# the player, and the backbox's side stands at the back end.
PB_SIDE_BACK, PB_SIDE_FRONT = 24, 298
PB_SIDE_DEPTH = 44                # how deep the top face reads, foreshortened
PB_SIDE_BOTTOM = PB_FOOT_Y - 4 - PB_LEG
PB_SIDE_SLOPE = 8                 # how much higher the back of the cabinet is
PB_SIDE_TOP = PB_SIDE_BOTTOM - PB_BODY - PB_SIDE_SLOPE - PB_SIDE_DEPTH
PB_SIDE_BOX = (22, 22 + PB_BOX_THICK)   # backbox, back to front
PB_SIDE_BOX_TOP = PB_SIDE_TOP - PB_BOX_RISE
PB_SIDE_GLASS = (PB_SIDE_BOX_TOP + 18, PB_SIDE_TOP - 4)   # lit edge of the backglass


def lighter(color, amount=0.28):
    """A lighter tint of a colour, for the tops of things catching the light."""
    r, g, b = color[0], color[1], color[2]
    a = color[3] if len(color) > 3 else 255
    return (int(r + (255 - r) * amount), int(g + (255 - g) * amount),
            int(b + (255 - b) * amount), a)


def _side_top(x):
    """The top edge of the cabinet's top face in the side view, at x."""
    return PB_SIDE_TOP + (x - PB_SIDE_BACK) * float(PB_SIDE_SLOPE) / (PB_SIDE_FRONT - PB_SIDE_BACK)


class MirrorCanvas:
    """Draws onto a canvas flipped left to right, so the west side view is the
    east one drawn again rather than a second copy of the code."""

    def __init__(self, canvas):
        self.c = canvas
        self.w, self.h = canvas.w, canvas.h

    def rect(self, x0, y0, x1, y1, color, radius=0.0):
        self.c.rect(self.w - x1, y0, self.w - x0, y1, color, radius)

    def frame(self, x0, y0, x1, y1, color, width=1.0, radius=0.0):
        self.c.frame(self.w - x1, y0, self.w - x0, y1, color, width, radius)

    def ellipse(self, cx, cy, rx, ry, color):
        self.c.ellipse(self.w - cx, cy, rx, ry, color)

    def circle(self, cx, cy, r, color):
        self.c.circle(self.w - cx, cy, r, color)

    def ring(self, cx, cy, r_outer, r_inner, color):
        self.c.ring(self.w - cx, cy, r_outer, r_inner, color)

    def poly(self, points, color):
        self.c.poly([(self.w - x, y) for x, y in points], color)

    def line(self, x0, y0, x1, y1, color, width=1.0):
        self.c.line(self.w - x0, y0, self.w - x1, y1, color, width)


class PinballView:
    """Where a point on the playfield lands in one facing's drawing."""

    def __init__(self, facing):
        self.facing = facing
        self.side = facing in ("east", "west")
        self.scale = 0.75 if self.side else 1.0     # for line widths

    def pt(self, u, v):
        if self.facing == "south":
            return 24 + v * 112, 104 + u * (PB_LOCKBAR + PB_S_RISE - 112)
        if self.facing == "north":
            # Seen from the other end: the player's left is on the right.
            return 136 - v * 112, PB_NORTH_BOX_TOP + 20 - u * (PB_NORTH_BOX_TOP - 10)
        # East, drawn as is; west goes through a MirrorCanvas, which turns the
        # player's left from the top of the strip to the bottom unless v is
        # flipped back here.
        if self.facing == "west":
            v = 1.0 - v
        x = PB_SIDE_BOX[1] + 6 + u * 228
        return x, _side_top(x) + 4 + v * (PB_SIDE_DEPTH - 8)

    def radii(self, r):
        if self.side:
            return r * 104, r * 36
        return r * 112, r * 104

    def hidden(self, u, v):
        """True where the backbox stands between the camera and the playfield."""
        return self.facing == "north" and self.pt(u, v)[1] > PB_NORTH_BOX_TOP - 4

    def canvas(self):
        if self.side:
            base = Canvas(PB_SIDE_SQ, PB_SIDE_SQ)
        else:
            base = Canvas(PB_W, PB_H + (PB_S_RISE if self.facing == "south" else 0))
        return base, (MirrorCanvas(base) if self.facing == "west" else base)

    def save(self, base, path):
        """Write a drawing out square. Every facing is centred on the
        footprint, except south: that one fills the square from the bottom,
        and drawOffsetSouth lifts it so its footprint part sits on the
        footprint and its backbox rises over the tile behind."""
        px = base.pixels()
        w, h = base.w, base.h
        pad_x = (PB_SQ - w) // 2
        pad_y = PB_SQ - h if self.facing == "south" else (PB_SQ - h) // 2
        sq = bytearray(PB_SQ * PB_SQ * 4)
        for y in range(h):
            row = y * w * 4
            at = ((y + pad_y) * PB_SQ + pad_x) * 4
            sq[at:at + w * 4] = px[row:row + w * 4]
        write_png(path, PB_SQ, PB_SQ, sq)


# A seven-segment digit, the way a real score reel reads.
SEVEN_SEG = {
    0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg",
    5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


def seg_digit(c, x, y, w, h, value, on, off):
    """One seven-segment digit with its top-left at (x, y)."""
    t = max(1.4, w * 0.22)
    mid = y + h / 2.0
    places = {
        "a": (x, y, x + w, y + t),
        "b": (x + w - t, y, x + w, mid),
        "c": (x + w - t, mid, x + w, y + h),
        "d": (x, y + h - t, x + w, y + h),
        "e": (x, mid, x + t, y + h),
        "f": (x, y, x + t, mid),
        "g": (x, mid - t / 2, x + w, mid + t / 2),
    }
    lit = SEVEN_SEG.get(value, "")
    for name, (x0, y0, x1, y1) in places.items():
        c.rect(x0, y0, x1, y1, on if name in lit else off, 1)


def pb_reels(c, top, digits_left, digits_right, glow):
    """Two score windows across the bottom of the backglass, one per player."""
    dark = (18, 16, 20, 255)
    off = (52, 26, 18, 255)
    for x0, digits in ((24, digits_left), (82, digits_right)):
        c.rect(x0, top, x0 + 54, top + 18, (10, 9, 12, 255), 3)
        c.rect(x0 + 2, top + 2, x0 + 52, top + 16, dark, 2)
        for i, value in enumerate(digits):
            seg_digit(c, x0 + 4.5 + i * 8, top + 3, 5.8, 12, value, glow, off)


def _pb_playfield(c, view, field, accent, accent2):
    """Lanes, targets, bumpers, slingshots, flippers and the waiting ball."""
    p, s = view.pt, view.scale

    lane_v, lane_u0, lane_u1 = PB_LANE
    c.line(*p(lane_u0, lane_v), *p(lane_u1, lane_v), (238, 238, 244, 150), 3 * s)
    rail_v, rail_u0, rail_u1 = PB_RAIL
    c.line(*p(rail_u0, rail_v), *p(rail_u1, rail_v), (238, 238, 244, 105), 2.4 * s)

    u0, u1 = PB_TARGETS_U
    for v0, v1 in PB_TARGETS_V:
        c.poly([p(u0, v0), p(u0, v1), p(u1, v1), p(u1, v0)], accent2)

    # Pop bumpers stand up off the playfield, so the cap sits above its skirt.
    lift = 3 if view.side else 1.5
    for u, v, r in PB_BUMPERS:
        x, y = p(u, v)
        rx, ry = view.radii(r)
        c.ellipse(x, y, rx + 2, ry + 2, darker(field, 0.5))
        c.ellipse(x, y, rx, ry, darker(accent, 0.6))
        c.ellipse(x, y - lift, rx, ry, accent)
        c.ellipse(x, y - lift, rx * 0.62, ry * 0.62, (250, 250, 252, 255))
        c.ellipse(x, y - lift, rx * 0.34, ry * 0.34, accent2)
        c.ellipse(x - rx * 0.3, y - lift - ry * 0.3, rx * 0.16, ry * 0.16, (255, 255, 255, 190))

    out_v, in_v, top_u, tip_u, bot_u = PB_SLING
    for mirror in (False, True):
        ov, iv = (1 - out_v, 1 - in_v) if mirror else (out_v, in_v)
        c.poly([p(tip_u, ov), p(top_u, iv), p(bot_u, iv)], darker(field, 0.5))
        inset = 0.03 if mirror else -0.03
        c.poly([p(tip_u, ov - inset), p(top_u + 0.02, iv + inset), p(bot_u - 0.02, iv + inset)],
               accent2)
        c.line(*p(tip_u, ov), *p(top_u, iv), (255, 255, 255, 120), 2 * s)   # rubber
        c.line(*p(tip_u, ov), *p(bot_u, iv), (255, 255, 255, 120), 2 * s)

    for pivot_v, tip_v in PB_FLIPPERS:
        x0, y0 = p(PB_FLIP_U, pivot_v)
        x1, y1 = p(PB_FLIP_TIP_U, tip_v)
        c.line(x0, y0, x1, y1, darker(field, 0.45), 12 * s)
        c.line(x0, y0, x1, y1, accent, 8 * s)
        c.circle(x0, y0, 4.2 * s, (236, 236, 240, 255))

    x, y = p(*PB_BALL_REST)
    pb_ball(c, x, y, view)


def pb_ball(c, x, y, view, shade=(20, 22, 30, 255)):
    r = 4.4 if view.side else 5.4
    c.circle(x, y, r + 1.3, darker(shade, 1.0))
    c.circle(x, y, r, (226, 228, 236, 255))
    c.circle(x - r * 0.3, y - r * 0.3, r * 0.4, (255, 255, 255, 220))


def _pb_glass(c, pts, alpha=16):
    """Two streaks of reflected light across the playfield glass."""
    c.poly(pts[0], (255, 255, 255, alpha))
    c.poly(pts[1], (255, 255, 255, alpha // 2))


def pinball_south(cab, cab_dark, field, accent, accent2, glass, motif):
    """The player's end nearest: backglass at the far end, apron and legs here."""
    view = PinballView("south")
    base, c = view.canvas()
    L, R, mid = 16, 144, 80
    box_l, box_r = 10, 150
    lock = PB_LOCKBAR + PB_S_RISE
    apron = lock + 10
    cab_bot, floor = PB_CAB_BOT + PB_S_RISE, 316 + PB_S_RISE
    silhouette(c, [
        ("rect", L + 1, floor - 7, L + 15, floor, 2, darker(PB_METAL, 0.6)),     # leveller feet
        ("rect", R - 15, floor - 7, R - 1, floor, 2, darker(PB_METAL, 0.6)),
        ("rect", L + 4, cab_bot - 2, L + 12, floor - 4, 2, PB_METAL),        # front legs
        ("rect", R - 12, cab_bot - 2, R - 4, floor - 4, 2, PB_METAL),
        ("rect", L, 90, R, cab_bot, 6, cab),                            # cabinet
        ("rect", L - 5, lock - 8, L + 2, lock + 4, 2, accent2),            # flipper buttons
        ("rect", R - 2, lock - 8, R + 5, lock + 4, 2, accent2),
        ("rect", box_l, PB_BOX_TOP, box_r, PB_BOX_BOT, 6, cab),           # backbox
    ])
    for x in (L + 6, R - 10):                                              # chrome on the legs
        c.line(x, cab_bot + 1, x, floor - 6, (255, 255, 255, 90), 1.5)

    # Playfield under glass, with the rails of the cabinet either side of it.
    c.rect(L + 5, PB_BOX_BOT, R - 5, lock + 3, darker(cab_dark, 0.55), 4)
    c.rect(L + 8, PB_BOX_BOT, R - 8, lock, field, 3)
    _pb_playfield(c, view, field, accent, accent2)
    _pb_glass(c, ([(28, lock - 4), (46, lock - 4), (112, 100), (94, 100)],
                  [(58, lock - 4), (66, lock - 4), (132, 100), (124, 100)]))
    c.line(L + 1.5, PB_BOX_BOT, L + 1.5, lock + 1, (255, 255, 255, 40), 2)  # rail highlight

    # The backbox stands up off the back of the cabinet, so it throws a shadow
    # down the glass in front of it: this is most of what makes it read upright.
    for k in range(6):
        c.rect(L + 5, PB_BOX_BOT + k * 2, R - 5, PB_BOX_BOT + k * 2 + 2, (0, 0, 0, 84 - k * 14))

    # Lockbar, then the apron: the front face, in its own shade.
    c.rect(L + 1, lock - 1, R - 1, apron, (182, 186, 196, 255), 3)
    c.rect(L + 3, lock, R - 3, lock + 3, (230, 232, 240, 255), 2)
    c.rect(L, apron, R, cab_bot - 10, cab_dark)
    c.rect(L, apron + 8, R, cab_bot, cab_dark, 6)
    c.line(L, apron + 0.5, R, apron + 0.5, darker(cab_dark, 0.6), 1.5)
    c.rect(mid - 16, apron + 3, mid + 16, apron + 25, (24, 22, 26, 255), 3)   # coin door
    c.rect(mid - 14, apron + 5, mid + 14, apron + 23, (40, 38, 44, 255), 2)
    for sx in (-1, 1):
        c.rect(mid + sx * 8 - 3, apron + 8, mid + sx * 8 + 3, apron + 16, accent, 1)   # coin slots
    c.rect(mid - 7, apron + 18, mid + 7, apron + 21, (18, 16, 20, 255), 1)          # coin return

    # Shooter rod, on the player's right, pointing out of the apron at them.
    rod_x = R - 16
    c.circle(rod_x, apron + 8, 4.6, (120, 124, 134, 255))                 # collar
    c.rect(rod_x - 2, apron + 8, rod_x + 2, apron + 17, PB_CHROME, 1.5)
    c.circle(rod_x, apron + 19, 7.2, DARK)
    c.circle(rod_x, apron + 19, 6, accent)
    c.circle(rod_x - 2, apron + 17, 2.2, (255, 255, 255, 160))

    # Backbox: the lid catching the light, then the front with its backglass.
    lid = PB_BOX_TOP + PB_LID
    c.rect(box_l, PB_BOX_TOP, box_r, lid, lighter(cab), 6)
    c.rect(box_l, lid - 5, box_r, lid, lighter(cab))
    c.line(box_l, lid, box_r, lid, darker(cab, 0.6), 1.5)
    gx0, gy0, gx1, gy1 = PB_GLASS
    c.rect(gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2, (14, 12, 16, 255), 4)
    c.rect(gx0, gy0, gx1, gy1, glass, 3)
    motif(c, gx0, gx1, 8)
    pb_reels(c, PB_SCORE_TOP, (0, 1, 2, 4, 8, 0), (0, 0, 3, 9, 6, 0), accent)
    c.rect(gx0, gy0, gx1, gy0 + 12, (255, 255, 255, 34), 3)                # glass sheen
    for i in range(6):                                                     # marquee lamps
        c.circle(25 + i * 22, PB_LAMP_Y, 3.2, (255, 244, 208, 230))
    c.line(box_l + 1.5, lid + 1, box_l + 1.5, PB_BOX_BOT - 2, (255, 255, 255, 44), 2)
    return base


def pinball_north(cab, cab_dark, field, accent, accent2, glass, motif):
    """The backbox nearest, showing its back; the flippers at the far end."""
    view = PinballView("north")
    base, c = view.canvas()
    L, R, mid = 16, 144, 80
    box_l, box_r = 10, 150
    rod_x = L + 16                         # the player's right is on our left
    box_bot = PB_NORTH_BOX_BOT
    silhouette(c, [
        ("rect", L + 1, 309, L + 15, 316, 2, darker(PB_METAL, 0.6)),
        ("rect", R - 15, 309, R - 1, 316, 2, darker(PB_METAL, 0.6)),
        ("rect", L + 4, PB_CAB_BOT - 2, L + 12, 312, 2, PB_METAL),        # back legs
        ("rect", R - 12, PB_CAB_BOT - 2, R - 4, 312, 2, PB_METAL),
        ("circle", rod_x, 9, 6.2, accent),                                 # shooter knob
        ("rect", L, 14, R, PB_CAB_BOT, 6, cab),                            # cabinet
        ("rect", L - 5, 26, L + 2, 38, 2, accent2),                        # flipper buttons
        ("rect", R - 2, 26, R + 5, 38, 2, accent2),
        ("rect", box_l, PB_NORTH_BOX_TOP, box_r, box_bot, 6, cab),        # backbox
    ])
    for x in (L + 6, R - 10):
        c.line(x, PB_CAB_BOT + 1, x, 310, (255, 255, 255, 90), 1.5)
    c.circle(rod_x - 2, 7, 2.1, (255, 255, 255, 150))

    # Lockbar at the far end, then the playfield running back to the backbox.
    c.rect(L + 1, 16, R - 1, 27, (182, 186, 196, 255), 3)
    c.rect(L + 3, 17, R - 3, 20, (230, 232, 240, 255), 2)
    c.rect(L + 5, 27, R - 5, PB_NORTH_BOX_TOP + 6, darker(cab_dark, 0.55), 4)
    c.rect(L + 8, 30, R - 8, PB_NORTH_BOX_TOP + 6, field, 3)
    _pb_playfield(c, view, field, accent, accent2)
    _pb_glass(c, ([(28, PB_NORTH_BOX_TOP), (46, PB_NORTH_BOX_TOP), (112, 32), (94, 32)],
                  [(58, PB_NORTH_BOX_TOP), (66, PB_NORTH_BOX_TOP), (132, 32), (124, 32)]))
    c.line(L + 1.5, 28, L + 1.5, PB_NORTH_BOX_TOP, (255, 255, 255, 40), 2)
    for k in range(4):                     # contact shadow where the box stands
        c.rect(L + 5, PB_NORTH_BOX_TOP - 8 + k * 2, R - 5, PB_NORTH_BOX_TOP - 6 + k * 2,
               (0, 0, 0, 20 + k * 16))

    # Backbox from behind: a lid, then a plain back panel - no art on this side.
    back = darker(cab, 0.72)
    lid = PB_NORTH_BOX_TOP + PB_LID
    c.rect(box_l, PB_NORTH_BOX_TOP, box_r, lid, lighter(cab), 6)
    c.rect(box_l, lid - 5, box_r, lid, lighter(cab))
    c.rect(box_l, lid, box_r, box_bot, back, 6)
    c.rect(box_l, lid, box_r, box_bot - 10, back)
    c.line(box_l, lid, box_r, lid, darker(cab, 0.5), 1.5)
    c.frame(box_l + 8, PB_NORTH_BOX_TOP + 20, box_r - 8, box_bot - 8, darker(back, 0.7), 1.5, 4)
    for row in range(5):                   # vent slots
        y = PB_NORTH_BOX_TOP + 30 + row * 7
        for x0 in (28, 94):
            c.rect(x0, y, x0 + 38, y + 3, darker(back, 0.5), 1.5)
    c.circle(mid, PB_NORTH_BOX_TOP + 44, 4.6, PB_METAL)                    # lock
    c.circle(mid, PB_NORTH_BOX_TOP + 44, 1.6, DARK)
    c.rect(mid - 16, box_bot - 22, mid + 16, box_bot - 14, (214, 204, 176, 255), 1.5)   # maker's plate
    c.line(box_l + 1.5, PB_NORTH_BOX_TOP + 14, box_l + 1.5, box_bot - 4, (255, 255, 255, 36), 2)

    # The back of the cabinet under the box, in shadow.
    c.rect(L, box_bot, R, PB_CAB_BOT, darker(cab_dark, 0.8), 6)
    c.rect(L, box_bot, R, PB_CAB_BOT - 6, darker(cab_dark, 0.8))
    c.line(L, box_bot + 0.5, R, box_bot + 0.5, darker(cab_dark, 0.5), 1.5)
    return base


def pinball_side(facing, cab, cab_dark, field, accent, accent2, glass, motif):
    """Side-on: drawn facing east, and mirrored for west."""
    view = PinballView(facing)
    base, c = view.canvas()
    B, F, bot, depth = PB_SIDE_BACK, PB_SIDE_FRONT, PB_SIDE_BOTTOM, PB_SIDE_DEPTH
    bx0, bx1 = PB_SIDE_BOX
    gy0, gy1 = PB_SIDE_GLASS
    top = _side_top
    foot = PB_FOOT_Y - 4                   # where the near legs meet the floor
    far = darker(PB_METAL, 0.62)
    # The far pair of legs stands further back, so it shows higher up and a
    # little in from the near pair, and in shade; the near pair is drawn over it.
    silhouette(c, [
        ("rect", B + 30, foot - 14, B + 48, foot - 8, 2, darker(far, 0.7)),
        ("rect", F - 48, foot - 14, F - 30, foot - 8, 2, darker(far, 0.7)),
        ("poly", [(B + 36, bot - 6), (B + 45, bot - 6), (B + 42, foot - 12), (B + 34, foot - 12)], far),
        ("poly", [(F - 45, bot - 6), (F - 36, bot - 6), (F - 34, foot - 12), (F - 42, foot - 12)], far),
    ])
    silhouette(c, [
        ("rect", B, foot - 2, B + 20, foot + 4, 2, darker(PB_METAL, 0.6)),       # leveller feet
        ("rect", F - 20, foot - 2, F, foot + 4, 2, darker(PB_METAL, 0.6)),
        ("poly", [(B + 11, bot - 6), (B + 21, bot - 6), (B + 14, foot), (B + 5, foot)], PB_METAL),
        ("poly", [(F - 21, bot - 6), (F - 11, bot - 6), (F - 5, foot), (F - 14, foot)], PB_METAL),
        ("poly", [(B, top(B)), (F, top(F)), (F, bot), (B, bot)], cab),    # cabinet
        ("rect", F - 2, bot - 20, F + 10, bot - 15, 1, PB_CHROME),        # shooter rod
        ("circle", F + 13, bot - 17.5, 6, accent),                         # and its knob
        ("rect", bx0, PB_SIDE_BOX_TOP, bx1, top(bx1) + depth, 4, cab),    # backbox
    ])
    c.line(B + 13, bot - 2, B + 8, foot - 2, (255, 255, 255, 80), 1.5)    # chrome on the legs
    c.line(F - 14, bot - 2, F - 9, foot - 2, (255, 255, 255, 80), 1.5)
    c.circle(F + 11, bot - 19.5, 2, (255, 255, 255, 150))

    # Top face: the playfield under glass, foreshortened, rising to the back.
    rim = darker(cab_dark, 0.55)
    c.poly([(bx1, top(bx1)), (F, top(F)), (F, top(F) + depth), (bx1, top(bx1) + depth)], rim)
    c.poly([(bx1 + 2, top(bx1) + 2), (F - 12, top(F - 12) + 2),
            (F - 12, top(F - 12) + depth - 2), (bx1 + 2, top(bx1) + depth - 2)], field)
    _pb_playfield(c, view, field, accent, accent2)
    for x0, w, a in ((110, 30, 18), (172, 12, 12)):                        # glass streaks
        c.poly([(x0, top(x0) + depth - 2), (x0 + w, top(x0 + w) + depth - 2),
                (x0 + w + 26, top(x0 + w + 26) + 2), (x0 + 26, top(x0 + 26) + 2)],
               (255, 255, 255, a))
    c.poly([(F - 12, top(F - 12)), (F, top(F)), (F, top(F) + depth),
            (F - 12, top(F - 12) + depth)], (182, 186, 196, 255))         # lockbar
    c.line(F - 11, top(F - 11) + 1, F - 11, top(F - 11) + depth - 1, (230, 232, 240, 255), 2)
    for k in range(4):                     # the backbox shades the glass in front of it
        c.rect(bx1 + k * 3, top(bx1) + 1, bx1 + k * 3 + 3, top(bx1) + depth - 1,
               (0, 0, 0, 70 - k * 16))

    # Side panel, with the table's colours run along it as side art.
    y_edge = lambda x: top(x) + depth
    c.poly([(B, y_edge(B)), (F, y_edge(F)), (F, bot), (B, bot)], cab)
    c.line(bx1, y_edge(bx1) + 1, F, y_edge(F) + 1, lighter(cab, 0.35), 2)
    c.poly([(bx1 + 14, bot - 9), (F - 34, bot - 17), (F - 27, bot - 11), (bx1 + 18, bot - 4)], accent)
    c.poly([(bx1 + 36, bot - 18), (F - 64, bot - 23), (F - 60, bot - 20), (bx1 + 39, bot - 15)], accent2)
    c.rect(B, bot - 3, F, bot, darker(cab, 0.7))
    c.circle(F - 18, y_edge(F - 18) + 7, 4.6, DARK)                        # flipper button
    c.circle(F - 18, y_edge(F - 18) + 7, 3.4, accent2)

    # Backbox side: a lid on top, the table's accent across it, and the lit
    # edge of the backglass at the front.
    bt = PB_SIDE_BOX_TOP
    lid = bt + PB_LID - 3
    c.rect(bx0, bt, bx1, lid, lighter(cab), 4)
    c.rect(bx0, lid - 4, bx1, lid, lighter(cab))
    c.line(bx0, lid, bx1, lid, darker(cab, 0.6), 1.5)
    c.rect(bx0, bt + 62, bx1, bt + 69, accent)
    c.rect(bx0, bt + 70, bx1, bt + 72, accent2)
    c.rect(bx1 - 4, gy0, bx1 - 1, gy1, glass, 1)
    c.rect(bx1 - 3, gy0 + 2, bx1 - 2, gy1 - 2, lighter(glass, 0.45))
    c.line(bx0 + 1.5, lid + 2, bx0 + 1.5, y_edge(bx0) - 2, (255, 255, 255, 40), 2)
    for y in (bt + 24, bt + 46):                                           # hinges
        c.rect(bx0 - 1, y, bx0 + 3, y + 8, PB_METAL, 1)
    return base


def pinball(name, cab, cab_dark, field, accent, accent2, glass, motif):
    """One table in all four facings. Returns the south view for the preview."""
    colours = (cab, cab_dark, field, accent, accent2, glass, motif)
    views = {
        "south": pinball_south(*colours),
        "north": pinball_north(*colours),
        "east": pinball_side("east", *colours),
        "west": pinball_side("west", *colours),
    }
    for facing, canvas in views.items():
        PinballView(facing).save(canvas, os.path.join(OUT, "%s_%s.png" % (name, facing)))
    print("  %s_{north,east,south,west}.png  (%dx%d)" % (name, PB_SQ, PB_SQ))
    return views["south"]


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
        c.ellipse(lx, 72, 22, 17, darker((48, 46, 66, 255), 0.5))
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
SCREEN_BG = (10, 10, 16, 255)
RING = (46, 46, 114, 114)         # corridor the miner and the bugs run
ROCK = (150, 104, 54, 255)        # tunnel walls
ORE_COUNT = 24


def on_screen(x, y, pad=0.0):
    """True while a sprite is far enough inside the glass to be drawn whole.

    Nothing here is clipped by the renderer - these are plain overlays laid on
    the cabinet - so anything drawn outside the glass lands on the table top.
    Every moving part is tested against this before it is drawn."""
    x0, y0, x1, y1 = SCREEN
    return x0 + pad <= x <= x1 - pad and y0 + pad <= y <= y1 - pad



def screen_title(c, string, y, scale, color):
    """Centre a line inside the glass, or fail loudly if it does not fit.

    Text drawn past the screen edge lands on the cabinet, which is exactly the
    kind of thing that ships unnoticed. Better to break the build."""
    from preview import text, text_width

    x0, _, x1, _ = SCREEN
    width = text_width(string, scale)
    room = (x1 - x0) - 4
    if width > room:
        raise ValueError("%r is %dpx at scale %d but the screen only has %dpx"
                         % (string, width, scale, room))
    text(c, string, (x0 + x1) / 2.0 - width / 2.0, y, scale, color)


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


# ---------------------------------------------------------------------------
# Game one: DEEP DRILL. A miner works the tunnels for ore while the things
# that live down there work their way toward the miner.
# ---------------------------------------------------------------------------

def draw_bug(c, gx, gy, col, dx, dy, wobble):
    """A megaspider from above: low body, too many legs, two red eyes."""
    import math
    for side in (-1, 1):                                    # legs, scuttling
        for k in range(3):
            a = math.radians(38 + k * 52) * side
            reach = 9 + (2 if (k + wobble) % 2 else 0)
            c.line(gx, gy, gx + math.sin(a) * reach * side, gy - math.cos(a) * reach * 0.8,
                   (col[0] // 2, col[1] // 2, col[2] // 2, 255), 2)
    c.ellipse(gx, gy + 1, 8, 6.5, (col[0] // 2, col[1] // 2, col[2] // 2, 255))
    c.ellipse(gx, gy, 7, 5.5, col)                          # abdomen
    hx, hy = gx + dx * 5.5, gy + dy * 5.5
    c.ellipse(hx, hy, 4.5, 4, col)                          # head
    for side in (-1, 1):
        c.circle(hx - dy * side * 2, hy + dx * side * 2, 1.5, (255, 90, 70, 255))


def draw_miner(c, x, y, dx, dy, step):
    """A colonist in a hard hat, lamp pointing the way they are going."""
    c.circle(x, y, 9.5, (24, 24, 30, 255))
    c.circle(x, y, 8, (86, 132, 186, 255))                  # jacket
    c.circle(x, y - 1, 5.5, (226, 190, 156, 255))           # face
    c.circle(x, y - 3, 6, (236, 198, 64, 255))              # hard hat
    lx, ly = x + dx * 8, y + dy * 8
    c.circle(lx, ly, 3.2, (255, 244, 188, 255 if step % 2 else 190))   # lamp
    c.circle(lx, ly, 1.6, (255, 255, 240, 255))


def draw_drill_screen(c, frame=None, total=16):
    """The play screen: tunnels, ore, one miner, three bugs."""
    import math
    x0, y0, x1, y1 = SCREEN
    c.rect(x0, y0, x1, y1, SCREEN_BG, 8)

    # Tunnel walls: an outer gallery and four worked-out chambers.
    c.frame(37, 37, 123, 123, ROCK, 2.5, 5)
    c.frame(48, 48, 78, 68, ROCK, 2.5, 3)
    c.frame(84, 48, 112, 68, ROCK, 2.5, 3)
    c.frame(48, 92, 78, 112, ROCK, 2.5, 3)
    c.frame(84, 92, 112, 112, ROCK, 2.5, 3)
    c.rect(72, 74, 90, 86, ROCK, 3)                         # the nest
    c.rect(75, 77, 87, 83, SCREEN_BG, 2)

    p = 0.0 if frame is None else float(frame) / total
    step = frame if frame is not None else 0

    # Ore in the corridor, taken as the miner passes it.
    for k in range(ORE_COUNT):
        pk = float(k) / ORE_COUNT
        if frame is not None and pk <= p:
            continue
        px, py, _, _ = ring_point(pk)
        c.rect(px - 2, py - 2, px + 2, py + 2, (226, 188, 108, 255), 1)

    # Rich seams in the corners, glinting the way the big ones do.
    if frame is None or (step // 2) % 2 == 0:
        for corner in (0.0, 0.25, 0.5, 0.75):
            if frame is not None and corner <= p:
                continue
            px, py, _, _ = ring_point(corner + 0.0001)
            c.circle(px, py, 4.6, (152, 226, 240, 255))

    # Two bugs working the corridor, a third sat on the nest.
    for lead, col in ((0.30, (176, 72, 64, 255)), (0.58, (150, 108, 186, 255))):
        gx, gy, gdx, gdy = ring_point(p + lead)
        draw_bug(c, gx, gy, col, gdx, gdy, step)
    draw_bug(c, 81, 78, (104, 150, 92, 255), 0, 1, step + 1)

    mx, my, mdx, mdy = ring_point(p)
    draw_miner(c, mx, my, mdx, mdy, step)

    # Bezel last, so an overlay frame lands exactly on the cabinet's own glass.
    c.frame(x0, y0, x1, y1, (86, 92, 118, 220), 2.5, 8)


def draw_drill_title(c, frame, total):
    """Attract mode. The cast walks back and forth well inside the glass."""
    import math
    x0, y0, x1, y1 = SCREEN
    c.rect(x0, y0, x1, y1, SCREEN_BG, 8)                    # opaque: hides the
                                                            # maze on the cabinet
    c.rect(x0, 36, x1, 58, (30, 20, 12, 255))
    screen_title(c, "ORE RUSH", 40, 2, (236, 198, 64, 255))

    # A pendulum march: the cast crosses the glass, turns, and comes back, so
    # nobody ever has to be clipped at an edge.
    # A pack of three, sized and swung so that at no point in the cycle does
    # any of them need clipping: the glass is only a hundred pixels wide.
    p = float(frame) / total
    facing = 1 if math.cos(2 * math.pi * p) >= 0 else -1
    front = 84 + 13 * math.sin(2 * math.pi * p)

    draw_miner(c, front, 82, facing, 0, frame)
    for k, col in enumerate(((176, 72, 64, 255), (150, 108, 186, 255))):
        gx = front - facing * (14 + k * 14)
        if on_screen(gx, 82, 12):
            draw_bug(c, gx, 82, col, facing, 0, frame + k)

    for k in range(5):                                      # ore still in the seam
        ox = x0 + 8 + k * 9
        if ox < front - 12 and on_screen(ox, 82, 5):
            c.rect(ox - 2, 80, ox + 2, 84, (226, 188, 108, 255), 1)

    if (frame // 2) % 2 == 0:
        screen_title(c, "INSERT COIN", 106, 1, (226, 232, 248, 255))

    c.frame(x0, y0, x1, y1, (86, 92, 118, 220), 2.5, 8)


# ---------------------------------------------------------------------------
# Game two: THRUMBO! Something enormous is at the top of the scaffold throwing
# rocks down it, and there is a colonist up there who would like to come down.
# ---------------------------------------------------------------------------

GIRDERS = [(40, 112, 118, 106), (42, 92, 120, 98), (40, 72, 118, 66),
           (42, 52, 120, 58)]
LADDERS = [(108, 98, 112), (52, 78, 92), (100, 58, 72)]


def girder_y(index, x):
    """Height of a girder at x, since they all slope."""
    gx0, gy0, gx1, gy1 = GIRDERS[index]
    t = max(0.0, min(1.0, (x - gx0) / float(gx1 - gx0)))
    return gy0 + (gy1 - gy0) * t


def draw_thrumbo(c, x, y, step):
    """Big, horned, and extremely cross. Seen from the side, as the game is."""
    c.ellipse(x, y, 13, 8, (228, 224, 216, 255))            # body
    c.ellipse(x - 10, y - 4, 6, 5, (236, 232, 226, 255))    # head
    lift = 2 if step % 4 < 2 else 0
    c.line(x - 13, y - 7 - lift, x - 20, y - 13 - lift, (240, 236, 228, 255), 2.6)  # horn
    c.circle(x - 12, y - 5, 1.4, (40, 36, 34, 255))         # eye
    for k in (-6, 0, 6):                                     # legs
        c.line(x + k, y + 6, x + k, y + 11, (210, 206, 198, 255), 2.4)
    c.line(x + 13, y - 2, x + 20, y - 6, (236, 232, 226, 255), 2.2)   # tail


def draw_climb_colonist(c, x, y, step, climbing=False):
    c.circle(x, y - 5, 3.6, (226, 190, 156, 255))           # head
    c.rect(x - 3, y - 2, x + 3, y + 5, (196, 84, 72, 255), 1)   # torso
    swing = 2 if step % 2 else -2
    if climbing:
        c.line(x - 3, y - 1, x - 6, y - 4 - swing, (226, 190, 156, 255), 1.8)
        c.line(x + 3, y - 1, x + 6, y - 4 + swing, (226, 190, 156, 255), 1.8)
        c.line(x - 2, y + 5, x - 3, y + 9, (60, 72, 110, 255), 1.8)
        c.line(x + 2, y + 5, x + 3, y + 9, (60, 72, 110, 255), 1.8)
    else:
        c.line(x - 2, y + 5, x - 4 - swing, y + 9, (60, 72, 110, 255), 1.8)
        c.line(x + 2, y + 5, x + 4 + swing, y + 9, (60, 72, 110, 255), 1.8)


def draw_climb_screen(c, frame=None, total=16):
    """Scaffolding, rolling rock, a thrumbo at the top and someone to reach."""
    import math
    x0, y0, x1, y1 = SCREEN
    c.rect(x0, y0, x1, y1, SCREEN_BG, 8)

    for gx0, gy0, gx1, gy1 in GIRDERS:                      # steel girders
        c.line(gx0, gy0, gx1, gy1, (156, 96, 64, 255), 4)
        c.line(gx0, gy0 - 2, gx1, gy1 - 2, (206, 132, 88, 255), 1.4)
    for lx, ly0, ly1 in LADDERS:                            # ladders between
        c.line(lx - 3, ly0, lx - 3, ly1, (120, 206, 226, 255), 1.8)
        c.line(lx + 3, ly0, lx + 3, ly1, (120, 206, 226, 255), 1.8)
        rung = ly0
        while rung < ly1:
            c.line(lx - 3, rung, lx + 3, rung, (120, 206, 226, 255), 1.4)
            rung += 5

    p = 0.0 if frame is None else float(frame) / total
    step = frame if frame is not None else 0

    draw_thrumbo(c, 62, girder_y(3, 62) - 10, step)         # top girder
    draw_climb_colonist(c, 108, girder_y(3, 108) - 8, step) # the one to reach
    if frame is None or step % 4 < 2:                       # ...calling for help
        c.circle(112, girder_y(3, 108) - 18, 2.2, (255, 244, 188, 220))

    # Rocks rolling down the slopes, each on its own girder and phase.
    for k in range(3):
        lane = 2 - k
        t = (p + k / 3.0) % 1.0
        gx0, _, gx1, _ = GIRDERS[lane]
        rx = gx1 - t * (gx1 - gx0) if lane % 2 else gx0 + t * (gx1 - gx0)
        ry = girder_y(lane, rx) - 5
        if on_screen(rx, ry, 5):
            c.circle(rx, ry, 4.4, (120, 112, 104, 255))
            c.circle(rx - 1.4, ry - 1.4, 1.8, (168, 160, 150, 255))
            spin = math.radians(t * 720 + k * 40)
            c.line(rx, ry, rx + math.cos(spin) * 3, ry + math.sin(spin) * 3,
                   (80, 74, 70, 255), 1.2)

    # The player, hopping along the bottom girder.
    px = 50 + 48 * (0.5 - 0.5 * math.cos(2 * math.pi * p))
    hop = abs(math.sin(2 * math.pi * p * 4)) * 5
    draw_climb_colonist(c, px, girder_y(0, px) - 8 - hop, step)

    c.frame(x0, y0, x1, y1, (86, 92, 118, 220), 2.5, 8)


def draw_climb_title(c, frame, total):
    import math

    x0, y0, x1, y1 = SCREEN
    c.rect(x0, y0, x1, y1, SCREEN_BG, 8)
    c.rect(x0, 36, x1, 58, (26, 24, 34, 255))
    screen_title(c, "THRUMBO!", 40, 2, (236, 232, 226, 255))

    c.line(44, 92, 116, 92, (156, 96, 64, 255), 4)          # one girder to stand on
    c.line(44, 90, 116, 90, (206, 132, 88, 255), 1.4)

    p = float(frame) / total
    draw_thrumbo(c, 58, 80, frame)
    px = 92 + 14 * math.sin(2 * math.pi * p)
    draw_climb_colonist(c, px, 84, frame)
    rx = 76 + 8 * math.cos(2 * math.pi * p)
    if on_screen(rx, 86, 5):
        c.circle(rx, 86, 4.4, (120, 112, 104, 255))
        c.circle(rx - 1.4, 84.6, 1.8, (168, 160, 150, 255))

    if (frame // 2) % 2 == 0:
        screen_title(c, "INSERT COIN", 106, 1, (226, 232, 248, 255))

    c.frame(x0, y0, x1, y1, (86, 92, 118, 220), 2.5, 8)


# ---------------------------------------------------------------------------
# The cabinet both games live in.
# ---------------------------------------------------------------------------

# Seen the way vanilla draws a table: the top a little foreshortened, and the
# cabinet's south side - whichever side that is for the facing - showing below
# it with the legs. From the ends that is a player's end; turned east or west
# it is the cabinet's long side, with its side art and the control ledges
# sticking out at each end. The top is the flat drawing turned for the facing
# and squeezed into COCKTAIL_TOP_H, and the screen frames go through exactly
# the same squeeze, so they sit on the glass in every facing.
COCKTAIL_TURNS = {"south": 0, "west": 1, "north": 2, "east": 3}
COCKTAIL_TOP_H = 122
COCKTAIL_FACE = (12, 110, 148, 140)


def cocktail_top(c, px, facing):
    rp, rw, rh = rotate(px, 160, 160, COCKTAIL_TURNS[facing])
    blit_rect(c, rp, rw, rh, (0, 0, 160, 160), (0, 0, 160, COCKTAIL_TOP_H))


def cocktail_face(c, facing, trim):
    body = (52, 48, 58, 255)
    side = darker(body, 0.8)
    x0, y0, x1, y1 = COCKTAIL_FACE
    for lx in (x0 + 8, x1 - 8):                                 # legs
        c.rect(lx - 6, y1 - 4, lx + 6, 156, DARK, 3)
        c.rect(lx - 4, y1 - 2, lx + 4, 153, darker(body, 0.6), 2)
    c.rect(x0 - 3, y0 - 2, x1 + 3, y1 + 3, DARK, 6)
    c.rect(x0, y0, x1, y1, side, 5)
    c.rect(x0, y0, x1, y0 + 3, lighter(side, 0.2), 2)           # lip under the glass top
    c.rect(x0 + 4, y1 - 6, x1 - 4, y1 - 3, trim, 1)              # trim stripe
    cx = 80
    if facing in ("south", "north"):                            # a player's end: the coin door
        c.rect(cx - 10, y0 + 11, cx + 10, y1 - 9, darker(side, 0.6), 2)
        c.rect(cx - 7, y0 + 14, cx - 2, y0 + 20, (226, 182, 78, 255), 1)
        c.rect(cx + 2, y0 + 14, cx + 7, y0 + 20, (226, 182, 78, 255), 1)
    else:                                                       # the long side: side art
        c.rect(x0 + 6, y0 + 8, x1 - 6, y1 - 9, darker(side, 0.85), 3)
        c.poly([(x0 + 10, y1 - 10), (x0 + 40, y0 + 9), (x0 + 58, y0 + 9), (x0 + 28, y1 - 10)], trim)
        c.poly([(x1 - 10, y0 + 9), (x1 - 40, y1 - 10), (x1 - 58, y1 - 10), (x1 - 28, y0 + 9)], trim)
        c.rect(cx - 22, y0 + 10, cx + 22, y1 - 11, (20, 20, 26, 255), 3)     # marquee
        c.rect(cx - 19, y0 + 13, cx + 19, y1 - 14, lighter(trim, 0.35), 2)
        for sx in (x0 - 3, x1 - 4):                             # control ledges, side-on
            c.rect(sx - 4, y0 - 4, sx + 7, y0 + 6, DARK, 2)
            c.rect(sx - 2, y0 - 2, sx + 5, y0 + 4, (68, 64, 78, 255), 1)


def cocktail_cabinet(name, screen_drawer, trim):
    """The flat drawing - the top, looked straight down on - then each facing
    built from it. Returns the flat drawing, which the previews use."""
    c = Canvas(160, 160)
    cx = cy = 80

    c.rect(10, 10, 150, 150, DARK, 20)
    c.rect(14, 14, 146, 146, (52, 48, 58, 255), 18)        # vinyl-edged table
    c.rect(20, 20, 140, 140, (34, 32, 40, 255), 14)
    c.frame(20, 20, 140, 140, (150, 146, 168, 70), 2, 14)

    screen_drawer(c, None)                                 # attract mode, baked

    # Control clusters on the two seating sides (north and south).
    panel = (52, 48, 58, 255)
    for sy in (24, 136):
        c.rect(cx - 26, sy - 7, cx + 26, sy + 7, darker(panel, 0.5), 6)
        c.rect(cx - 23, sy - 5, cx + 23, sy + 5, (68, 64, 78, 255), 5)
        c.circle(cx - 12, sy, 4.6, (28, 26, 32, 255))      # joystick ball
        c.circle(cx - 12, sy, 3.2, trim)
        for i in range(2):
            c.circle(cx + 6 + i * 11, sy, 3.4, (236, 196, 76, 255))
    c.rect(cx + 44, cy - 10, cx + 52, cy + 10, (28, 26, 32, 255), 3)   # coin slot

    px = c.pixels()
    for facing in COCKTAIL_TURNS:
        view = Canvas(160, 160)
        cocktail_face(view, facing, trim)
        cocktail_top(view, px, facing)
        view.save(os.path.join(OUT, "%s_%s.png" % (name, facing)))
    print("  %s_{north,east,south,west}.png  (160x160)" % name)
    return c


def cocktail_arcade():
    return cocktail_cabinet("CocktailArcade", draw_drill_screen, (214, 70, 62, 255))


def cocktail_climb():
    return cocktail_cabinet("CocktailClimb", draw_climb_screen, (96, 170, 226, 255))


def _screen_strip(name, drawer, total):
    """One strip per facing (CompAnimatedScreen perFacing), each frame put
    through the same turn and squeeze as the cabinet top it lies on."""
    for i in range(total):
        c = Canvas(160, 160)
        drawer(c, i, total)
        px = c.pixels()
        for facing in COCKTAIL_TURNS:
            view = Canvas(160, 160)
            cocktail_top(view, px, facing)
            view.save(os.path.join(OUT, "%s%s_%d.png" % (name, facing.capitalize(), i)))
    print("  %s{North,East,South,West}_0..%d.png  (160x160)" % (name, total - 1))


def cocktail_arcade_frames(total=16):
    _screen_strip("CocktailArcadeScreen", draw_drill_screen, total)


def cocktail_arcade_title_frames(total=8):
    _screen_strip("CocktailArcadeTitle", draw_drill_title, total)


def cocktail_climb_frames(total=16):
    _screen_strip("CocktailClimbScreen", draw_climb_screen, total)


def cocktail_climb_title_frames(total=8):
    _screen_strip("CocktailClimbTitle", draw_climb_title, total)


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
    carries it. The massage side is the roller seams and the control pad.

    Drawn the way RimWorld draws furniture: one bold dark line around the whole
    silhouette and nothing like it inside. That is what the two passes below
    are for - every piece of the chair is laid down oversized in the outline
    colour first, then every piece is laid down again at true size in its fill,
    which buries the outline everywhere two pieces touch and leaves it showing
    only around the outside. Interior divisions are a darker tint of the
    upholstery at a fraction of the weight, never the outline colour.
    """
    c = Canvas(128, 128)
    pale = (212, 206, 202, 255)        # takes the stuff colour
    pale_lt = (230, 225, 221, 255)
    pale_dk = (178, 172, 168, 255)
    seam = (168, 162, 158, 200)        # interior lines: a tint, not the outline
    seam_soft = (186, 180, 176, 190)

    # The chair, as rounded boxes: (x0, y0, x1, y1, corner radius).
    back = (12, 8, 116, 64, 22)
    arm_l = (6, 46, 34, 112, 13)
    arm_r = (94, 46, 122, 112, 13)
    seat = (22, 50, 106, 112, 18)
    foot = (34, 104, 94, 122, 10)
    pieces = (back, arm_l, arm_r, seat, foot)

    OUT = 5.0                                                  # silhouette weight
    for x0, y0, x1, y1, r in pieces:                           # pass 1: outline
        c.rect(x0 - OUT, y0 - OUT, x1 + OUT, y1 + OUT, DARK, r + OUT)
    for x0, y0, x1, y1, r in pieces:                           # pass 2: fill
        c.rect(x0, y0, x1, y1, pale_dk, r)

    # Pass 3: the soft interior. Tints only.
    c.rect(18, 14, 110, 58, pale, 18)                          # backrest face
    c.ellipse(64, 24, 34, 12, pale_lt)                         # headrest crown
    for y in range(32, 56, 7):                                 # roller seams
        c.line(30, y, 98, y, seam, 1.6)

    c.rect(28, 56, 100, 106, pale, 15)                         # seat cushion
    c.ellipse(64, 82, 32, 18, pale_lt)
    c.line(32, 94, 96, 94, seam, 1.6)
    c.line(64, 60, 64, 92, seam_soft, 1.4)                     # cushion split

    for ax in (6, 94):                                         # arm pads
        c.rect(ax + 4, 52, ax + 24, 106, pale, 10)
        c.ellipse(ax + 14, 66, 8, 12, pale_lt)
        c.line(ax + 6, 88, ax + 22, 88, seam_soft, 1.4)

    c.rect(38, 106, 90, 119, pale, 8)                          # footrest face
    c.ellipse(64, 112, 20, 4, pale_lt)

    # Control pad: the one thing meant to read as hardware rather than
    # upholstery, so it keeps a dark body - inset well inside the arm so it
    # never breaks the silhouette.
    c.rect(99, 76, 117, 98, (62, 60, 64, 255), 5)
    for i in range(3):
        c.circle(108, 82 + i * 7, 2.6, (238, 232, 216, 255))
    save_rotations(c, "MassageChair")
    return c


def massage_chair_frames(total=8):
    """Roller sweep up the backrest, vibration arcs, pulsing control light.
    Kept to the backrest and the arms: a pawn using the chair is drawn on top
    of the seat, so anything painted there is never seen."""
    import math
    for i in range(total):
        c = Canvas(128, 128)
        phase = float(i) / total

        # Rollers travelling up the backrest, wrapping at the top.
        for roller in (0.0, 0.5):
            t = (phase + roller) % 1.0
            y = 54 - t * 34
            glow = int(150 * math.sin(math.pi * t) + 40)
            c.rect(30, y - 3, 98, y + 3, (255, 214, 150, max(0, min(220, glow))), 3)

        # Vibration arcs off the armrests, where a seated pawn will not hide them.
        for side, sx in ((-1, 18), (1, 110)):
            for ring in range(3):
                t = (phase + ring / 3.0) % 1.0
                r = 5 + t * 13
                alpha = int(150 * (1.0 - t))
                if alpha > 6:
                    c.wedge(sx, 80, r, r - 2.2, 90 + side * 30, 90 + side * 150,
                            (255, 226, 176, alpha))

        # Control pad light, pulsing in time with the rollers.
        lamp = int(120 + 120 * math.sin(2 * math.pi * phase))
        c.circle(108, 94, 3.2, (255, 190, 120, max(0, min(255, lamp))))
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


# One tile of panel is 128 wide; the depth stays three quarters of a tile
# whatever the width, because that is what makes it sit on the wall's face.
VISTA_TILE = 128
VISTA_H = 96


def vista_bezel(c, w):
    c.rect(2, 3, w - 2, 93, DARK, 8)
    c.rect(5, 6, w - 5, 90, (78, 82, 94, 255), 7)
    c.frame(5, 6, w - 5, 90, (146, 152, 170, 90), 2, 7)
    c.rect(12, 12, w - 12, 84, (10, 12, 20, 255), 4)        # glass


def draw_vista_scene(c, name, frame, total):
    """The view, drawn to fit whatever width the canvas is.

    Everything across the picture is placed as a fraction of the glass rather
    than at a fixed pixel, so the one-tile panel shows the same landscape as
    the three-tile one rather than a squashed copy of it."""
    import math
    sky = VISTA_SKY[name]
    w = c.w
    x0, y0, x1, y1 = 12, 12, w - 12, 84
    span = float(x1 - x0)
    p = float(frame) / total

    def at(fraction):
        return x0 + span * fraction

    vista_bezel(c, w)

    # Sky, blended top to horizon in bands.
    bands = 18
    for b in range(bands):
        t = b / float(bands - 1)
        col = tuple(int(sky["top"][k] + (sky["bottom"][k] - sky["top"][k]) * t) for k in range(3))
        c.rect(x0, y0 + t * 50, x1, y0 + (b + 1) * 50.0 / bands + 1, col + (255,), 0)

    if sky["stars"]:
        count = max(8, int(sky["stars"] * span / 360.0))
        for k in range(count):
            sx = x0 + 6 + (k * 61) % max(1, int(span - 12))
            sy = y0 + 3 + (k * 37) % 40
            twinkle = 120 + int(120 * math.sin(2 * math.pi * (p * 2 + k * 0.17)))
            c.circle(sx, sy, 1.5, (240, 244, 255, max(40, min(255, twinkle))))

    # Sun or moon, drifting a little across the loop so the view is never still.
    bx = at(sky["body_x"] + 0.03 * math.sin(2 * math.pi * p))
    by = y0 + 58 * sky["body_y"]
    c.circle(bx, by, 17, sky["glow"] + (45,))
    c.circle(bx, by, 10, sky["body"] + (255,))
    if name == "Night":
        c.circle(bx + 4, by - 3, 8.5, (34, 44, 86, 255))    # crescent bite

    # Clouds drifting left to right, wrapping off the edges.
    cloud_col = (250, 250, 255, 150) if name == "Day" else (255, 214, 190, 120)
    if name == "Night":
        cloud_col = (120, 132, 180, 90)
    clouds = max(1, int(round(3 * span / 360.0)))
    for k in range(clouds):
        cx = x0 - 40 + ((p + k / float(clouds)) % 1.0) * (span + 80)
        cy = y0 + 13 + (k % 3) * 9
        for dx, dy, r in ((-13, 2, 6), (-3, -2, 8), (8, 2, 6), (16, 2, 5)):
            c.ellipse(cx + dx, cy + dy, r, r * 0.62, cloud_col)

    # Birds, a long way off.
    for k in range(sky["birds"]):
        fx = at(0.06 + ((p * 0.8 + k * 0.3) % 1.0) * 0.88)
        fy = y0 + 22 + 4 * math.sin(2 * math.pi * (p * 2 + k))
        c.line(fx - 5, fy, fx, fy - 2.5, (40, 40, 56, 190), 1.8)
        c.line(fx, fy - 2.5, fx + 5, fy, (40, 40, 56, 190), 1.8)

    # Land: a far ridge and a near one, so there is some depth to look at.
    far = tuple(min(255, v + 26) for v in sky["hills"])
    ridge_far = ((0.0, 66), (0.16, 52), (0.33, 63), (0.55, 49), (0.74, 61),
                 (0.91, 54), (1.0, 63))
    ridge_near = ((0.0, 72), (0.13, 63), (0.30, 73), (0.52, 61), (0.72, 72),
                  (0.88, 66), (1.0, 74))
    c.poly([(at(f), y) for f, y in ridge_far] + [(x1, y1), (x0, y1)], far + (255,))
    c.poly([(at(f), y) for f, y in ridge_near] + [(x1, y1), (x0, y1)],
           sky["hills"] + (255,))
    c.rect(x0, 77, x1, y1, tuple(max(0, v - 8) for v in sky["hills"]) + (255,), 0)

    # Scanlines and a faint sheen, to keep it reading as a screen.
    for y in range(y0, y1, 4):
        c.rect(x0, y, x1, y + 1, (8, 10, 18, 40), 0)
    c.rect(x0, y0, x1, y0 + 10, (255, 255, 255, 18), 0)
    c.frame(x0, y0, x1, y1, (150, 160, 190, 90), 1.5, 4)


# The three widths offered in the architect dropdown.
VISTA_WIDTHS = ((1, "VistaPanel1"), (2, "VistaPanel2"), (3, "VistaPanel3"))


# Wall pieces - the vista panels and the framed jigsaws - drawn for the wall
# face they hang on. South is the picture face-on. On a north face the wall
# itself is between the picture and the camera, so only the top of it shows,
# over the wall's top edge (drawOffsetNorth puts that edge WALL_PEEK px down
# the canvas). On an east or west face it would be seen edge-on, so it is
# tipped out a little at the bottom, the way a hung picture leans: its top
# against the wall, its foot toward the room - a narrowed strip lying along
# the wall tile's face, still showing the picture. West is east turned half
# round rather than mirrored, so nothing on it reads backwards.
WALL_PEEK = 34
WALL_EDGE_EAST = 79               # the wall's east face, at drawOffsetEast 0.26



# ---------------------------------------------------------------------------
# Tables: the top as it has always been drawn, and under its south edge the
# front of the table and its legs, the way vanilla draws a table. Everything
# that animates on a table top - puzzle pieces, boards, a ball, a puck, orrery
# gears - is drawn at the building's centre at its own size, so the canvas is
# padded by the same amount above as the legs take below, keeping the top
# exactly where it was.
# ---------------------------------------------------------------------------
def table_legs(c, x0, x1, y_edge, drop, apron, leg, legs, apron_h=16):
    """The south edge and the legs under it. Drawn before the top is laid
    over, so only what hangs below the top's edge shows."""
    for lx in legs:
        c.rect(lx - 6, y_edge, lx + 6, y_edge + drop, DARK, 3)
        c.rect(lx - 4, y_edge, lx + 4, y_edge + drop - 2, leg, 2)
    c.ellipse((x0 + x1) / 2.0, y_edge + drop - 2, (x1 - x0) / 2.0, 5, (0, 0, 0, 45))
    c.rect(x0 - 3, y_edge - 12, x1 + 3, y_edge + apron_h + 3, DARK, 5)
    c.rect(x0, y_edge - 10, x1, y_edge + apron_h, apron, 4)
    c.line(x0 + 3, y_edge + apron_h - 3, x1 - 3, y_edge + apron_h - 3, darker(apron, 0.7), 1.4)


def lay_over(c, px, w, h, x, y):
    """Composite a finished drawing onto a canvas at 1:1."""
    blit_rect(c, px, w, h, (0, 0, w, h), (x, y, x + w, y + h))


def save_table_views(top, name, drop, apron, leg, legs_ns, legs_ew, extra=None):
    """A rotatable table's four views from its top, drawn facing south.

    Each canvas is the turned top padded by drop on every side: the legs take
    the padding below, and the rest keeps the top centred. The def's drawSize
    is the top's size plus 2 * drop, in tiles."""
    px, w, h = top.pixels(), top.w, top.h
    for facing, turns in (("south", 0), ("west", 1), ("north", 2), ("east", 3)):
        rp, rw, rh = rotate(px, w, h, turns)
        c = Canvas(rw + 2 * drop, rh + 2 * drop)
        legs = legs_ns if facing in ("north", "south") else legs_ew
        table_legs(c, drop + 6, drop + rw - 6, drop + rh - 8, drop + 6, apron, leg,
                   [drop + rw * f for f in legs])
        lay_over(c, rp, rw, rh, drop, drop)
        if extra is not None:
            extra(c, facing, drop, rw, rh)
        c.save(os.path.join(OUT, "%s_%s.png" % (name, facing)))
    print("  %s_{north,east,south,west}.png  (tables, padded %d)" % (name, drop))


def save_wall_piece(face, name, strip):
    """Write the four facings of a wall piece from its face-on drawing."""
    px, w, h = face.pixels(), face.w, face.h
    face.save(os.path.join(OUT, "%s_south.png" % name))
    north = Canvas(w, 96)
    blit_rect(north, px, w, h, (0, 0, w, h * 0.55), (0, 0, w, WALL_PEEK))
    north.save(os.path.join(OUT, "%s_north.png" % name))
    east = Canvas(96, w)
    blit_quad(east, px, w, h, (0, 0, w, h), (WALL_EDGE_EAST + 3, w), (0, -w), (-strip, 0))
    east.save(os.path.join(OUT, "%s_east.png" % name))
    wp, ww, wh = rotate(east.pixels(), 96, w, 2)
    write_png(os.path.join(OUT, "%s_west.png" % name), ww, wh, wp)
    print("  %s_{north,east,south,west}.png" % name)


def vista_panel():
    """Each panel's own texture: a daylight view with the lights down.

    This is what shows in the architect menu and when the power is out. It used
    to be a black slab, which told a player nothing about what they were
    building; a dimmed view of the picture reads as a window in the menu and as
    a dead screen in the room, which is what both want."""
    made = {}
    for tiles, name in VISTA_WIDTHS:
        c = Canvas(VISTA_TILE * tiles, VISTA_H)
        draw_vista_scene(c, "Day", 0, 6)
        c.rect(12, 12, c.w - 12, 84, (10, 12, 22, 150), 4)  # lights down
        for i in range(min(3, tiles + 1)):
            c.circle(28 + i * 12, 89, 2.2, (54, 58, 70, 255))
        save_wall_piece(c, name, 56)
        made[name] = c
    return made


def vista_panel_frames(total=6):
    made = {}
    for tiles, name in VISTA_WIDTHS:
        for phase in ("Dawn", "Day", "Dusk", "Night"):
            for i in range(total):
                c = Canvas(VISTA_TILE * tiles, VISTA_H)
                draw_vista_scene(c, phase, i, total)
                c.save(os.path.join(OUT, "%s%s_%d.png" % (name, phase, i)))
                if i == 0 and tiles == 3:
                    made[phase] = c
        print("  %s{Dawn,Day,Dusk,Night}_0..%d.png  (%dx%d)"
              % (name, total - 1, VISTA_TILE * tiles, VISTA_H))
    return made


# ---------------------------------------------------------------------------
# Pinball in play  (one overlay set per facing, shared by all four tables)
#
# Only the ball, its trail and the lamps that just got hit are drawn, all in
# neutral white and silver, so the same frames sit correctly on the red, green,
# steel and violet cabinets. Each facing gets its own set because each shows a
# different part of the machine: the score only faces south, and from the
# north the backbox hides the back of the playfield, ball and all.
# ---------------------------------------------------------------------------
PB_PLAY_FILES = {"south": "PinballPlay", "north": "PinballPlayNorth",
                 "east": "PinballPlayEast", "west": "PinballPlayWest"}


def pinball_play_frame(view, i, total):
    import math
    base, c = view.canvas()
    p, s = view.pt, view.scale
    bu, bv = PB_BALL_PATH[i % len(PB_BALL_PATH)]
    pu, pv = PB_BALL_PATH[(i - 1) % len(PB_BALL_PATH)]
    lamp = (255, 250, 220, 200)

    # Motion trail back toward the previous position.
    if not view.hidden(bu, bv) and not view.hidden(pu, pv):
        (px, py), (bx, by) = p(pu, pv), p(bu, bv)
        c.line(px, py, bx, by, (226, 232, 248, 70), 7 * s)
        c.line((px + bx) / 2, (py + by) / 2, bx, by, (238, 242, 255, 110), 8 * s)

    # Lamps flare when the ball is on top of them. Distance is measured on the
    # playfield itself, so every facing lights the same bumper.
    lift = 2.5 if view.side else 1.5
    for mu, mv, mr in PB_BUMPERS:
        if math.hypot((bu - mu) * 132, (bv - mv) * 112) < mr * 112 + 14 and not view.hidden(mu, mv):
            mx, my = p(mu, mv)
            rx, ry = view.radii(mr)
            c.ellipse(mx, my - lift, rx + 9 * s, ry + 9 * (ry / rx), (255, 252, 226, 60))
            c.ellipse(mx, my - lift, rx + 3, ry + 3 * (ry / rx), (255, 250, 214, 150))
            c.ellipse(mx, my - lift, rx * 0.5, ry * 0.5, (255, 255, 244, 220))

    # Flippers snap up as the ball comes down to them.
    if bu > 0.7:
        for pivot_v, tip_v in PB_FLIPPERS:
            c.line(*p(PB_FLIP_U, pivot_v), *p(PB_FLIP_UP_U, tip_v), (255, 250, 220, 210), 9 * s)

    # The backglass keeps flashing while the table is live - on its face from
    # the south, as light spilling past it everywhere else.
    bright = i % 2 == 0
    if view.facing == "south":
        gx0, gy0, gx1, gy1 = PB_GLASS
        if bright:
            c.rect(gx0, gy0, gx1, gy1, (255, 248, 210, 26), 3)
        for k in range(6):
            if (i + k) % 3 == 0:
                c.circle(25 + k * 22, PB_LAMP_Y, 4.4, lamp)
        # The score climbing, which is the whole reason anyone plays.
        left = tuple((d * (i + 1) + i) % 10 for d in (1, 3, 7, 2, 9, 0))
        pb_reels(c, PB_SCORE_TOP, left, (0, 0, 3, 9, 6, 0), (255, 176, 72, 255))
    elif view.facing == "north":
        c.rect(24, PB_NORTH_BOX_TOP - 22, 136, PB_NORTH_BOX_TOP,
               (255, 248, 210, 34 if bright else 16), 4)
    else:
        bx0, bx1 = PB_SIDE_BOX
        gy0, gy1 = PB_SIDE_GLASS
        c.rect(bx1 - 4, gy0, bx1 - 1, gy1, (255, 248, 214, 200 if bright else 120), 1)
        top, depth = _side_top, PB_SIDE_DEPTH           # light falling on the glass
        c.poly([(bx1, top(bx1) + 1), (bx1 + 24, top(bx1 + 24) + 1),
                (bx1 + 24, top(bx1 + 24) + depth - 1), (bx1, top(bx1) + depth - 1)],
               (255, 248, 210, 44 if bright else 22))

    if not view.hidden(bu, bv):
        pb_ball(c, *p(bu, bv), view)
    return base


def pinball_play_frames(total=8):
    for facing, stem in PB_PLAY_FILES.items():
        view = PinballView(facing)
        for i in range(total):
            view.save(pinball_play_frame(view, i, total), os.path.join(OUT, "%s_%d.png" % (stem, i)))
        print("  %s_0..%d.png  (%dx%d)" % (stem, total - 1, PB_SQ, PB_SQ))


# ---------------------------------------------------------------------------
# 9. Soaking tub  (medieval, 1x1, wood-fired, pawns get in)
# ---------------------------------------------------------------------------

# Drawn standing, the way RimWorld shows anything with height: the rim seen at
# the camera's slant as an ellipse with the water inside it, the staves and
# hoops of the barrel's near side below, feet on the floor. The wood-fired
# tub's stove and chimney stand on the side it faces; from the north only the
# chimney shows, over the rim. The electric tub has its control box there.
#
# A bather is drawn by the game at the tile's centre, which puts their head
# and shoulders above the rim. The overlay drawn over them (SoakingTubWater,
# drawOverPawns) is everything nearer the camera than they are - the water in
# front of them, the rim's near edge, the barrel's near wall, and a stove
# facing south - so they sit down inside the tub rather than on top of it.
TUB_CX, TUB_RIM_Y, TUB_RX, TUB_RY = 64, 48, 44, 19
TUB_BOT_Y = 104                   # centre of the bottom ellipse
TUB_WATER_RX, TUB_WATER_RY = 38, 15
TUB_WOOD = (112, 78, 48, 255)
TUB_WATER = (46, 104, 112, 255)
TUB_FACINGS = ("north", "east", "south", "west")


def _arc(cx, cy, rx, ry, a0, a1, n=40):
    """Points along an ellipse from angle a0 to a1, in degrees."""
    import math
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / float(n))),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / float(n)))) for k in range(n + 1)]


def _tub_near_wall(c, band):
    """The barrel's near side: from the rim's front edge down to the floor."""
    import math
    c.poly(_arc(TUB_CX, TUB_RIM_Y, TUB_RX, TUB_RY, 0, 180)
           + _arc(TUB_CX, TUB_BOT_Y, TUB_RX, TUB_RY * 0.8, 180, 0), TUB_WOOD)
    for k in range(1, 8):                                       # staves
        a = math.radians(180 * k / 8.0)
        x = TUB_CX + TUB_RX * math.cos(a)
        c.line(x, TUB_RIM_Y + TUB_RY * math.sin(a) + 1,
               x, TUB_BOT_Y + TUB_RY * 0.8 * math.sin(a) - 1, darker(TUB_WOOD, 0.7), 1.4)
    for hy in (TUB_RIM_Y + 18, TUB_BOT_Y - 6):                  # hoops
        pts = _arc(TUB_CX, hy, TUB_RX, TUB_RY * 0.9, 0, 180)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line(x0, y0, x1, y1, band, 3.4)
    c.poly(_arc(TUB_CX, TUB_RIM_Y, TUB_RX, TUB_RY, 0, 180)       # the rim's near lip
           + _arc(TUB_CX, TUB_RIM_Y + 3, TUB_RX - 1, TUB_RY - 1, 180, 0), lighter(TUB_WOOD, 0.22))


def _tub_far_side(c):
    """Shadow, outline, the rim all the way round and the inside of the staves."""
    c.ellipse(TUB_CX, TUB_BOT_Y + 6, TUB_RX + 6, TUB_RY * 0.8 + 3, (0, 0, 0, 60))
    outline = (_arc(TUB_CX, TUB_RIM_Y, TUB_RX, TUB_RY, 180, 360)
               + _arc(TUB_CX, TUB_BOT_Y, TUB_RX, TUB_RY * 0.8, 0, 180))
    c.poly(_grow_poly(outline, 3.5), DARK)
    c.ellipse(TUB_CX, TUB_RIM_Y, TUB_RX, TUB_RY, lighter(TUB_WOOD, 0.22))
    c.ellipse(TUB_CX, TUB_RIM_Y + 1, TUB_RX - 5, TUB_RY - 4, darker(TUB_WOOD, 0.7))


def _tub_stove(c, x, y):
    c.rect(x - 16, y - 12, x + 16, y + 14, DARK, 5)
    c.rect(x - 13, y - 9, x + 13, y + 11, (58, 50, 46, 255), 4)
    c.rect(x - 8, y - 3, x + 8, y + 7, (30, 24, 22, 255), 2)
    c.circle(x, y + 3, 5, (226, 120, 52, 235))
    c.circle(x, y + 3, 2.6, (255, 196, 110, 255))


def _tub_chimney(c, x, y_top, y_bot):
    c.rect(x - 5, y_top, x + 5, y_bot, DARK, 2)
    c.rect(x - 3, y_top + 2, x + 3, y_bot, (70, 66, 64, 255), 1.5)
    c.rect(x - 7, y_top - 4, x + 7, y_top + 3, DARK, 2)          # cap
    c.rect(x - 5, y_top - 2, x + 5, y_top + 1, (92, 88, 86, 255), 1)


def _tub_controls(c, x, y):
    c.rect(x - 18, y - 10, x + 18, y + 10, DARK, 5)
    c.rect(x - 15, y - 7, x + 15, y + 7, (62, 66, 78, 255), 4)
    for k, col in enumerate(((120, 226, 140, 255), (236, 196, 78, 255), (130, 190, 240, 255))):
        c.circle(x - 9 + k * 9, y, 2.8, col)


def _tub_front_fittings(c, facing, electric):
    """Whatever stands in front of the barrel facing south - over the bather too."""
    if facing != "south":
        return
    if electric:
        _tub_controls(c, TUB_CX, TUB_BOT_Y + 2)
    else:
        _tub_stove(c, TUB_CX, TUB_BOT_Y + 4)
        _tub_chimney(c, TUB_CX + TUB_RX + 2, 10, TUB_BOT_Y)


def soaking_tub_view(facing, electric=False):
    c = Canvas(128, 128)
    band = (150, 162, 178, 255) if electric else (146, 150, 158, 255)
    m = MirrorCanvas(c) if facing == "west" else c
    if facing in ("east", "west"):                               # on the side it faces
        if electric:
            _tub_controls(m, TUB_CX + TUB_RX + 2, TUB_BOT_Y - 4)
        else:
            _tub_chimney(m, TUB_CX + TUB_RX + 8, 10, TUB_BOT_Y + 2)
            _tub_stove(m, TUB_CX + TUB_RX + 4, TUB_BOT_Y + 2)
    elif facing == "north" and not electric:
        _tub_chimney(c, TUB_CX + 10, 4, TUB_RIM_Y - 4)           # behind, over the rim
    _tub_far_side(c)
    c.ellipse(TUB_CX, TUB_RIM_Y + 2, TUB_WATER_RX, TUB_WATER_RY, TUB_WATER)
    c.ellipse(TUB_CX, TUB_RIM_Y + 2, TUB_WATER_RX, TUB_WATER_RY, (60, 130, 138, 115))
    _tub_near_wall(c, band)
    _tub_front_fittings(c, facing, electric)
    return c


def soaking_tub(name="SoakingTub", electric=False):
    for facing in TUB_FACINGS:
        soaking_tub_view(facing, electric).save(os.path.join(OUT, "%s_%s.png" % (name, facing)))
    print("  %s_{north,east,south,west}.png  (128x128)" % name)
    return soaking_tub_view("south", electric)


def soaking_tub_water_frames(name="SoakingTubWater", electric=False, total=6):
    """Drawn over the bather: the water in front of them, with ripples running
    out from where they sit, then the rim's near edge and the barrel's near
    wall - everything the camera sees in front of someone sitting in a tub.

    1.6 does have a real swimming pose, but it is keyed to Pawn.Swimming, which
    is read-only and comes from the terrain underfoot - a building cannot ask
    for it - so the tub has to do the work on both 1.5 and 1.6.
    """
    band = (150, 162, 178, 255) if electric else (146, 150, 158, 255)
    hole_rx, hole_ry = 17, 7          # where the bather comes up through the water
    cy = TUB_RIM_Y + 2
    for i in range(total):
        p = float(i) / total
        for facing in TUB_FACINGS:
            c = Canvas(128, 128)
            c.poly(_arc(TUB_CX, cy, TUB_WATER_RX, TUB_WATER_RY, 0, 180)
                   + _arc(TUB_CX, cy, hole_rx, hole_ry, 180, 0), TUB_WATER)
            c.poly(_arc(TUB_CX, cy, hole_rx + 2, hole_ry + 1.2, 0, 180)       # meniscus
                   + _arc(TUB_CX, cy, hole_rx, hole_ry, 180, 0), (110, 186, 192, 200))
            for k in range(3):
                t = (p + k / 3.0) % 1.0
                rx = hole_rx + 3 + t * (TUB_WATER_RX - hole_rx - 5)
                ry = hole_ry + 1.5 + t * (TUB_WATER_RY - hole_ry - 2.5)
                pts = _arc(TUB_CX, cy, rx, ry, 10, 170, 24)
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    c.line(x0, y0, x1, y1, (168, 222, 228, int(150 * (1 - t))), 1.4)
            _tub_near_wall(c, band)
            _tub_front_fittings(c, facing, electric)
            c.save(os.path.join(OUT, "%s%s_%d.png" % (name, facing.capitalize(), i)))
    print("  %s{North,East,South,West}_0..%d.png  (128x128)" % (name, total - 1))


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

# The aquarium, drawn standing: a glass tank on a cabinet stand, 2x2 tiles of
# canvas. Facing north or south the footprint is the bottom half and the tank
# rises over the tile behind (drawOffsetNorth/South 0.5); you look through the
# long glass at gravel, planting and bubbles, and CompSwimmingFish swims the
# fish across it in profile. Facing east or west the tank runs away from the
# camera, 2 tiles long, so most of what shows is its top - looked down into
# through the glass lid, the same water and planting the flat view always had,
# with the fish swimming from above - and the near end's glass and the stand
# below it, with a sliver of the long glass on the side it faces.
AQ_GLASS = (18, 46, 238, 162)          # facing north/south: the long glass
AQ_SIDE_X = (70, 186)                  # facing east: the tank's width
AQ_SIDE_TOP = (8, 150)                 # its top, running away up the picture
AQ_SIDE_END = 206                      # the near end's glass, top..here
AQ_FLOOR = 252
AQ_WOOD = (70, 52, 40, 255)
AQ_FRAME = (40, 44, 50, 255)


def _aq_water(c, x0, y0, x1, y1, dim=1.0, fronds=True, seed=1):
    """Water seen through glass from the side: paler toward the surface, a
    gravel bed, planting standing up out of it."""
    import random
    for k in range(10):
        t = k / 9.0
        col = tuple(int(v * (0.85 + 0.25 * (1 - t)) * dim) for v in (58, 132, 150)) + (255,)
        c.rect(x0, y0 + (y1 - y0) * k / 10.0, x1, y0 + (y1 - y0) * (k + 1) / 10.0 + 1, col, 0)
    c.rect(x0, y1 - 12, x1, y1, tuple(int(v * dim) for v in (176, 150, 110)) + (255,), 0)
    for i in range(int((x1 - x0) / 9)):
        c.circle(x0 + 4 + i * 9 + (i * 7) % 5, y1 - 8 + (i * 3) % 5, 2,
                 tuple(int(v * dim) for v in (140, 116, 84)) + (255,))
    if not fronds:
        return
    r = random.Random(seed)
    for px in (x0 + (x1 - x0) * f for f in (0.12, 0.3, 0.72, 0.9)):
        for k in range(4):
            h = r.uniform(0.35, 0.8) * (y1 - y0)
            c.line(px + k * 3, y1 - 10, px + k * 3 + r.uniform(-6, 6), y1 - 10 - h,
                   tuple(int(v * dim) for v in (70, 150, 80)) + (255,), 2.2)


def _aq_top_pixels(frame=None, total=8, facing="east"):
    """The tank from above - the drawing the flat view used - turned to run
    up the picture, and the part of it that is water."""
    tmp = Canvas(256, 128)
    draw_tank_contents(tmp, frame, total)
    tx0, ty0, tx1, ty1 = TANK
    rp, rw, rh = rotate(tmp.pixels(), 256, 128, 3 if facing == "east" else 1)
    src = (128 - ty1, tx0, 128 - ty0, tx1) if facing == "east" else (ty0, 256 - tx1, ty1, 256 - tx0)
    return rp, rw, rh, src


def _aq_top_rect():
    x0, x1 = AQ_SIDE_X
    return (x0 + 3, AQ_SIDE_TOP[0] + 12, x1 - 3, AQ_SIDE_TOP[1] - 1)


def _fish_in_profile(c, x, y, length, col, left=False):
    """A fish side-on, nose east (or west): body, tail, fins, an eye."""
    d = -1 if left else 1
    h = length * 0.36
    c.ellipse(x, y, length * 0.45, h * 0.62, col)
    c.poly([(x - d * length * 0.38, y), (x - d * length * 0.62, y - h * 0.7),
            (x - d * length * 0.56, y), (x - d * length * 0.62, y + h * 0.7)], darker(col, 0.8))
    c.poly([(x - d * length * 0.12, y - h * 0.5), (x + d * length * 0.08, y - h * 0.5),
            (x - d * length * 0.2, y - h * 1.0)], darker(col, 0.8))             # dorsal fin
    c.ellipse(x + d * length * 0.02, y + h * 0.18, length * 0.24, h * 0.24, lighter(col, 0.25))
    c.circle(x + d * length * 0.28, y - h * 0.1, max(1.6, length * 0.05), (20, 20, 24, 255))


def aquarium_fish_profiles():
    """The same four fish in profile for the long-glass views: nose east, and
    "Left" nose west. CompSwimmingFish picks by which way each is swimming."""
    kinds = [(54, (240, 156, 60)), (46, (226, 96, 96)), (38, (244, 214, 96)), (42, (118, 186, 232))]
    for k, (length, col) in enumerate(kinds):
        for left in (False, True):
            c = Canvas(64, 64)
            _fish_in_profile(c, 32, 32, length, col + (255,), left)
            c.save(os.path.join(OUT, "AquariumFishSide_%d%s.png" % (k, "Left" if left else "")))
    print("  AquariumFishSide_0..3{,Left}.png  (64x64)")


def aquarium_view(facing):
    c = Canvas(256, 256)
    if facing in ("south", "north"):
        c.ellipse(128, 252, 124, 5, (0, 0, 0, 55))
        silhouette(c, [("rect", 10, 30, 246, 250, 4, darker(AQ_WOOD, 0.9))], 4.0)
        c.rect(10, 170, 246, 250, AQ_WOOD, 4)                            # the stand
        for dx in (64, 128, 192):
            c.line(dx, 176, dx, 244, darker(AQ_WOOD, 0.6), 1.5)
        for kx in (60, 68, 188, 196):
            c.circle(kx, 210, 2.2, (190, 160, 90, 255))
        c.rect(10, 164, 246, 172, darker(AQ_WOOD, 0.7), 2)
        c.rect(14, 30, 242, 44, (54, 58, 66, 255), 3)                    # hood, its top catching light
        c.rect(14, 30, 242, 35, (96, 102, 112, 255), 2)
        x0, y0, x1, y1 = AQ_GLASS
        c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, (30, 40, 44, 255), 1)
        _aq_water(c, x0, y0, x1, y1, 1.0 if facing == "south" else 0.7)
        c.rect(x0, y0, x1, y0 + 10, (255, 255, 255, 26), 0)             # waterline sheen
        c.line(x0 + 2, y0 + 4, x1 - 2, y0 + 4, (200, 235, 245, 120), 1.2)
        c.frame(x0 - 2, y0 - 2, x1 + 2, y1 + 2, AQ_FRAME, 3, 1)
        if facing == "north":
            c.rect(190, 26, 230, 70, DARK, 3)                            # the filter, on the back
            c.rect(193, 29, 227, 67, (60, 64, 70, 255), 2)
        c.poly([(24, 52), (40, 52), (70, 158), (54, 158)], (255, 255, 255, 20))   # a glint
        return c

    x0, x1 = AQ_SIDE_X
    top0, top1 = AQ_SIDE_TOP
    c.ellipse(128, AQ_FLOOR, 66, 5, (0, 0, 0, 55))
    silhouette(c, [("rect", x0, top0, x1, AQ_FLOOR - 2, 4, darker(AQ_WOOD, 0.9))], 4.0)
    c.rect(x0, top0, x1, top1, (30, 40, 44, 255), 1)
    rp, rw, rh, src = _aq_top_pixels(None, 8, facing)
    blit_rect(c, rp, rw, rh, src, _aq_top_rect())
    c.rect(x0 + 2, top0 + 2, x1 - 2, top0 + 12, (54, 58, 66, 255), 2)   # the light, across the far end
    c.rect(x0 + 8, top0 + 9, x1 - 8, top0 + 12, (240, 246, 220, 255), 1)
    c.poly([(x0 + 8, top0 + 16), (x0 + 22, top0 + 16), (x0 + 40, top1 - 4), (x0 + 26, top1 - 4)],
           (255, 255, 255, 22))
    c.frame(x0, top0, x1, top1, AQ_FRAME, 3, 2)
    end = AQ_SIDE_END                                                    # the near end's glass
    c.rect(x0, top1, x1, end, (30, 40, 44, 255), 1)
    _aq_water(c, x0 + 2, top1 + 2, x1 - 2, end - 2, 0.85, seed=5)
    c.frame(x0, top1, x1, end, AQ_FRAME, 3, 1)
    c.line(x0 + 2, top1 + 1.5, x1 - 2, top1 + 1.5, (200, 235, 245, 150), 1.4)
    c.rect(x0, end, x1, AQ_FLOOR - 2, AQ_WOOD, 3)                        # the stand's end
    c.line(x0 + 4, end + 4, x1 - 4, end + 4, darker(AQ_WOOD, 0.6), 1.4)
    c.circle((x0 + x1) / 2.0, (end + AQ_FLOOR) / 2.0, 2.2, (190, 160, 90, 255))
    m = MirrorCanvas(c) if facing == "west" else c                       # the long glass, a sliver
    m.rect(x1, top0 + 4, x1 + 12, end, (30, 40, 44, 255), 1)
    for k in range(10):
        t = k / 9.0
        col = tuple(int(v * (0.85 + 0.25 * (1 - t))) for v in (58, 132, 150)) + (255,)
        m.rect(x1 + 1, top0 + 6 + (end - top0 - 8) * k / 10.0,
               x1 + 11, top0 + 6 + (end - top0 - 8) * (k + 1) / 10.0 + 1, col, 0)
    m.rect(x1 + 1, end - 12, x1 + 11, end - 1, (176, 150, 110, 255), 0)
    for yy in (top0 + 60, top0 + 120):
        m.line(x1 + 5, end - 10, x1 + 7, yy, (70, 150, 80, 255), 2)
    m.rect(x1, end, x1 + 12, AQ_FLOOR - 2, darker(AQ_WOOD, 0.8), 2)
    m.line(x1 + 12, top0 + 4, x1 + 12, AQ_FLOOR - 2, AQ_FRAME, 2.5)
    return c


def aquarium():
    for facing in ("north", "east", "south", "west"):
        aquarium_view(facing).save(os.path.join(OUT, "Aquarium_%s.png" % facing))
    print("  Aquarium_{north,east,south,west}.png  (256x256)")
    return aquarium_view("south")


def aquarium_frames(total=8):
    """Per facing (perFacing), at the same 2x2 canvas as the tank. Through the
    long glass: bubbles rising from the airstone and light rippling down from
    the surface. From above, on the east and west views: the old looking-down
    loop - swaying planting, drifting caustics - on the top the same way the
    tank's own texture lays it there."""
    import math
    for i in range(total):
        p = float(i) / total
        for facing in ("south", "north"):
            c = Canvas(256, 256)
            x0, y0, x1, y1 = AQ_GLASS
            bright = 1.0 if facing == "south" else 0.6
            for k in range(7):                                           # bubbles
                t = (p + k / 7.0) % 1.0
                bx = x0 + (x1 - x0) * 0.86 + 3 * math.sin(2 * math.pi * (t * 2 + k * 0.3))
                by = y1 - 14 - t * (y1 - y0 - 18)
                c.circle(bx, by, 1.6 + t, (220, 240, 250, int(170 * bright)))
            for k in range(4):                                           # light from the surface
                lx = x0 + ((p * 0.5 + k / 4.0) % 1.0) * (x1 - x0)
                c.poly([(lx - 6, y0 + 6), (lx + 6, y0 + 6), (lx + 20, y1 - 14), (lx + 4, y1 - 14)],
                       (200, 240, 250, int(16 * bright)))
            c.line(x0 + 2, y0 + 4 + math.sin(2 * math.pi * p) * 1.2, x1 - 2,
                   y0 + 4 - math.sin(2 * math.pi * p) * 1.2, (220, 245, 250, int(110 * bright)), 1.2)
            c.save(os.path.join(OUT, "AquariumLife%s_%d.png" % (facing.capitalize(), i)))
        for facing in ("east", "west"):
            c = Canvas(256, 256)
            rp, rw, rh, src = _aq_top_pixels(i, total, facing)
            blit_rect(c, rp, rw, rh, src, _aq_top_rect())
            x0, x1 = AQ_SIDE_X
            top0 = AQ_SIDE_TOP[0]
            c.rect(x0 + 2, top0 + 2, x1 - 2, top0 + 12, (54, 58, 66, 255), 2)   # keep the light on top
            c.rect(x0 + 8, top0 + 9, x1 - 8, top0 + 12, (240, 246, 220, 255), 1)
            c.save(os.path.join(OUT, "AquariumLife%s_%d.png" % (facing.capitalize(), i)))
    print("  AquariumLife{North,East,South,West}_0..%d.png  (256x256)" % (total - 1))


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

# Karaoke, drawn the way an arcade cabinet is: side-on it is the machine's
# profile - the lit marquee, the screen leaning back toward the singer, the
# deck jutting out with the mic lying on it, the speaker cabinet below - and
# the front and back share its heights exactly, so all four views are one
# standing machine.
KA_CASE = (56, 48, 74, 255)
KA_TRIM = (206, 92, 178, 255)          # side art and marquee colour
KA_GLASS = (14, 16, 26, 255)
# Shared heights (canvas y), top to bottom.
KA_TOP = 14            # marquee top
KA_MARQ = 28           # marquee bottom / screen top
KA_SCR_BOT = 60        # screen bottom / deck top
KA_DECK = 72           # deck front edge bottom
KA_BASE = 112          # cabinet bottom / plinth top
KA_FLOOR = 120
# Side profile (east view, front to the right), x positions.
KA_BACK = 26           # back of the cabinet
KA_TOP_FRONT = 76      # front of the marquee
KA_SCR_FOOT = 84       # screen's bottom edge, leaning out toward the singer
KA_DECK_FRONT = 106    # the deck juts out
KA_BODY_FRONT = 94     # speaker cabinet front
# Front view: x span.
KA_FX0, KA_FX1 = 22, 106


def _karaoke_side(c):
    """East view: the cabinet's profile - marquee, the screen leaning back,
    the deck jutting out with the mic on it, the speaker cabinet below."""
    c.ellipse((KA_BACK + KA_DECK_FRONT) / 2.0, KA_FLOOR - 1, (KA_DECK_FRONT - KA_BACK) / 2.0 + 2, 4, (0, 0, 0, 60))
    profile = [(KA_BACK, KA_TOP), (KA_TOP_FRONT, KA_TOP), (KA_TOP_FRONT, KA_MARQ), (KA_SCR_FOOT, KA_SCR_BOT),
               (KA_DECK_FRONT, KA_SCR_BOT), (KA_DECK_FRONT, KA_DECK), (KA_BODY_FRONT, KA_DECK + 4),
               (KA_BODY_FRONT, KA_BASE), (KA_BACK, KA_BASE)]
    silhouette(c, [("poly", profile, KA_CASE),
                   ("rect", KA_BACK + 2, KA_BASE - 2, KA_BODY_FRONT - 2, KA_FLOOR, 2, darker(KA_CASE, 0.6))], 4.0)
    c.poly([(KA_BACK + 4, KA_BASE - 1), (KA_BODY_FRONT - 4, KA_BASE - 1), (KA_BODY_FRONT - 4, KA_FLOOR - 2), (KA_BACK + 4, KA_FLOOR - 2)], darker(KA_CASE, 0.55))
    # the marquee's side, and the screen's edge catching its own light
    c.rect(KA_BACK, KA_TOP, KA_TOP_FRONT, KA_MARQ, lighter(KA_CASE, 0.12), 3)
    c.line(KA_TOP_FRONT - 1, KA_TOP + 2, KA_TOP_FRONT - 1, KA_MARQ - 1, lighter(KA_TRIM, 0.3), 2)
    c.line(KA_TOP_FRONT, KA_MARQ, KA_SCR_FOOT, KA_SCR_BOT, (120, 150, 210, 230), 2)
    # the deck's top, seen from above as it juts out, and the mic lying on it
    c.poly([(KA_SCR_FOOT - 2, KA_SCR_BOT), (KA_DECK_FRONT, KA_SCR_BOT), (KA_DECK_FRONT - 2, KA_SCR_BOT + 4), (KA_SCR_FOOT - 2, KA_SCR_BOT + 4)], lighter(KA_CASE, 0.25))
    c.rect(KA_DECK_FRONT - 6, KA_SCR_BOT, KA_DECK_FRONT, KA_DECK, darker(KA_CASE, 0.7), 1)
    c.line(KA_SCR_FOOT + 2, KA_SCR_BOT - 3, KA_DECK_FRONT - 8, KA_SCR_BOT - 3, (170, 172, 184, 255), 4)
    c.circle(KA_DECK_FRONT - 7, KA_SCR_BOT - 3, 3.6, (206, 208, 218, 255))
    # speaker cones on the front, edge-on
    c.rect(KA_BODY_FRONT - 3, KA_DECK + 10, KA_BODY_FRONT + 2, KA_BASE - 6, darker(KA_CASE, 0.5), 2)
    c.rect(KA_BODY_FRONT - 1, KA_DECK + 14, KA_BODY_FRONT + 2, KA_DECK + 24, (96, 92, 116, 255), 1)
    c.rect(KA_BODY_FRONT - 1, KA_BASE - 24, KA_BODY_FRONT + 2, KA_BASE - 12, (96, 92, 116, 255), 1)
    # side art: a stripe following the profile and a big note
    c.poly([(KA_BACK + 4, KA_BASE - 8), (KA_BACK + 4, KA_BASE - 16), (KA_BODY_FRONT - 4, KA_DECK + 6), (KA_BODY_FRONT - 4, KA_DECK + 14)], KA_TRIM)
    nx, ny = KA_BACK + 26, KA_MARQ + 44
    c.ellipse(nx, ny, 7, 5.5, lighter(KA_TRIM, 0.35))
    c.rect(nx + 5, ny - 26, nx + 8, ny, lighter(KA_TRIM, 0.35), 1)
    c.poly([(nx + 8, ny - 26), (nx + 18, ny - 20), (nx + 18, ny - 15), (nx + 8, ny - 20)], lighter(KA_TRIM, 0.35))
    c.line(KA_BACK + 2, KA_TOP + 3, KA_BACK + 2, KA_BASE - 3, (255, 255, 255, 30), 2)


def _karaoke_front(c, lit=True):
    """South: the marquee, the screen, the deck with the mic, two speakers."""
    c.ellipse((KA_FX0 + KA_FX1) / 2.0, KA_FLOOR - 1, (KA_FX1 - KA_FX0) / 2.0 + 2, 4, (0, 0, 0, 60))
    silhouette(c, [("rect", KA_FX0, KA_TOP, KA_FX1, KA_BASE, 5, KA_CASE),
                   ("rect", KA_FX0 - 3, KA_SCR_BOT, KA_FX1 + 3, KA_DECK, 3, lighter(KA_CASE, 0.2)),
                   ("rect", KA_FX0 + 2, KA_BASE - 2, KA_FX1 - 2, KA_FLOOR, 2, darker(KA_CASE, 0.6))], 4.0)
    c.rect(KA_FX0 + 4, KA_BASE - 1, KA_FX1 - 4, KA_FLOOR - 2, darker(KA_CASE, 0.55), 1)
    # marquee
    c.rect(KA_FX0, KA_TOP, KA_FX1, KA_MARQ, darker(KA_CASE, 0.7), 5)
    c.rect(KA_FX0 + 5, KA_TOP + 3, KA_FX1 - 5, KA_MARQ - 3, lighter(KA_TRIM, 0.1) if lit else darker(KA_TRIM, 0.6), 3)
    for k in range(7):
        c.circle(KA_FX0 + 12 + k * 10, (KA_TOP + KA_MARQ) / 2.0, 2.2, (255, 240, 220, 200))
    # screen, leaning back
    c.rect(KA_FX0 + 5, KA_MARQ + 1, KA_FX1 - 5, KA_SCR_BOT - 1, darker(KA_CASE, 0.5), 4)
    c.rect(KA_FX0 + 8, KA_MARQ + 4, KA_FX1 - 8, KA_SCR_BOT - 4, KA_GLASS, 3)
    for k in range(4):
        c.rect(KA_FX0 + 14, KA_MARQ + 9 + k * 5.5, KA_FX0 + 14 + (16 + (k * 13) % 40), KA_MARQ + 12 + k * 5.5, (86, 132, 196, 200), 1.5)
    # the deck: its top catching the light, the mic lying on it, two buttons
    c.rect(KA_FX0 - 3, KA_SCR_BOT, KA_FX1 + 3, KA_SCR_BOT + 5, lighter(KA_CASE, 0.32), 2)
    c.line(52, KA_SCR_BOT + 2.5, 80, KA_SCR_BOT + 2.5, (170, 172, 184, 255), 4)
    c.circle(82, KA_SCR_BOT + 2.5, 3.8, (206, 208, 218, 255))
    for bx, col in ((34, (226, 182, 78, 255)), (94, (110, 196, 150, 255))):
        c.circle(bx, KA_SCR_BOT + 7.5, 2.8, col)
    # speakers
    for sx in (KA_FX0 + 20, KA_FX1 - 20):
        c.circle(sx, 92, 15, darker(KA_CASE, 0.5))
        c.circle(sx, 92, 13, (34, 32, 44, 255))
        c.ring(sx, 92, 9, 7.5, (78, 74, 96, 255))
        c.circle(sx, 92, 4, (96, 92, 116, 255))
    c.line(KA_FX0 + 1.5, KA_MARQ, KA_FX0 + 1.5, KA_BASE - 4, (255, 255, 255, 36), 2)


def _karaoke_back(c):
    c.ellipse((KA_FX0 + KA_FX1) / 2.0, KA_FLOOR - 1, (KA_FX1 - KA_FX0) / 2.0 + 2, 4, (0, 0, 0, 60))
    silhouette(c, [("rect", KA_FX0, KA_TOP, KA_FX1, KA_BASE, 5, KA_CASE),
                   ("rect", KA_FX0 + 2, KA_BASE - 2, KA_FX1 - 2, KA_FLOOR, 2, darker(KA_CASE, 0.6))], 4.0)
    c.rect(KA_FX0 + 4, KA_BASE - 1, KA_FX1 - 4, KA_FLOOR - 2, darker(KA_CASE, 0.55), 1)
    panel = darker(KA_CASE, 0.82)
    c.rect(KA_FX0, KA_TOP, KA_FX1, KA_MARQ, darker(KA_CASE, 0.7), 5)                   # back of the marquee
    c.rect(KA_FX0 + 4, KA_MARQ + 3, KA_FX1 - 4, KA_BASE - 4, panel, 3)
    for k in range(5):                                                   # vents behind the screen
        c.rect(34, KA_MARQ + 8 + k * 5, 94, KA_MARQ + 10.5 + k * 5, darker(panel, 0.5), 1)
    for sx in (KA_FX0 + 20, KA_FX1 - 20):                                     # speaker magnets
        c.circle(sx, 92, 9, darker(panel, 0.7))
        c.circle(sx, 92, 5, darker(panel, 0.5))
    c.rect(54, 78, 74, 88, (150, 146, 128, 255), 1.5)                   # maker's plate
    c.rect(59, 98, 69, 105, darker(panel, 0.4), 2)                      # cable
    c.line(64, 104, 64, 118, (22, 22, 26, 255), 3)
    c.line(64, 118, 86, 121, (22, 22, 26, 255), 3)


def _karaoke_notes(c, i, total, x, spread=22):
    p = float(i) / total
    for k in range(3):
        t = (p + k / 3.0) % 1.0
        nx = x + (k - 1) * spread + 6 * math.sin(2 * math.pi * t)
        ny = KA_TOP + 8 - t * 22
        a = int(210 * (1 - t))
        c.circle(nx, ny + 6, 3.0, (250, 232, 150, a))
        c.rect(nx + 1.8, ny - 4, nx + 3.4, ny + 6, (250, 232, 150, a), 1)


def _karaoke_frame_south(i, total=6):
    c = Canvas(128, 128); p = float(i) / total
    c.rect(KA_FX0 + 8, KA_MARQ + 4, KA_FX1 - 8, KA_SCR_BOT - 4, KA_GLASS, 3)
    for k in range(4):
        lit = (i + k) % 4
        width = 14 + ((k * 13 + i * 7) % 40)
        col = (250, 226, 120, 235) if lit < 2 else (86, 132, 196, 210)
        c.rect(KA_FX0 + 14, KA_MARQ + 9 + k * 5.5, KA_FX0 + 14 + width, KA_MARQ + 12 + k * 5.5, col, 1.5)
    for k in range(7):                                                   # marquee chase
        if (k + i) % 3 == 0:
            c.circle(KA_FX0 + 12 + k * 10, (KA_TOP + KA_MARQ) / 2.0, 3.2, (255, 250, 230, 240))
    for j, sx in enumerate((KA_FX0 + 20, KA_FX1 - 20)):
        pulse = 1.0 + 0.22 * math.sin(2 * math.pi * (p * 2 + j * 0.5))
        c.ring(sx, 92, 10 * pulse, 7.5 * pulse, (152, 146, 190, 180))
        c.circle(sx, 92, 4 * pulse, (206, 198, 246, 200))
    _karaoke_notes(c, i, total, 64)
    return c


def _karaoke_frame_north(i, total=6):
    c = Canvas(128, 128)
    _karaoke_notes(c, i, total, 64)
    return c


def _karaoke_frame_side(c, i, total=6):
    p = float(i) / total
    c.line(KA_TOP_FRONT - 1, KA_TOP + 2, KA_TOP_FRONT - 1, KA_MARQ - 1, (255, 240, 220, 150 + 90 * (i % 2)), 2.4)
    c.line(KA_TOP_FRONT, KA_MARQ, KA_SCR_FOOT, KA_SCR_BOT, (250, 226, 120, 170 + int(60 * math.sin(2 * math.pi * p * 2))), 2.4)
    for j, (y0, y1) in enumerate(((KA_DECK + 14, KA_DECK + 24), (KA_BASE - 24, KA_BASE - 12))):
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * (p * 2 + j * 0.5))
        c.rect(KA_BODY_FRONT + 1, y0 - 2 * pulse, KA_BODY_FRONT + 3 + 3 * pulse, y1 + 2 * pulse, (152, 146, 190, int(90 + 120 * pulse)), 1)
    _karaoke_notes(c, i, total, 84, 14)



def karaoke_machine():
    views = {}
    for facing in ("north", "east", "south", "west"):
        c = Canvas(128, 128)
        if facing == "south":
            _karaoke_front(c)
        elif facing == "north":
            _karaoke_back(c)
        else:
            _karaoke_side(MirrorCanvas(c) if facing == "west" else c)
        c.save(os.path.join(OUT, "KaraokeMachine_%s.png" % facing))
        views[facing] = c
    print("  KaraokeMachine_{north,east,south,west}.png  (128x128)")
    return views["south"]


def karaoke_frames(total=6):
    """One strip per facing (perFacing): lyrics, the marquee chase and the
    speakers from the front; notes rising from every side; the screen's edge
    and the speakers' rims side-on."""
    for i in range(total):
        _karaoke_frame_south(i, total).save(os.path.join(OUT, "KaraokeMachineSingSouth_%d.png" % i))
        _karaoke_frame_north(i, total).save(os.path.join(OUT, "KaraokeMachineSingNorth_%d.png" % i))
        for facing in ("east", "west"):
            c = Canvas(128, 128)
            _karaoke_frame_side(MirrorCanvas(c) if facing == "west" else c, i, total)
            c.save(os.path.join(OUT, "KaraokeMachineSing%s_%d.png" % (facing.capitalize(), i)))
    print("  KaraokeMachineSing{North,East,South,West}_0..%d.png  (128x128)" % (total - 1))


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

    court_line = (14, 18, 30, 255)                               # interior tint
    for gy in (54, 330):                                         # goal rings
        c.ring(mid, gy, 40, 33, court_line)
        c.ring(mid, gy, 38, 35, (126, 236, 240, 220))
        c.ring(mid, gy, 33, 31, (70, 140, 168, 200))
    for cx, cy in ((44, 44), (340, 44), (44, 340), (340, 340)):  # emitter posts
        c.circle(cx, cy, 20, court_line)
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
    save_single(orrery_case(c), "TabletopOrrery")
    return c


ORRERY_DROP = 44


def orrery_case(top):
    """The tabletop orrery's wooden case under its top: the front with a
    drawer, and brass feet. Padded ORRERY_DROP above as well, so the top and
    its turning gears stay centred (drawSize 1.2 x 1.86)."""
    d = ORRERY_DROP
    c = Canvas(160, 160 + 2 * d)
    wood = (104, 70, 44, 255)
    c.ellipse(80, 160 + 2 * d - 4, 66, 5, (0, 0, 0, 50))
    for fx in (26, 134):                                        # brass feet
        c.rect(fx - 7, d + 180, fx + 7, 160 + 2 * d - 2, DARK, 3)
        c.rect(fx - 5, d + 181, fx + 5, 160 + 2 * d - 4, (190, 150, 70, 255), 2)
    c.rect(16, d + 130, 144, d + 186, DARK, 6)
    c.rect(19, d + 133, 141, d + 183, darker(wood, 0.8), 5)     # the case's front
    c.rect(52, d + 156, 108, d + 176, darker(wood, 0.55), 3)    # drawer
    c.circle(80, d + 166, 3, (214, 176, 92, 255))
    c.line(20, d + 180, 140, d + 180, darker(wood, 0.6), 1.4)
    lay_over(c, top.pixels(), 160, 160, 0, d)
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


def _pool_filter_view(facing):
    """A filter tank and a pump on a skid. The pump, its fan cover and the
    control box face the way the unit does; the tank stands taller than the
    footprint, so the canvas is 2x2 tiles (160 px each) around it."""
    import math
    c = Canvas(320, 320)
    steel = (150, 156, 164, 255)
    tank = (64, 110, 150, 255)

    def tank_at(cv, x0, x1, top, bottom, rim_rx, rim_ry):
        silhouette(cv, [("rect", x0, top, x1, bottom, 14, tank)], 4.0)
        cx = (x0 + x1) / 2.0
        cv.rect(x0, top + 4, x1, bottom, tank, 0)
        cv.ellipse(cx, top + 4, rim_rx, rim_ry, lighter(tank, 0.3))
        cv.ellipse(cx, top + 4, rim_rx - 10, rim_ry - 5, lighter(tank, 0.15))
        cv.circle(cx, top, 9, steel)
        cv.circle(cx, top, 5, (90, 96, 104, 255))
        cv.line(x0 + 14, top + 20, x0 + 14, bottom - 6, lighter(tank, 0.25), 3)
        for y in (top + (bottom - top) * 0.36, top + (bottom - top) * 0.72):
            cv.line(x0, y, x1, y, darker(tank, 0.7), 2)

    def controls(cv, x, y):
        cv.rect(x - 22, y - 12, x + 22, y + 12, DARK, 3)
        cv.rect(x - 19, y - 9, x + 19, y + 9, (40, 44, 50, 255), 2)
        for k in range(3):
            cv.rect(x - 15 + k * 11, y - 4, x - 8 + k * 11, y + 4, (120, 226, 140, 255), 1)

    if facing == "south":                                   # footprint x 80..240, y 0..320
        c.ellipse(160, 314, 82, 6, (0, 0, 0, 55))
        c.rect(84, 236, 236, 312, DARK, 4)
        c.rect(87, 239, 233, 309, (92, 96, 104, 255), 3)             # skid
        tank_at(c, 100, 220, 40, 232, 60, 16)
        c.rect(110, 232, 210, 300, DARK, 10)
        c.rect(113, 235, 207, 297, steel, 9)                         # pump, fan cover toward us
        c.circle(160, 266, 26, DARK)
        c.circle(160, 266, 23, (110, 116, 124, 255))
        for k in range(8):
            a = k * math.pi / 4
            c.line(160, 266, 160 + 20 * math.cos(a), 266 + 20 * math.sin(a), (70, 74, 80, 255), 2)
        controls(c, 208, 250)
        for px in (118, 202):                                        # pipes
            c.rect(px - 5, 226, px + 5, 312, DARK, 2)
            c.rect(px - 3, 228, px + 3, 310, (200, 204, 210, 255), 1)
    elif facing == "north":                                 # the pump at the far end, the tank nearest
        c.ellipse(160, 314, 82, 6, (0, 0, 0, 55))
        c.rect(84, 60, 236, 312, DARK, 4)
        c.rect(87, 63, 233, 309, (92, 96, 104, 255), 3)
        c.rect(104, 40, 216, 110, DARK, 10)
        c.rect(107, 43, 213, 107, darker(steel, 0.85), 9)
        for x in range(114, 206, 8):
            c.line(x, 48, x, 102, darker(steel, 0.7), 1.5)           # cooling fins
        c.rect(196, 30, 232, 56, DARK, 3)
        c.rect(199, 33, 229, 53, (40, 44, 50, 255), 2)
        tank_at(c, 100, 220, 110, 300, 60, 16)
    else:                                                   # side-on; footprint y 80..240
        m = MirrorCanvas(c) if facing == "west" else c
        c.ellipse(160, 236, 150, 6, (0, 0, 0, 55))
        m.rect(8, 200, 312, 238, DARK, 4)
        m.rect(11, 203, 309, 235, (92, 96, 104, 255), 3)             # skid
        tank_at(m, 24, 144, 30, 200, 60, 14)
        silhouette(m, [("rect", 168, 140, 290, 200, 12, steel)], 3.5)   # pump, lying along
        for x in range(176, 250, 8):
            m.line(x, 146, x, 194, darker(steel, 0.8), 1.5)
        m.rect(270, 144, 296, 196, (110, 116, 124, 255), 8)          # fan cover, toward the front
        m.line(144, 170, 168, 170, (200, 204, 210, 255), 6)          # pipe, tank to pump
        m.rect(290, 150, 314, 190, DARK, 3)
        m.rect(293, 153, 311, 187, (40, 44, 50, 255), 2)             # control box, on the front
        for k in range(3):
            m.rect(299, 158 + k * 9, 305, 164 + k * 9, (120, 226, 140, 255), 1)
    return c


def pool_filter():
    for facing in ("north", "east", "south", "west"):
        _pool_filter_view(facing).save(os.path.join(OUT, "PoolFilter_%s.png" % facing))
    print("  PoolFilter_{north,east,south,west}.png  (320x320)")
    return _pool_filter_view("south")


# ---------------------------------------------------------------------------
# 23. Hammock  (1x2, stuffable, a pawn lies in it)
# ---------------------------------------------------------------------------

def hammock():
    """Near-neutral, because the stuff colour tints the whole sprite.

    No posts of its own: it is slung between whatever is standing at each end -
    a wall or a column - so the cords gather to a point right at the edge of
    the sprite, where that support is. The bold line goes round the sheet and
    nothing inside it; the weave, the sag and the cushion are tints."""
    c = Canvas(160, 320)
    mid = 80
    OUT = 4.5
    body = (208, 200, 188, 255)
    weave = (184, 176, 164, 210)
    selvedge = (170, 162, 150, 235)
    cord = (104, 94, 82, 255)
    cord_lt = (140, 128, 114, 255)

    head, foot = 84, 236          # where the sheet begins and ends

    def sag(y):
        """Half-width of the sheet at height y: gathered at the ends, slack in
        the middle, which is the whole shape of the thing."""
        t = max(0.0, min(1.0, (y - head) / float(foot - head)))
        return 34 + 30 * math.sin(math.pi * t)

    # Cords running off to the supports at either end, drawn first so the
    # sheet sits on top of them.
    for end_y, toward in ((head, 4), (foot, 316)):
        for k in range(-3, 4):
            spread = k * 9
            c.line(mid + spread, end_y, mid + k * 1.5, toward, cord, 2.8)
            c.line(mid + spread, end_y, mid + k * 1.5, toward, cord_lt, 1.2)
        c.circle(mid, toward, 5, DARK)             # the ring it hangs from
        c.circle(mid, toward, 3.4, cord_lt)

    # The sheet: one pass oversized in the outline colour, one at true size.
    for y in range(head - int(OUT) - 1, foot + int(OUT) + 1):
        w = sag(y) + OUT
        c.rect(mid - w, y, mid + w, y + 1, DARK)
    for y in range(head, foot):
        w = sag(y)
        c.rect(mid - w, y, mid + w, y + 1, body)

    for k in range(11):                            # weave, following the sag
        t = (k + 0.5) / 11.0
        y = head + t * (foot - head)
        w = sag(y)
        c.line(mid - w + 4, y, mid + w - 4, y, weave, 1.6)
    c.line(mid, head + 6, mid, foot - 6, selvedge, 1.4)     # the fold

    for sx in (-1, 1):                             # rolled edge, a tint
        for y in range(head + 2, foot - 1, 2):
            c.circle(mid + sx * (sag(y) - 2), y, 2.2, selvedge)

    c.rect(mid - 21, 146, mid + 21, 174, (226, 220, 210, 255), 9)   # cushion
    c.line(mid - 15, 160, mid + 15, 160, weave, 1.6)
    save_rotations(c, "Hammock")
    return c

# ---------------------------------------------------------------------------
# 24. Cornhole set  (1x5, a board at each end, wood and cloth)
# ---------------------------------------------------------------------------

CH_PLANK = (176, 132, 82, 255)
CH_PLANK_LT = (204, 166, 116, 255)
CH_PLANK_DK = (140, 100, 60, 255)
CH_SEAM = (156, 114, 70, 220)
# Side-on (east; west is the same drawing mirrored): the hole end is raised,
# so the board's top is a slanted strip, higher at that end. These place it;
# CompCornholeGame lands sacks on the same strip.
CH_SIDE_X = (12, 244)
CH_SIDE_EDGE = (66, 96)           # the top's near edge at each end, y
CH_SIDE_DEPTH = 34                # how deep the top reads, foreshortened
CH_SIDE_GROUND = 106


def _ch_side_edge(x):
    x0, x1 = CH_SIDE_X
    return CH_SIDE_EDGE[0] + (x - x0) * float(CH_SIDE_EDGE[1] - CH_SIDE_EDGE[0]) / (x1 - x0)


def _ch_hole(c, x, y, rx=15, ry=15):
    c.ellipse(x, y, rx, ry, CH_PLANK_DK)
    c.ellipse(x, y, rx * 0.8, ry * 0.8, (34, 28, 22, 255))
    c.ellipse(x, y - ry * 0.12, rx * 0.6, ry * 0.6, (22, 18, 14, 255))


def _ch_slope(c, x0, x1, y0, y1, dark_at_bottom):
    """Plank shading in bands: pale at the raised end, darker toward the low."""
    for k in range(12):
        t = k / 11.0
        ya = y0 + (y1 - y0) * k / 12.0
        yb = y0 + (y1 - y0) * (k + 1) / 12.0 + 1
        f = (1 - t) if dark_at_bottom else t
        shade = tuple(int(CH_PLANK_DK[i] + (CH_PLANK_LT[i] - CH_PLANK_DK[i]) * f) for i in range(3))
        c.rect(x0, ya, x1, yb, shade + (255,), 0)


def cornhole_view(facing):
    """A two-tile board with its hole end raised on folding legs.

    Facing south the thrower's end is nearest and low, so the board is mostly
    its top. Facing north the raised end is nearest: its end panel and legs
    stand at the bottom and the top slopes away. Side-on it is a slanted strip
    over its side rail, with the legs under the high end."""
    if facing in ("east", "west"):
        base = Canvas(256, 128)
        c = MirrorCanvas(base) if facing == "west" else base
        x0, x1 = CH_SIDE_X
        edge, depth, ground = _ch_side_edge, CH_SIDE_DEPTH, CH_SIDE_GROUND
        c.ellipse(128, ground + 2, 118, 6, (0, 0, 0, 50))
        for lx, col in ((x0 + 20, CH_PLANK_DK), (x0 + 8, darker(CH_PLANK_DK, 0.8))):   # legs
            c.rect(lx - 4, edge(lx) + 6, lx + 4, ground, DARK, 2)
            c.rect(lx - 2.5, edge(lx) + 7, lx + 2.5, ground - 1, col, 1.5)
        top = [(x0, edge(x0) - depth), (x1, edge(x1) - depth), (x1, edge(x1)), (x0, edge(x0))]
        rail = [(x0, edge(x0)), (x1, edge(x1)), (x1, edge(x1) + 10), (x0, edge(x0) + 10)]
        silhouette(c, [("poly", top, CH_PLANK), ("poly", rail, CH_PLANK_DK)], 3.5)
        for k in range(12):                                     # the slope
            t = k / 12.0
            xa = x0 + (x1 - x0) * t
            xb = x0 + (x1 - x0) * (t + 1 / 12.0) + 1
            shade = tuple(int(CH_PLANK_LT[i] + (CH_PLANK_DK[i] - CH_PLANK_LT[i]) * t * 0.6) for i in range(3))
            c.poly([(xa, edge(xa) - depth + 2), (xb, edge(xb) - depth + 2),
                    (xb, edge(xb) - 1), (xa, edge(xa) - 1)], shade + (255,))
        for k in range(1, 4):                                   # plank seams, foreshortened
            c.line(x0 + 4, edge(x0) - depth * k / 4.0, x1 - 4, edge(x1) - depth * k / 4.0,
                   (156, 114, 70, 200), 1.2)
        hx = x0 + 46
        _ch_hole(c, hx, edge(hx) - depth / 2.0, 14, 7.5)
        c.line(x0 + 2, edge(x0) + 5, x1 - 2, edge(x1) + 5, darker(CH_PLANK_DK, 0.75), 1.2)
        return base

    c = Canvas(128, 256)
    mid = 64
    if facing == "south":
        top, bottom = 6, 238
        c.ellipse(mid, 248, 50, 5, (0, 0, 0, 50))
        silhouette(c, [("rect", mid - 44, top, mid + 44, bottom, 6, CH_PLANK),
                       ("rect", mid - 44, bottom - 4, mid + 44, bottom + 7, 2, CH_PLANK_DK)], 4.0)
        _ch_slope(c, mid - 40, mid + 40, top, bottom, True)
        for k in range(4):
            x = mid - 40 + (k + 1) * 16
            c.line(x, top + 6, x, bottom - 6, CH_SEAM, 1.6)
        _ch_hole(c, mid, top + 40)
        c.rect(mid - 44, bottom - 1, mid + 44, bottom + 6, CH_PLANK_DK, 2)   # the low front edge
        return c

    top, edge_y, ground = 12, 196, 244
    c.ellipse(mid, ground + 2, 50, 5, (0, 0, 0, 50))
    for lx in (mid - 36, mid + 36):                             # legs under the near, raised end
        c.rect(lx - 5, edge_y + 20, lx + 5, ground, DARK, 2)
        c.rect(lx - 3, edge_y + 21, lx + 3, ground - 1, CH_PLANK_DK, 1.5)
    silhouette(c, [("rect", mid - 44, top, mid + 44, edge_y, 6, CH_PLANK),
                   ("rect", mid - 44, edge_y - 4, mid + 44, edge_y + 22, 3, CH_PLANK_DK)], 4.0)
    _ch_slope(c, mid - 40, mid + 40, top, edge_y, False)
    for k in range(4):
        x = mid - 40 + (k + 1) * 16
        c.line(x, top + 6, x, edge_y - 4, CH_SEAM, 1.6)
    _ch_hole(c, mid, edge_y - 36)
    c.rect(mid - 44, edge_y, mid + 44, edge_y + 20, CH_PLANK_DK, 3)          # the raised end's face
    for k in range(3):
        c.line(mid - 42, edge_y + 5 + k * 5, mid + 42, edge_y + 5 + k * 5, darker(CH_PLANK_DK, 0.8), 1.2)
    return c


def cornhole_board():
    for facing in ("north", "east", "south", "west"):
        cornhole_view(facing).save(os.path.join(OUT, "CornholeBoard_%s.png" % facing))
    print("  CornholeBoard_{north,east,south,west}.png")
    return cornhole_view("south")


def cornhole_sack():
    """A bean bag from above. Painted white so the comp can tint it to
    whichever player threw it."""
    c = Canvas(64, 64)
    body = (255, 255, 255, 255)
    c.rect(10, 14, 54, 50, (60, 54, 48, 255), 13)             # outline
    c.rect(13, 17, 51, 47, body, 11)
    # Slumped corners and a seam, so it reads as full of something.
    for cx, cy in ((20, 24), (44, 24), (20, 40), (44, 40)):
        c.circle(cx, cy, 7, (238, 238, 238, 255))
    # One soft seam only. Two crossed ones read as a plus sign once the sack
    # is drawn a third of a tile across.
    c.line(18, 33, 46, 31, (222, 222, 222, 150), 2.0)
    c.circle(26, 25, 5, (255, 255, 255, 170))                 # highlight
    save_single(c, "CornholeSack")
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
    drill = cocktail_arcade()
    cocktail_arcade_frames()
    cocktail_arcade_title_frames()
    climb = cocktail_climb()
    cocktail_climb_frames()
    cocktail_climb_title_frames()
    return {"CocktailArcade": drill, "CocktailClimb": climb}


def _build_hologamepod():
    return {"HologamePod": hologame_pod()}


def _build_holotheater():
    canvas = dreamloop_holotheater()
    sample = dreamloop_projection_frames()
    return {"DreamloopHolotheater": canvas, "DreamloopProjection": sample}


def _build_vistapanel():
    made = dict(vista_panel())
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
    soaking_tub_water_frames("SoakingTubElectricWater", electric=True)
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
    aquarium_fish_profiles()
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


def _build_cornhole():
    made = {"CornholeBoard": cornhole_board()}
    cornhole_sack()
    return made


_register("gravball", _build_gravball)
_register("orreries", _build_orreries)
_register("pool", _build_pool)
_register("hammock", _build_hammock)
_register("cornhole", _build_cornhole)



# ---------------------------------------------------------------------------
# Jigsaw table  (2x2, non-rotatable) and the framed puzzles it turns out
#
# The table is plain furniture, drawn in pale neutrals so the stuff it is made
# from tints it the way vanilla furniture is tinted. The puzzle is not part of
# that texture: it is a separate overlay the comp draws on top, one of seven
# stages per picture, so the picture keeps its own colours whatever the table
# is made of and visibly fills in as colonists work on it.
#
# Pieces go in the way people actually do a jigsaw: a run of edge pieces from
# a corner first, then the rest of the border, then the middle filling inward
# from the frame in blobs.
# ---------------------------------------------------------------------------

JIGSAW_COLS, JIGSAW_ROWS = 12, 9
JIGSAW_PIECE = 15
JIGSAW_X, JIGSAW_Y = 38, 38                      # puzzle area on the table
JIGSAW_W = JIGSAW_COLS * JIGSAW_PIECE             # 180
JIGSAW_H = JIGSAW_ROWS * JIGSAW_PIECE             # 135
# Fraction of pieces in place at each stage. The last stage is only ever shown
# when the puzzle is finished; the one before it is "nearly there".
JIGSAW_STAGES = (0.0, 0.15, 0.35, 0.55, 0.72, 0.88, 1.0)
JIGSAW_PICTURES = ("ThrumboDawn", "MuffaloCrossing", "LaunchDay", "BoomalopePicnic")


def _sky(c, x0, y0, w, h, top, bottom, bands=16):
    for b in range(bands):
        t = b / float(bands - 1)
        col = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        c.rect(x0, y0 + h * b / float(bands), x0 + w, y0 + h * (b + 1) / float(bands) + 1,
               col + (255,), 0)


def _ridge(c, x0, y0, w, h, points, color):
    """A filled band of land from a list of (x fraction, y fraction) points
    down to the bottom of the picture."""
    c.poly([(x0 + w * fx, y0 + h * fy) for fx, fy in points]
           + [(x0 + w, y0 + h), (x0, y0 + h)], color)


def draw_jigsaw_scene(c, name, x0, y0, w, h):
    """One of the puzzle pictures, laid out in fractions of the area given so
    the same scene serves the table-sized puzzle and the small framed one."""
    import random
    rng = random.Random(name)

    def X(f):
        return x0 + w * f

    def Y(f):
        return y0 + h * f

    s = min(w / 180.0, h / 135.0)                  # detail scale

    if name == "ThrumboDawn":
        _sky(c, x0, y0, w, h * 0.62, (92, 104, 168), (250, 182, 136))
        c.circle(X(0.24), Y(0.5), 22 * s, (255, 214, 160, 70))
        c.circle(X(0.24), Y(0.5), 12 * s, (255, 232, 186, 255))
        _ridge(c, x0, y0, w, h, ((0, .52), (.18, .40), (.36, .50), (.58, .36),
                                 (.8, .48), (1, .42)), (206, 204, 226, 255))
        _ridge(c, x0, y0, w, h, ((0, .70), (.25, .62), (.5, .70), (.75, .60),
                                 (1, .68)), (238, 240, 248, 255))
        c.poly([(X(.5), Y(.74)), (X(1), Y(.64)), (X(1), Y(1)), (X(.62), Y(1))],
               (212, 218, 238, 255))                                    # snow shadow
        for fx, fy, sc in ((.06, .62, 1.0), (.13, .66, .8), (.9, .6, .9)):   # pines
            px, py, pw = X(fx), Y(fy), 9 * s * sc
            c.poly([(px, py - 26 * s * sc), (px + pw, py), (px - pw, py)], (44, 70, 64, 255))
            c.poly([(px, py - 34 * s * sc), (px + pw * .7, py - 12 * s * sc),
                    (px - pw * .7, py - 12 * s * sc)], (54, 84, 74, 255))
        # The thrumbo, side on, one horn swept forward.
        tx, ty = X(.6), Y(.62)
        fur, fur_dk = (244, 244, 250, 255), (196, 198, 214, 255)
        for lx in (-20, -9, 8, 19):
            c.rect(tx + lx * s, ty + 4 * s, tx + (lx + 6) * s, ty + 18 * s, fur_dk, 2 * s)
        c.ellipse(tx, ty, 30 * s, 15 * s, fur_dk)
        c.ellipse(tx - 1 * s, ty - 1 * s, 28 * s, 13.5 * s, fur)
        c.ellipse(tx + 29 * s, ty - 6 * s, 11 * s, 9 * s, fur_dk)
        c.ellipse(tx + 29 * s, ty - 7 * s, 10 * s, 8 * s, fur)
        c.poly([(tx + 34 * s, ty - 12 * s), (tx + 50 * s, ty - 28 * s),
                (tx + 38 * s, ty - 9 * s)], (236, 214, 150, 255))      # horn
        c.circle(tx + 33 * s, ty - 8 * s, 1.6 * s, (60, 60, 80, 255))

    elif name == "MuffaloCrossing":
        _sky(c, x0, y0, w, h * 0.5, (160, 190, 220), (228, 232, 226))
        _ridge(c, x0, y0, w, h, ((0, .44), (.3, .38), (.55, .45), (.8, .36), (1, .42)),
               (150, 160, 170, 255))
        _ridge(c, x0, y0, w, h, ((0, .5), (1, .48)), (164, 158, 112, 255))
        c.poly([(X(0), Y(.66)), (X(1), Y(.58)), (X(1), Y(.72)), (X(0), Y(.8))],
               (104, 146, 186, 255))                                     # the river
        c.poly([(X(0), Y(.7)), (X(1), Y(.62)), (X(1), Y(.64)), (X(0), Y(.72))],
               (160, 196, 226, 255))
        _ridge(c, x0, y0, w, h, ((0, .82), (.5, .78), (1, .74)), (128, 132, 86, 255))
        # A herd wading across, smaller as they go into the distance.
        for fx, fy, sc in ((.2, .77, 1.0), (.44, .7, .8), (.64, .65, .64), (.82, .61, .5)):
            mx, my, r = X(fx), Y(fy), 17 * s * sc
            coat, coat_dk = (122, 86, 56, 255), (84, 58, 38, 255)
            c.ellipse(mx, my, r * 1.3, r * .78, coat_dk)
            c.ellipse(mx - r * .05, my - r * .08, r * 1.2, r * .68, coat)
            c.ellipse(mx - r * .45, my - r * .5, r * .75, r * .5, coat)              # hump
            for k in range(5):                                                   # shag
                c.line(mx - r * (0.9 - k * .35), my + r * .35, mx - r * (0.95 - k * .35),
                       my + r * .72, coat_dk, max(1.0, r * .12))
            c.ellipse(mx + r * 1.2, my - r * .05, r * .5, r * .44, coat_dk)          # head
            c.ellipse(mx + r * 1.36, my + r * .02, r * .26, r * .24, (206, 184, 150, 255))
            for side in (-1, 1):                                                 # horns
                c.line(mx + r * 1.1, my - r * .35, mx + r * (1.1 + .35 * side), my - r * .8,
                       (236, 226, 196, 255), max(1.2, r * .14))
            c.rect(mx - r * 1.35, my + r * .5, mx + r * 1.6, my + r * .72,
                   (160, 198, 228, 190), r * .2)                                  # wake

    elif name == "LaunchDay":
        _sky(c, x0, y0, w, h, (10, 14, 38), (46, 56, 104))
        for k in range(40):
            c.circle(X(rng.random()), Y(rng.random() * .6), (0.6 + rng.random()) * s,
                     (236, 240, 255, 110 + rng.randint(0, 140)))
        _ridge(c, x0, y0, w, h, ((0, .7), (.2, .56), (.4, .66), (.66, .5), (.86, .64), (1, .58)),
               (30, 32, 52, 255))
        # The plume first, so the ship sits in front of its own fire.
        sx = X(.55)
        c.ellipse(sx, Y(.6), 26 * s, 50 * s, (255, 150, 60, 60))
        c.ellipse(sx, Y(.62), 9 * s, 30 * s, (255, 176, 80, 220))
        c.ellipse(sx, Y(.58), 5 * s, 20 * s, (255, 240, 190, 255))
        for k in range(7):
            fx = .38 + k * .05
            c.circle(X(fx), Y(.82 + 0.03 * (k % 2)), (10 + (k % 3) * 3) * s, (132, 128, 140, 230))
        hull, hull_dk = (206, 210, 222, 255), (150, 156, 172, 255)
        c.rect(sx - 7 * s, Y(.1), sx + 7 * s, Y(.44), hull_dk, 3 * s)
        c.rect(sx - 5.5 * s, Y(.11), sx + 5 * s, Y(.43), hull, 2 * s)
        c.poly([(sx - 7 * s, Y(.11)), (sx, Y(.02)), (sx + 7 * s, Y(.11))], hull)
        for fin in (-1, 1):
            c.poly([(sx + fin * 7 * s, Y(.34)), (sx + fin * 14 * s, Y(.46)),
                    (sx + fin * 7 * s, Y(.44))], hull_dk)
        c.circle(sx, Y(.2), 2.4 * s, (120, 200, 255, 255))
        # The colony it is leaving behind, lights still on.
        _ridge(c, x0, y0, w, h, ((0, .86), (1, .84)), (22, 22, 34, 255))
        for bx, bw, bh in ((.06, .1, .1), (.18, .08, .14), (.72, .12, .09), (.86, .09, .12)):
            c.rect(X(bx), Y(.86 - bh), X(bx + bw), Y(.87), (26, 26, 40, 255), 0)
            for wx in range(2):
                c.rect(X(bx + bw * (0.25 + 0.4 * wx)), Y(.86 - bh * .7),
                       X(bx + bw * (0.25 + 0.4 * wx)) + 3 * s, Y(.86 - bh * .7) + 3 * s,
                       (255, 214, 120, 255), 0)

    elif name == "BoomalopePicnic":
        _sky(c, x0, y0, w, h * .5, (104, 164, 228), (198, 226, 246))
        c.ellipse(X(.2), Y(.16), 16 * s, 6 * s, (255, 255, 255, 200))
        c.ellipse(X(.28), Y(.14), 12 * s, 6 * s, (255, 255, 255, 200))
        _ridge(c, x0, y0, w, h, ((0, .48), (.4, .42), (.7, .5), (1, .44)), (120, 176, 96, 255))
        _ridge(c, x0, y0, w, h, ((0, .6), (.5, .56), (1, .62)), (142, 196, 104, 255))
        # Something went off in the distance. Nobody at the picnic has noticed.
        bx, by = X(.82), Y(.44)
        c.circle(bx, by - 6 * s, 12 * s, (150, 146, 140, 200))
        c.circle(bx, by, 9 * s, (255, 180, 70, 255))
        c.circle(bx, by, 5 * s, (255, 240, 170, 255))
        for k in range(26):
            c.circle(X(rng.random()), Y(.6 + rng.random() * .38), 1.4 * s,
                     rng.choice(((250, 240, 120, 255), (250, 250, 250, 255), (236, 140, 180, 255))))
        # The blanket, checked.
        px, py, pw, ph = X(.12), Y(.76), 40 * s, 18 * s
        c.poly([(px, py), (px + pw, py - 4 * s), (px + pw + 6 * s, py + ph), (px + 4 * s, py + ph + 3 * s)],
               (238, 238, 232, 255))
        for i in range(4):
            for j in range(2):
                if (i + j) % 2 == 0:
                    c.rect(px + 3 * s + i * 10 * s, py + 1 * s + j * 8 * s,
                           px + 3 * s + (i + 1) * 10 * s, py + 1 * s + (j + 1) * 8 * s,
                           (206, 64, 58, 255), 0)
        # Boomalopes grazing, sacs glowing.
        for fx, fy, sc in ((.52, .76, 1.0), (.72, .68, .78), (.36, .64, .62)):
            mx, my, r = X(fx), Y(fy), 15 * s * sc
            hide, hide_dk = (190, 170, 138, 255), (138, 120, 96, 255)
            for lx in (-.8, -.35, .3, .7):                                        # legs
                c.rect(mx + r * lx - r * .12, my + r * .35, mx + r * lx + r * .12, my + r * 1.0,
                       hide_dk, r * .08)
            c.ellipse(mx, my, r * 1.2, r * .7, hide_dk)
            c.ellipse(mx - r * .05, my - r * .06, r * 1.1, r * .6, hide)
            c.ellipse(mx - r * .15, my - r * .55, r * .62, r * .42, (220, 86, 40, 255))   # sac
            c.ellipse(mx - r * .28, my - r * .66, r * .26, r * .15, (255, 200, 120, 255))
            c.ellipse(mx + r * 1.05, my + r * .28, r * .34, r * .3, hide_dk)             # head,
            c.ellipse(mx + r * 1.05, my + r * .25, r * .28, r * .24, hide)               # down grazing
            c.circle(mx + r * 1.12, my + r * .18, max(0.8, r * .06), (40, 34, 30, 255))
    else:
        raise ValueError(name)


def _order_pieces(name):
    """The order pieces go in: edge run, rest of the border, then inward."""
    import random
    rng = random.Random("order-" + name)
    cols, rows = JIGSAW_COLS, JIGSAW_ROWS
    ring = ([(i, 0) for i in range(cols)] + [(cols - 1, j) for j in range(1, rows)]
            + [(i, rows - 1) for i in range(cols - 2, -1, -1)]
            + [(0, j) for j in range(rows - 2, 0, -1)])
    start = rng.choice((0, cols - 1, cols + rows - 2, 2 * cols + rows - 3))   # a corner
    ring = ring[start:] + ring[:start]
    order = list(ring)
    placed = set(order)
    inner = [(i, j) for i in range(1, cols - 1) for j in range(1, rows - 1)]
    frontier = [cell for cell in inner
                if any((cell[0] + dx, cell[1] + dy) in placed
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    while len(order) < cols * rows:
        # Grow from wherever is already done, in small blobs.
        rng.shuffle(frontier)
        cell = frontier.pop()
        if cell in placed:
            continue
        order.append(cell)
        placed.add(cell)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cell[0] + dx, cell[1] + dy)
            if n in inner and n not in placed:
                frontier.append(n)
    return order


def _paste(dst, dw, src, sw, sh, ox, oy, shade=None):
    """Copy an RGBA block into a bigger buffer. `shade(x, y)` may darken
    individual pixels, which is how the seams between pieces are drawn."""
    for y in range(sh):
        for x in range(sw):
            si = (y * sw + x) * 4
            if src[si + 3] == 0:
                continue
            di = ((oy + y) * dw + ox + x) * 4
            f = shade(x, y) if shade else 1.0
            dst[di] = int(src[si] * f)
            dst[di + 1] = int(src[si + 1] * f)
            dst[di + 2] = int(src[si + 2] * f)
            dst[di + 3] = src[si + 3]


def _over(dst, src):
    """Alpha-composite one full-size RGBA buffer onto another, in place."""
    for i in range(0, len(dst), 4):
        a = src[i + 3]
        if a == 0:
            continue
        if a == 255 or dst[i + 3] == 0:
            dst[i:i + 4] = src[i:i + 4]
            continue
        fa, ba = a / 255.0, dst[i + 3] / 255.0
        oa = fa + ba * (1 - fa)
        for k in range(3):
            dst[i + k] = int((src[i + k] * fa + dst[i + k] * ba * (1 - fa)) / oa)
        dst[i + 3] = int(oa * 255)


GAME_TABLE_DROP = 50


def jigsaw_table():
    """The jigsaw table, which the board game table shares: a wooden table with
    a pale play surface set into its top, and its front edge and two legs
    under the south edge. Padded GAME_TABLE_DROP above as well, so the top -
    where the puzzle and the boards are drawn - stays on the footprint
    (drawSize 2 x 2.78)."""
    d = GAME_TABLE_DROP
    c = Canvas(256, 256 + 2 * d)
    wood = (150, 104, 62, 255)
    table_legs(c, 12, 244, d + 246, d + 6, darker(wood, 0.85), darker(wood, 0.7), (26, 230))
    silhouette(c, [("rect", 8, d + 8, 248, d + 248, 10, wood)], 4.0)
    c.rect(12, d + 12, 244, d + 22, lighter(wood, 0.15), 8)          # far edge catching the light
    for k in range(1, 6):
        c.line(10, d + 8 + k * 40, 246, d + 8 + k * 40, darker(wood, 0.85), 1.2)
    c.rect(22, d + 22, 234, d + 234, darker(wood, 0.6), 6)
    c.rect(26, d + 26, 230, d + 230, (236, 228, 206, 255), 5)         # the play surface
    c.frame(26, d + 26, 230, d + 230, (210, 198, 170, 255), 2, 5)
    save_single(c, "JigsawTable")
    return c


def jigsaw_stages():
    import random
    size = 256
    for name in JIGSAW_PICTURES:
        scene = Canvas(JIGSAW_W, JIGSAW_H)
        draw_jigsaw_scene(scene, name, 0, 0, JIGSAW_W, JIGSAW_H)
        sp = scene.pixels()
        lid = Canvas(60, 45)
        draw_jigsaw_scene(lid, name, 0, 0, 60, 45)
        lp = lid.pixels()
        order = _order_pieces(name)
        total = len(order)

        def colour_of(cell):
            cx = cell[0] * JIGSAW_PIECE + JIGSAW_PIECE // 2
            cy = cell[1] * JIGSAW_PIECE + JIGSAW_PIECE // 2
            i = (cy * JIGSAW_W + cx) * 4
            return (sp[i], sp[i + 1], sp[i + 2], 255)

        for stage, fraction in enumerate(JIGSAW_STAGES):
            count = int(round(fraction * total))
            placed = set(order[:count])
            buf = bytearray(size * size * 4)

            # Pieces in place, each with a seam that is a shade of the picture
            # rather than a line on top of it.
            for (i, j) in placed:
                block = bytearray(JIGSAW_PIECE * JIGSAW_PIECE * 4)
                for y in range(JIGSAW_PIECE):
                    row = ((j * JIGSAW_PIECE + y) * JIGSAW_W + i * JIGSAW_PIECE) * 4
                    block[y * JIGSAW_PIECE * 4:(y + 1) * JIGSAW_PIECE * 4] = \
                        sp[row:row + JIGSAW_PIECE * 4]

                def seam(x, y, i=i, j=j):
                    edge = x == 0 or y == 0
                    # A tab on each edge's middle, so it reads as a jigsaw.
                    tab = (x == 0 and 6 <= y <= 8 and i > 0) or (y == 0 and 6 <= x <= 8 and j > 0)
                    return 0.93 if tab else (0.8 if edge else 1.0)
                _paste(buf, size, block, JIGSAW_PIECE, JIGSAW_PIECE,
                       JIGSAW_X + i * JIGSAW_PIECE, JIGSAW_Y + j * JIGSAW_PIECE, seam)

            # Loose pieces, box and lid drawn as ordinary shapes on top.
            over = Canvas(size, size)
            rng = random.Random("%s-%d" % (name, stage))
            if count < total:
                remaining = order[count:]
                empty = [cell for cell in order if cell not in placed]
                shown = remaining[:min(len(remaining), 30)]
                for k, cell in enumerate(shown):
                    if k % 3 == 0:                     # a heap by the box
                        px = 40 + rng.random() * 90
                        py = 190 + rng.random() * 36
                    else:
                        # Strewn over whatever of the table is still empty -
                        # not over each piece's own slot, which would trace
                        # out the frame, since the edge pieces are next up.
                        spot = rng.choice(empty)
                        px = JIGSAW_X + (spot[0] + 0.5) * JIGSAW_PIECE + rng.uniform(-6, 6)
                        py = JIGSAW_Y + (spot[1] + 0.5) * JIGSAW_PIECE + rng.uniform(-6, 6)
                    ang = rng.uniform(0, math.pi)
                    col = colour_of(cell)
                    half = 6.2
                    pts = [(px + math.cos(ang + a) * half * 1.41, py + math.sin(ang + a) * half * 1.41)
                           for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4)]
                    over.poly(_grow_poly(pts, 1.1), darker(col, 0.55))
                    over.poly(pts, col)
                    over.circle(px + math.cos(ang) * 7, py + math.sin(ang) * 7, 2.6, col)
            # The box lid, standing in for the picture on the front of it.
            silhouette(over, [("rect", 160, 186, 228, 238, 3, (226, 220, 206, 255))], 3.0)
            ob = over.pixels()
            _over(buf, ob)
            _paste(buf, size, lp, 60, 45, 164, 190)
            write_png(os.path.join(OUT, "Jigsaw%s_%d.png" % (name, stage)), size, size, buf)
        print("  Jigsaw%s_{0..%d}.png  (%dx%d)" % (name, len(JIGSAW_STAGES) - 1, size, size))


def framed_jigsaws():
    """Each finished puzzle glued down and framed, to hang on a wall. Drawn
    to the one-tile vista panel's proportions, since it mounts the same way."""
    made = {}
    for name in JIGSAW_PICTURES:
        c = Canvas(128, 96)
        frame_col = (132, 92, 56, 255)
        silhouette(c, [("rect", 4, 6, 124, 90, 4, frame_col)], 4.0)
        c.frame(9, 11, 119, 85, darker(frame_col, 0.72), 2.0, 2)
        draw_jigsaw_scene(c, name, 13, 15, 102, 66)
        for k in range(1, JIGSAW_COLS):                       # faint seams
            x = 13 + 102.0 * k / JIGSAW_COLS
            c.line(x, 15, x, 81, (0, 0, 0, 34), 0.8)
        for k in range(1, JIGSAW_ROWS):
            y = 15 + 66.0 * k / JIGSAW_ROWS
            c.line(13, y, 115, y, (0, 0, 0, 34), 0.8)
        c.rect(13, 15, 115, 21, (255, 255, 255, 22), 0)      # glass sheen
        save_wall_piece(c, "FramedJigsaw%s" % name, 46)
        made["FramedJigsaw%s" % name] = c
    return made


def _build_jigsaw():
    made = {"JigsawTable": jigsaw_table()}
    jigsaw_stages()
    made.update(framed_jigsaws())
    return made


_register("jigsaw", _build_jigsaw)


# ---------------------------------------------------------------------------
# Storyteller's stump  (neolithic, 1x1, faces its audience)
#
# The teller cannot be posed without Harmony, so the stump itself is plain and
# the show happens in the smoke of the nearest fire: while a story is being
# told, shapes out of it - a thrumbo, a raider, a ship, a mechanoid - form in
# the smoke, climb and fade. Drawn lit by the fire rather than by the room, so
# they read at night, which is when stories get told.
# ---------------------------------------------------------------------------

STORY_MOTIFS = ("Thrumbo", "Raider", "Ship", "Mech")
STORY_FRAMES = 10


def _stump_view(facing):
    """Standing, like the tubs: the cut top with its rings, the bark side and
    roots below, and the small step up on the side it faces."""
    import math
    c = Canvas(128, 128)
    bark = (92, 64, 42, 255)
    cx, top_y, rx, ry, bot_y = 64, 50, 38, 16, 96

    def body():
        c.ellipse(cx, bot_y + 8, rx + 10, 9, (0, 0, 0, 55))
        pts = _arc(cx, top_y, rx, ry, 180, 360) + _arc(cx, bot_y, rx, ry * 0.8, 0, 180)
        c.poly(_grow_poly(pts, 3.5), DARK)
        for dx in (-rx + 2, rx - 4):                                 # roots
            c.ellipse(cx + dx, bot_y + 6, 12, 6, darker(bark, 0.9))
        c.poly(_arc(cx, top_y, rx, ry, 0, 180) + _arc(cx, bot_y, rx, ry * 0.8, 180, 0), bark)
        for k in range(1, 9):                                        # bark furrows
            a = math.radians(180 * k / 9.0)
            x = cx + rx * math.cos(a)
            c.line(x, top_y + ry * math.sin(a) + 2, x + math.sin(k) * 2,
                   bot_y + ry * 0.8 * math.sin(a) - 1, darker(bark, 0.65), 1.6)
        c.ellipse(cx, top_y, rx, ry, (206, 170, 120, 255))           # the cut top
        for r in range(6, rx, 6):
            pts = _arc(cx, top_y, r, r * ry / float(rx), 0, 360, 48)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                c.line(x0, y0, x1, y1, (176, 138, 92, 200), 1)
        c.line(cx, top_y, cx + 18, top_y - 5, (150, 110, 70, 200), 1.4)   # a crack

    def step(cv, x, y):
        cv.poly(_grow_poly([(x - 16, y - 6), (x + 16, y - 6), (x + 16, y + 8), (x - 16, y + 8)], 3), DARK)
        cv.rect(x - 16, y - 6, x + 16, y + 8, darker(bark, 0.9), 2)
        cv.ellipse(x, y - 6, 16, 5, (196, 160, 112, 255))

    if facing == "north":
        step(c, cx, top_y - 16)
        body()
    elif facing == "south":
        body()
        step(c, cx, bot_y + 12)
    else:
        body()
        step(MirrorCanvas(c) if facing == "west" else c, cx + rx + 6, bot_y - 2)
    return c


def storyteller_stump():
    for facing in ("north", "east", "south", "west"):
        _stump_view(facing).save(os.path.join(OUT, "StorytellerStump_%s.png" % facing))
    print("  StorytellerStump_{north,east,south,west}.png  (128x128)")
    return _stump_view("south")


def _story_shape(c, motif, x, y, sc, col):
    """One story, as a smoke-shape centred on (x, y)."""
    if motif == "Thrumbo":
        c.ellipse(x, y, 22 * sc, 12 * sc, col)
        c.ellipse(x + 22 * sc, y - 5 * sc, 9 * sc, 7 * sc, col)
        c.poly([(x + 26 * sc, y - 10 * sc), (x + 38 * sc, y - 24 * sc), (x + 30 * sc, y - 7 * sc)], col)
        for lx in (-15, -6, 6, 14):
            c.line(x + lx * sc, y + 8 * sc, x + lx * sc, y + 20 * sc, col, 4 * sc)
    elif motif == "Raider":
        c.ellipse(x, y - 16 * sc, 6 * sc, 6 * sc, col)                  # head
        c.ellipse(x, y, 8 * sc, 12 * sc, col)                           # body
        c.line(x - 4 * sc, y + 10 * sc, x - 8 * sc, y + 26 * sc, col, 4 * sc)
        c.line(x + 4 * sc, y + 10 * sc, x + 8 * sc, y + 26 * sc, col, 4 * sc)
        c.line(x - 14 * sc, y - 2 * sc, x + 22 * sc, y - 8 * sc, col, 3 * sc)  # the rifle
    elif motif == "Ship":
        c.rect(x - 7 * sc, y - 24 * sc, x + 7 * sc, y + 14 * sc, col, 3 * sc)
        c.poly([(x - 7 * sc, y - 22 * sc), (x, y - 34 * sc), (x + 7 * sc, y - 22 * sc)], col)
        for side in (-1, 1):
            c.poly([(x + side * 7 * sc, y + 4 * sc), (x + side * 15 * sc, y + 18 * sc),
                    (x + side * 7 * sc, y + 14 * sc)], col)
        c.ellipse(x, y + 22 * sc, 5 * sc, 9 * sc, col)                  # exhaust
    else:  # Mech: a centipede, the thing every colony's stories end up about
        for k in range(5):
            c.ellipse(x - 24 * sc + k * 12 * sc, y + (k % 2) * 3 * sc, 7 * sc, 6 * sc, col)
            c.line(x - 24 * sc + k * 12 * sc, y + 4 * sc, x - 27 * sc + k * 12 * sc,
                   y + 13 * sc, col, 2 * sc)
            c.line(x - 24 * sc + k * 12 * sc, y + 4 * sc, x - 21 * sc + k * 12 * sc,
                   y + 13 * sc, col, 2 * sc)
        c.ellipse(x + 34 * sc, y - 3 * sc, 8 * sc, 7 * sc, col)
        c.circle(x + 37 * sc, y - 5 * sc, 1.8 * sc, (255, 120, 90, int(col[3] * 1.6) if col[3] < 150 else 255))


def storyteller_smoke_frames(total=STORY_FRAMES):
    """Each shape forms low in the smoke, climbs, and thins away, over a
    column of ordinary smoke that keeps rising underneath it."""
    import math
    import random
    for motif in STORY_MOTIFS:
        rng = random.Random(motif)
        wisps = [(rng.uniform(-14, 14), rng.uniform(0, 1), rng.uniform(7, 13)) for _ in range(7)]
        for f in range(total):
            t = f / float(total)
            c = Canvas(128, 192)
            # Plain smoke, always drifting up, wrapping round.
            for wx, phase, r in wisps:
                u = (t + phase) % 1.0
                a = int(70 * math.sin(math.pi * u))
                c.circle(64 + wx + 8 * math.sin(6.28 * u + phase * 6), 176 - 150 * u,
                         r * (0.7 + 0.8 * u), (210, 204, 198, max(0, a)))
            # The story's shape: fades in, peaks a third of the way up, fades out.
            alpha = int(150 * math.sin(math.pi * min(1.0, t * 1.1)))
            y = 130 - 76 * t
            sc = 0.85 + 0.3 * t
            if alpha > 6:
                _story_shape(c, motif, 64, y, sc, (246, 232, 212, alpha))
            write_png(os.path.join(OUT, "StorySmoke%s_%d.png" % (motif, f)), c.w, c.h, c.pixels())
        print("  StorySmoke%s_{0..%d}.png  (128x192)" % (motif, total - 1))


def _build_storyteller():
    made = {"StorytellerStump": storyteller_stump()}
    storyteller_smoke_frames()
    return made


_register("storyteller", _build_storyteller)


# ---------------------------------------------------------------------------
# Board games. The table under them is the jigsaw table's furniture; these are
# the overlays drawn on top by CompBoardGame - one board per game, three
# stages each as the game moves on, and the stacked boxes shown when nobody is
# playing. Every board is a RimWorld-flavoured take on a real game.
# ---------------------------------------------------------------------------

PLAYER_COLS = ((206, 70, 62, 255), (70, 118, 196, 255), (236, 196, 70, 255), (96, 168, 90, 255))


def die(c, x, y, value, size=13, body=(244, 240, 230, 255)):
    silhouette(c, [("rect", x - size / 2.0, y - size / 2.0, x + size / 2.0, y + size / 2.0, 3, body)], 1.6)
    pips = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
            4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
            6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[value]
    q = size * 0.27
    for px, py in pips:
        c.circle(x + px * q, y + py * q, size * 0.09, (40, 34, 30, 255))


def cards(c, x, y, count, back, spread=7):
    for k in range(count):
        cx = x + k * spread
        silhouette(c, [("rect", cx, y, cx + 14, y + 20, 2, back)], 1.4)
        c.frame(cx + 2, y + 2, cx + 12, y + 18, darker(back, 0.75), 1.0, 1)


def board_base(c, x0, y0, x1, y1, fill):
    silhouette(c, [("rect", x0, y0, x1, y1, 5, fill)], 3.0)
    c.frame(x0 + 4, y0 + 4, x1 - 4, y1 - 4, darker(fill, 0.8), 1.4, 3)


def _hex(c, cx, cy, r, color):
    import math
    c.poly([(cx + r * math.cos(math.pi / 6 + k * math.pi / 3),
             cy + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)], color)


def board_colonists(c, stage, rng):
    """Colonists of the Rim: hex tiles, settlements and roads."""
    import math
    board_base(c, 30, 28, 226, 206, (86, 132, 176, 255))           # the sea round it
    terr = [(58, 112, 64), (222, 194, 92), (150, 150, 160), (142, 196, 104), (186, 108, 70)]
    r = 17.5
    rows = (3, 4, 5, 4, 3)
    centres = []
    for j, n in enumerate(rows):
        for i in range(n):
            cx = 128 + (i - (n - 1) / 2.0) * r * math.sqrt(3)
            cy = 117 + (j - 2) * r * 1.5
            centres.append((cx, cy))
    base_rng = __import__("random").Random("colonists-tiles")
    for k, (cx, cy) in enumerate(centres):
        col = terr[base_rng.randrange(len(terr))] if k != 9 else (214, 196, 150)   # ruins in the middle
        _hex(c, cx, cy, r + 0.8, darker(col + (255,), 0.7))
        _hex(c, cx, cy, r - 0.6, col + (255,))
        if k != 9:
            c.circle(cx, cy, 5.2, (240, 230, 200, 255))
            c.circle(cx, cy, 1.6, darker((240, 230, 200, 255), 0.5))
    # Settlements and roads grow with the game.
    verts = []
    for cx, cy in centres:
        for k in range(6):
            a = math.pi / 6 + k * math.pi / 3
            verts.append((round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)))
    verts = sorted(set(verts))
    pick = __import__("random").Random("colonists-build")
    order = pick.sample(verts, 14)
    for k, (vx, vy) in enumerate(order[:4 + stage * 4]):
        col = PLAYER_COLS[k % 4]
        near = min((v for v in verts if v != (vx, vy)), key=lambda v: (v[0] - vx) ** 2 + (v[1] - vy) ** 2)
        c.line(vx, vy, (vx + near[0]) / 2.0, (vy + near[1]) / 2.0, darker(col, 0.6), 4.2)
        c.line(vx, vy, (vx + near[0]) / 2.0, (vy + near[1]) / 2.0, col, 2.6)
        silhouette(c, [("rect", vx - 4, vy - 2, vx + 4, vy + 4, 1, col),
                       ("poly", [(vx - 5, vy - 1.5), (vx, vy - 6.5), (vx + 5, vy - 1.5)], col)], 1.4)
    die(c, 60, 226, rng.randint(1, 6))
    die(c, 78, 228, rng.randint(1, 6))
    cards(c, 150, 216, 3 + stage, (176, 140, 96, 255))


def board_raid(c, stage, rng):
    """Raid!: a world map and armies - including a grey mechanoid one."""
    board_base(c, 26, 30, 230, 196, (74, 112, 150, 255))
    lands = [[(44, 58), (96, 46), (112, 74), (90, 104), (52, 96)],
             [(126, 44), (184, 50), (206, 86), (170, 104), (134, 84)],
             [(58, 118), (104, 112), (118, 156), (84, 182), (50, 160)],
             [(138, 118), (190, 114), (212, 150), (176, 184), (136, 166)],
             [(112, 96), (134, 100), (128, 116), (110, 112)]]
    greens = [(118, 150, 88), (160, 148, 96), (104, 136, 92), (140, 118, 84), (170, 160, 110)]
    for pts, col in zip(lands, greens):
        c.poly(_grow_poly(pts, 1.8), darker(col + (255,), 0.65))
        c.poly(pts, col + (255,))
    armies = PLAYER_COLS[:3] + ((132, 136, 146, 255),)       # the grey one is the mechanoids
    spots = [(78, 72), (100, 86), (160, 70), (186, 90), (80, 142), (96, 166), (164, 140), (184, 164), (122, 106)]
    for k, (sx, sy) in enumerate(spots):
        owner = (k + stage) % 4
        n = 1 + (k * 3 + stage * 2) % 4
        for m in range(n):
            x, y = sx + (m % 2) * 7, sy + (m // 2) * 7
            silhouette(c, [("rect", x - 3, y - 3, x + 3, y + 3, 1, armies[owner])], 1.2)
    for k in range(3):
        die(c, 52 + k * 17, 220, rng.randint(1, 6), body=(214, 72, 62, 255))
    cards(c, 160, 212, 2 + stage, (120, 82, 60, 255))


def board_orbital(c, stage, rng):
    """Orbital Trader: a track of properties round a planet, and silver."""
    x0, y0, x1, y1 = 40, 24, 216, 200
    board_base(c, x0, y0, x1, y1, (226, 230, 214, 255))
    n = 9
    step = (x1 - x0 - 8) / float(n)
    strips = [(160, 96, 60), (120, 180, 220), (206, 90, 150), (230, 150, 60), (206, 64, 58),
              (236, 214, 70), (80, 160, 90), (60, 80, 170)]
    for side in range(4):
        for k in range(n):
            col = strips[(side * 2 + k // 5) % len(strips)] + (255,)
            if side == 0:
                cx0, cy0, cx1, cy1 = x0 + 4 + k * step, y1 - 22, x0 + 4 + (k + 1) * step, y1 - 4
                band = (cx0, cy0, cx1, cy0 + 5)
            elif side == 1:
                cx0, cy0, cx1, cy1 = x0 + 4, y1 - 4 - (k + 1) * step, x0 + 22, y1 - 4 - k * step
                band = (cx1 - 5, cy0, cx1, cy1)
            elif side == 2:
                cx0, cy0, cx1, cy1 = x1 - 4 - (k + 1) * step, y0 + 4, x1 - 4 - k * step, y0 + 22
                band = (cx0, cy1 - 5, cx1, cy1)
            else:
                cx0, cy0, cx1, cy1 = x1 - 22, y0 + 4 + k * step, x1 - 4, y0 + 4 + (k + 1) * step
                band = (cx0, cy0, cx0 + 5, cy1)
            c.frame(cx0, cy0, cx1, cy1, (160, 164, 150, 200), 1.0, 0)
            if 0 < k < n - 1:
                c.rect(band[0], band[1], band[2], band[3], col, 0)
    # The planet in the middle, a ring, and a trade ship on it.
    c.circle(128, 112, 34, (70, 110, 170, 255))
    c.circle(120, 104, 12, (100, 150, 110, 255))
    c.circle(140, 124, 9, (100, 150, 110, 255))
    c.ring(128, 112, 50, 48, (120, 124, 140, 200))
    c.rect(170, 98, 180, 104, (200, 204, 214, 255), 2)
    # Tokens moving round the track, and silver piles by the board.
    for k in range(3):
        pos = (k * 7 + stage * 5) % 32
        side, idx = pos // 8, pos % 8
        if side == 0:
            tx, ty = x0 + 10 + idx * step, y1 - 12
        elif side == 1:
            tx, ty = x0 + 12, y1 - 10 - idx * step
        elif side == 2:
            tx, ty = x1 - 10 - idx * step, y0 + 12
        else:
            tx, ty = x1 - 12, y0 + 10 + idx * step
        silhouette(c, [("circle", tx, ty, 4.2, PLAYER_COLS[k])], 1.4)
    for k, (sx, sy) in enumerate(((52, 222), (150, 224), (200, 220))):
        for m in range(3 + (k + stage) % 3):
            c.circle(sx + m * 2, sy - m * 2.2, 5, darker((200, 204, 214, 255), 0.6))
            c.circle(sx + m * 2, sy - m * 2.2, 4, (206, 210, 220, 255))
    die(c, 104, 226, rng.randint(1, 6))


def board_caravan(c, stage, rng):
    """Caravan Routes: towns, the roads between them, and claimed routes."""
    board_base(c, 26, 26, 230, 200, (214, 196, 150, 255))
    towns = [(52, 52), (104, 44), (170, 56), (208, 90), (64, 108), (128, 96), (186, 136),
             (52, 170), (112, 158), (160, 180), (210, 176)]
    routes = [(0, 1), (1, 2), (2, 3), (0, 4), (1, 5), (4, 5), (5, 3), (5, 6), (3, 6), (4, 7),
              (7, 8), (8, 5), (8, 9), (9, 6), (6, 10), (9, 10), (2, 5)]
    claimed = __import__("random").Random("caravan").sample(range(len(routes)), 12)
    import math
    for k, (a, b) in enumerate(routes):
        (ax, ay), (bx, by) = towns[a], towns[b]
        owner = claimed.index(k) % 4 if k in claimed[:3 + stage * 3] else None
        d = math.hypot(bx - ax, by - ay)
        segs = max(2, int(d // 11))
        for s in range(segs):
            t0, t1 = (s + 0.12) / segs, (s + 0.88) / segs
            x0, y0 = ax + (bx - ax) * t0, ay + (by - ay) * t0
            x1, y1 = ax + (bx - ax) * t1, ay + (by - ay) * t1
            if owner is None:
                c.line(x0, y0, x1, y1, (160, 142, 104, 255), 3.4)
            else:
                c.line(x0, y0, x1, y1, darker(PLAYER_COLS[owner], 0.55), 5.6)
                c.line(x0, y0, x1, y1, PLAYER_COLS[owner], 3.8)
    for tx, ty in towns:
        silhouette(c, [("circle", tx, ty, 5, (120, 84, 56, 255))], 1.6)
        c.circle(tx, ty, 2.2, (236, 220, 180, 255))
    cards(c, 40, 212, 4, (96, 130, 90, 255))
    cards(c, 150, 212, 2 + stage, (150, 96, 70, 255))


def board_muffalo(c, stage, rng):
    """Muffalo & Thrumbo: draughts, brown pieces against white."""
    x0, y0 = 56, 36
    sq = 18
    board_base(c, x0 - 8, y0 - 8, x0 + 8 * sq + 8, y0 + 8 * sq + 8, (110, 78, 50, 255))
    for j in range(8):
        for i in range(8):
            col = (226, 204, 160, 255) if (i + j) % 2 == 0 else (120, 84, 56, 255)
            c.rect(x0 + i * sq, y0 + j * sq, x0 + (i + 1) * sq, y0 + (j + 1) * sq, col, 0)
    rnd = __import__("random").Random("draughts-%d" % stage)
    dark = [(i, j) for j in range(8) for i in range(8) if (i + j) % 2 == 1]
    muff = [cell for cell in dark if cell[1] < 3]
    thr = [cell for cell in dark if cell[1] > 4]
    # Pieces advance and fall as the game goes.
    lost = stage * 2
    muff = rnd.sample(muff, len(muff) - lost)
    thr = rnd.sample(thr, len(thr) - lost)
    if stage:
        mids = [cell for cell in dark if 3 <= cell[1] <= 4]
        muff += rnd.sample(mids, stage)
        thr += rnd.sample([m for m in mids if m not in muff], stage)
    for (i, j), body in [(m, (118, 80, 50, 255)) for m in muff] + [(t, (240, 240, 236, 255)) for t in thr]:
        cx, cy = x0 + (i + 0.5) * sq, y0 + (j + 0.5) * sq
        silhouette(c, [("circle", cx, cy, 6.8, body)], 1.6)
        c.ring(cx, cy, 5.2, 4.2, darker(body, 0.78))
    # Captured pieces at the side.
    for k in range(lost):
        c.circle(30, 60 + k * 12, 6, (118, 80, 50, 255))
        c.circle(226, 180 - k * 12, 6, (240, 240, 236, 255))


BOARD_GAMES = (("Colonists", board_colonists), ("Raid", board_raid), ("Orbital", board_orbital),
               ("Caravan", board_caravan), ("Muffalo", board_muffalo))


def board_game_frames(stages=3):
    import random
    for name, drawer in BOARD_GAMES:
        for stage in range(stages):
            c = Canvas(256, 256)
            drawer(c, stage, random.Random("%s-%d" % (name, stage)))
            c.save(os.path.join(OUT, "Board%s_%d.png" % (name, stage)))
        print("  Board%s_{0..%d}.png  (256x256)" % (name, stages - 1))


def board_games_idle():
    """The boxes, stacked at one end while nobody is playing."""
    c = Canvas(256, 256)
    lids = ((70, 118, 196, 255), (206, 70, 62, 255), (86, 132, 90, 255))
    for k, lid in enumerate(lids):
        x, y = 150 - k * 6, 176 - k * 16
        silhouette(c, [("rect", x, y, x + 70, y + 44, 3, lid)], 2.6)
        c.rect(x + 8, y + 8, x + 40, y + 34, darker(lid, 0.75), 2)
        c.rect(x + 46, y + 10, x + 62, y + 14, (240, 232, 214, 255), 1)
        c.rect(x + 46, y + 20, x + 58, y + 24, (240, 232, 214, 255), 1)
    # A folded board leaning against them.
    silhouette(c, [("rect", 40, 150, 120, 210, 3, (86, 132, 176, 255))], 2.6)
    c.line(80, 152, 80, 208, darker((86, 132, 176, 255), 0.7), 1.6)
    save_single(c, "BoardGamesIdle")
    return c


# Seed Pits: mancala on a carved board, for a tribe's first evenings.

def seed_pit_board():
    c = Canvas(128, 128)
    wood = (232, 224, 210, 255)                                   # pale: stuff tints it
    silhouette(c, [("rect", 8, 36, 120, 92, 22, wood)], 4.0)
    for i in range(6):
        for j in range(2):
            c.circle(28 + i * 14.4, 54 + j * 20, 6.4, darker(wood, 0.72))
            c.circle(28 + i * 14.4, 55 + j * 20, 5.4, darker(wood, 0.8))
    for x in (15, 113):
        c.ellipse(x, 64, 6, 16, darker(wood, 0.72))
    save_single(c, "SeedPitBoard")
    return c


def seed_pit_frames(stages=3):
    import random
    seeds = ((200, 64, 52, 255), (246, 232, 170, 255), (110, 170, 80, 255), (240, 150, 60, 255))
    for stage in range(stages):
        c = Canvas(128, 128)
        rng = random.Random("seedpits-%d" % stage)
        counts = [4] * 12 if stage == 0 else [rng.randint(0, 7) for _ in range(12)]
        stores = (0, 0) if stage == 0 else (rng.randint(3, 8) + stage * 2, rng.randint(3, 8) + stage)
        for k, n in enumerate(counts):
            i, j = k % 6, k // 6
            px, py = 28 + i * 14.4, 55 + j * 20
            for m in range(n):
                a = m * 2.4 + k
                col = seeds[(m + k) % len(seeds)]
                sx, sy = px + math.cos(a) * (1.2 + m * 0.45), py + math.sin(a) * (1.2 + m * 0.4)
                c.ellipse(sx, sy, 2.9, 2.2, darker(col, 0.6))
                c.ellipse(sx - 0.3, sy - 0.3, 2.3, 1.7, col)
        for (x, n) in ((15, stores[0]), (113, stores[1])):
            for m in range(n):
                c.ellipse(x + (m % 2) * 3.4 - 1.7, 54 + m * 2.2, 2.9, 2.2, darker(seeds[m % len(seeds)], 0.6))
                c.ellipse(x + (m % 2) * 3.4 - 2.0, 53.7 + m * 2.2, 2.3, 1.7, seeds[m % len(seeds)])
        c.save(os.path.join(OUT, "SeedPits_%d.png" % stage))
    print("  SeedPits_{0..%d}.png  (128x128)" % (stages - 1))


def _build_boardgames():
    made = {"BoardGamesIdle": board_games_idle(), "SeedPitBoard": seed_pit_board()}
    board_game_frames()
    seed_pit_frames()
    return made


_register("boardgames", _build_boardgames)


# ---------------------------------------------------------------------------
# Rally games: table tennis (2x3, unpowered) and air hockey (1x2, powered).
# The ball, puck and mallets are separate sprites CompRallyGame moves about.
# ---------------------------------------------------------------------------

def table_tennis_table():
    c = Canvas(256, 384)
    top = (46, 104, 88, 255)
    silhouette(c, [("rect", 18, 16, 238, 368, 6, top)], 5.0)
    c.frame(26, 24, 230, 360, (240, 240, 236, 255), 3.0, 2)        # edge lines
    c.line(128, 26, 128, 358, (240, 240, 236, 200), 1.6)           # centre line
    # The net, across the middle, with its posts.
    c.rect(12, 187, 244, 197, darker(top, 0.55), 2)
    c.rect(14, 189, 242, 195, (232, 232, 226, 255), 1)
    for x in (10, 246):
        c.circle(x, 192, 6, DARK)
        c.circle(x, 192, 4.2, (170, 170, 176, 255))
    save_table_views(c, "TableTennisTable", 46, (48, 58, 56, 255), (150, 156, 164, 255),
                     (0.16, 0.84), (0.12, 0.39, 0.61, 0.88), _tt_net)
    return c


def _tt_net(c, facing, drop, rw, rh):
    """The net stands up: facing north or south its face shows as a band
    rising from its line; side-on only its posts stand proud."""
    if facing in ("north", "south"):
        y = drop + rh / 2.0
        c.rect(drop + 8, y - 14, drop + rw - 8, y, (236, 236, 240, 150), 1)
        for x in range(int(drop + 12), int(drop + rw - 10), 5):
            c.line(x, y - 14, x, y, (200, 200, 210, 160), 0.8)
        c.rect(drop + 8, y - 15, drop + rw - 8, y - 12, (250, 250, 252, 255), 1)
        for x in (drop + 6, drop + rw - 6):
            c.rect(x - 3, y - 16, x + 3, y + 2, (60, 60, 66, 255), 1)
    else:
        x = drop + rw / 2.0
        c.rect(x - 3, drop + 4, x + 3, drop + 30, (60, 60, 66, 255), 1)
        c.rect(x - 3, drop + rh - 20, x + 3, drop + rh + 2, (60, 60, 66, 255), 1)


def _ah_lights(c, facing, drop, rw, rh):
    if facing in ("east", "west"):
        for k in range(6):
            c.circle(drop + rw / 2.0 - 32 + k * 13, drop + rh + 8, 3,
                     (240, 90, 80, 255) if k < 3 else (90, 160, 240, 255))


def air_hockey_table():
    c = Canvas(128, 256)
    rail, surface = (44, 60, 120, 255), (226, 236, 244, 255)
    silhouette(c, [("rect", 8, 8, 120, 248, 12, rail)], 5.0)
    c.rect(16, 16, 112, 240, surface, 8)
    for y in range(24, 236, 8):                                     # air holes
        for x in range(22, 110, 8):
            c.circle(x, y, 0.9, darker(surface, 0.82))
    c.line(18, 128, 110, 128, (206, 70, 62, 200), 2.0)
    c.ring(64, 128, 20, 18.4, (206, 70, 62, 200))
    for y, col in ((16, (60, 110, 190, 220)), (240, (206, 70, 62, 220))):
        c.ring(64, y, 22, 20.4, col)
        c.rect(44, y - 3 if y > 128 else y - 1, 84, y + 1 if y > 128 else y + 3, DARK, 1)   # goal slot
    c.rect(52, 244, 76, 250, (236, 196, 70, 255), 2)                # scoreboard light
    save_table_views(c, "AirHockeyTable", 46, (40, 52, 110, 255), (120, 126, 140, 255),
                     (0.16, 0.84), (0.08, 0.5, 0.92), _ah_lights)
    return c


def rally_sprites():
    c = Canvas(32, 32)
    c.circle(16, 16, 12, DARK)
    c.circle(16, 16, 10, (250, 248, 240, 255))
    c.circle(13, 13, 3.5, (255, 255, 255, 255))
    save_single(c, "TableTennisBall")
    c = Canvas(48, 48)
    c.circle(24, 24, 20, DARK)
    c.circle(24, 24, 18, (214, 60, 52, 255))
    c.ring(24, 24, 13, 11, darker((214, 60, 52, 255), 0.7))
    save_single(c, "AirHockeyPuck")
    c = Canvas(48, 48)                                              # white: tinted per end
    c.circle(24, 24, 20, (60, 60, 64, 255))
    c.circle(24, 24, 18, (255, 255, 255, 255))
    c.circle(24, 24, 9, (60, 60, 64, 255))
    c.circle(24, 24, 7.5, (236, 236, 236, 255))
    save_single(c, "AirHockeyMallet")


def _build_rally():
    made = {"TableTennisTable": table_tennis_table(), "AirHockeyTable": air_hockey_table()}
    rally_sprites()
    return made


_register("rally", _build_rally)


# ---------------------------------------------------------------------------
# Lawn noughts and crosses: a rope grid pegged out on the grass. The ground
# shows through - there is nothing here but rope and pegs.
# ---------------------------------------------------------------------------

def lawn_grid():
    c = Canvas(384, 384)
    rope, rope_dk = (238, 232, 214, 255), (150, 138, 110, 255)
    peg, peg_dk = (150, 108, 66, 255), (96, 66, 40, 255)
    for k in (1, 2):
        v = k * 128
        for (x0, y0, x1, y1) in ((v, 14, v, 370), (14, v, 370, v)):
            c.line(x0, y0, x1, y1, rope_dk, 7)
            c.line(x0, y0, x1, y1, rope, 4.2)
    for k in (1, 2):
        v = k * 128
        for (x, y) in ((v, 10), (v, 374), (10, v), (374, v)):
            silhouette(c, [("circle", x, y, 8, peg)], 3.0)
            c.circle(x - 2, y - 2, 3, darker(peg, 1.2) if False else (178, 132, 86, 255))
    save_single(c, "LawnNoughtsGrid")
    return c


_register("lawngrid", lambda: {"LawnNoughtsGrid": lawn_grid()})


# ---------------------------------------------------------------------------
# Giant four-in-a-row. Drawn the way a television is: the face when it faces
# south, the back from the north, and a slim edge-on profile from the sides,
# because from above an upright frame is only a strip. The discs are an
# overlay, shown face-on only.
# ---------------------------------------------------------------------------

FOUR_COLS, FOUR_ROWS = 7, 6
FOUR_X0, FOUR_Y0, FOUR_CELL = 37, 12, 26
FOUR_H = 192     # 1.5 tiles tall: an upright face needs more than its footprint, as a TV does


def _four_face(c, back=False):
    frame = (48, 92, 176, 255) if not back else (38, 74, 146, 255)
    pieces = [("rect", FOUR_X0 - 10, FOUR_Y0 - 6, FOUR_X0 + FOUR_COLS * FOUR_CELL + 10,
               FOUR_Y0 + FOUR_ROWS * FOUR_CELL + 6, 6, frame),
              ("rect", FOUR_X0 - 26, 176, FOUR_X0 + 12, 186, 3, (120, 88, 56, 255)),     # feet
              ("rect", FOUR_X0 + FOUR_COLS * FOUR_CELL - 12, 176,
               FOUR_X0 + FOUR_COLS * FOUR_CELL + 26, 186, 3, (120, 88, 56, 255))]
    silhouette(c, pieces, 4.0)
    for j in range(FOUR_ROWS):
        for i in range(FOUR_COLS):
            x = FOUR_X0 + (i + 0.5) * FOUR_CELL
            y = FOUR_Y0 + (j + 0.5) * FOUR_CELL
            c.circle(x, y, 11, darker(frame, 0.6))
            c.circle(x, y, 9.5, (28, 30, 40, 255))
    if back:
        c.rect(FOUR_X0 - 6, FOUR_Y0 + 4, FOUR_X0 + FOUR_COLS * FOUR_CELL + 6, FOUR_Y0 + 10,
               darker(frame, 0.8), 1)


def four_in_a_row():
    south = Canvas(256, FOUR_H)
    _four_face(south)
    south.save(os.path.join(OUT, "FourInARow_south.png"))
    north = Canvas(256, FOUR_H)
    _four_face(north, back=True)
    north.save(os.path.join(OUT, "FourInARow_north.png"))
    # Edge on: the frame is a strip across its two tiles, feet out either side.
    # East and west get the draw size turned round (1.5 x 2), so the canvas is too.
    for name in ("east", "west"):
        c = Canvas(FOUR_H, 256)
        m = FOUR_H // 2
        silhouette(c, [("rect", m - 8, 20, m + 8, 236, 3, (48, 92, 176, 255)),
                       ("rect", m - 28, 22, m + 28, 32, 3, (120, 88, 56, 255)),
                       ("rect", m - 28, 224, m + 28, 234, 3, (120, 88, 56, 255))], 4.0)
        c.line(m, 24, m, 232, darker((48, 92, 176, 255), 0.7), 1.6)
        c.save(os.path.join(OUT, "FourInARow_%s.png" % name))
    print("  FourInARow_{north,east,south,west}.png")
    return south


def four_in_a_row_frames(total=16):
    """Discs dropping in turn, a line of four lit up, then the frame emptied."""
    import random
    rng = random.Random("four")
    heights = [0] * FOUR_COLS
    moves = []
    for k in range(13):
        col = rng.choice([i for i in range(FOUR_COLS) if heights[i] < FOUR_ROWS])
        moves.append((col, heights[col], k % 2))
        heights[col] += 1
    colours = ((214, 64, 54, 255), (238, 200, 60, 255))
    for f in range(total):
        c = Canvas(256, FOUR_H)
        shown = min(f + 1, len(moves))
        for (i, h, who) in moves[:shown]:
            x = FOUR_X0 + (i + 0.5) * FOUR_CELL
            y = FOUR_Y0 + (FOUR_ROWS - 0.5 - h) * FOUR_CELL
            c.circle(x, y, 9.5, darker(colours[who], 0.7))
            c.circle(x - 1, y - 1, 8, colours[who])
        if f >= len(moves):
            # The winning line, glowing.
            for (i, h, who) in moves[len(moves) - 7:len(moves):2]:
                x = FOUR_X0 + (i + 0.5) * FOUR_CELL
                y = FOUR_Y0 + (FOUR_ROWS - 0.5 - h) * FOUR_CELL
                c.ring(x, y, 12.5, 10.5, (255, 250, 210, 200 if f % 2 == 0 else 90))
        c.save(os.path.join(OUT, "FourInARowDiscs_%d.png" % f))
    print("  FourInARowDiscs_{0..%d}.png  (256x%d)" % (total - 1, FOUR_H))


def _build_four():
    made = {"FourInARow": four_in_a_row()}
    four_in_a_row_frames()
    return made


_register("fourinarow", _build_four)


# ---------------------------------------------------------------------------
# Tangle mat: four columns of coloured spots, and a spinner in the corner. The
# arrow is an overlay that spins while anyone is playing.
# ---------------------------------------------------------------------------

TANGLE_SPOTS = ((214, 64, 54, 255), (60, 110, 200, 255), (238, 200, 60, 255), (80, 170, 84, 255))
TANGLE_SPIN = (330, 326)


def tangle_mat():
    c = Canvas(384, 384)
    mat = (246, 244, 238, 255)
    silhouette(c, [("rect", 14, 14, 370, 290, 8, mat)], 4.0)
    for i, col in enumerate(TANGLE_SPOTS):
        for j in range(4):
            x = 62 + i * 87
            y = 50 + j * 66
            c.circle(x, y, 25, darker(col, 0.72))
            c.circle(x, y, 23, col)
    # The spinner card, set down beside the mat.
    silhouette(c, [("rect", TANGLE_SPIN[0] - 44, TANGLE_SPIN[1] - 40, TANGLE_SPIN[0] + 44,
                    TANGLE_SPIN[1] + 40, 5, mat)], 3.0)
    for k, col in enumerate(TANGLE_SPOTS):
        c.wedge(TANGLE_SPIN[0], TANGLE_SPIN[1], 32, 0, k * 90, (k + 1) * 90, col)
    c.circle(TANGLE_SPIN[0], TANGLE_SPIN[1], 3.5, DARK)
    save_single(c, "TangleMat")
    return c


def tangle_spinner_frames(total=8):
    for f in range(total):
        c = Canvas(384, 384)
        a = math.radians(f * 360.0 / total * 2.6 + 20)
        x, y = TANGLE_SPIN
        tip = (x + math.cos(a) * 30, y + math.sin(a) * 30)
        tail = (x - math.cos(a) * 12, y - math.sin(a) * 12)
        c.line(tail[0], tail[1], tip[0], tip[1], DARK, 6)
        c.line(tail[0], tail[1], tip[0], tip[1], (250, 250, 250, 255), 3.4)
        c.circle(x, y, 4.5, DARK)
        c.save(os.path.join(OUT, "TangleSpinner_%d.png" % f))
    print("  TangleSpinner_{0..%d}.png  (384x384)" % (total - 1))


def _build_tangle():
    made = {"TangleMat": tangle_mat()}
    tangle_spinner_frames()
    return made


_register("tangle", _build_tangle)

if __name__ == "__main__":
    main()
