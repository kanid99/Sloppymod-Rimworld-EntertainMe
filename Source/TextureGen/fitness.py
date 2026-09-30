"""The fitness equipment: trampoline, punching bag, weight bench, exercise
bike and bouldering wall.

Unlike the rest of the generator these are modelled in 3D - boxes, cylinders
and slabs - and drawn from RimWorld's own camera, which looks down from the
south: every view, north and south included, shows the tops of things and
the faces turned toward the viewer, and all four facings come from the one
model, so they cannot disagree. A small z-buffered rasteriser draws them in
the mod's style: flat-shaded faces, a soft tint where two faces meet, and one
bold dark line round the whole silhouette.

The trampoline is the exception: it was approved as a flat drawing and is
drawn that way.

Canvases are square, since a Graphic_Multi turns its draw size round for
east and west. Each model's footprint centre sits at ORIGIN on its canvas;
the defs carry the matching drawSize and drawOffset.

Needs numpy and Pillow, unlike the rest of the generator.
"""

import math
import os

import numpy as np
from PIL import Image

from pnglib import Canvas

S = 128                          # px per tile
VIEW = (0.0, -0.6, 0.8)          # toward the camera: from the south, above
UP = (0.0, 0.8, 0.6)             # screen up: depth keeps 0.8, height 0.6
LIGHT = (-0.35, -0.45, 0.82)
SS = 4                           # supersampling
DARK_RGB = (26, 22, 20)
OUTLINE_PX = 3.0

FACINGS = ("north", "east", "south", "west")

STEEL = (158, 164, 174, 255)
STEEL_DK = (100, 106, 118, 255)
PAD = (54, 54, 60, 255)
RED = (178, 52, 44, 255)
PLATE = (46, 46, 52, 255)
PLY = (214, 178, 128, 255)
WOOD = (150, 108, 70, 255)
MATC = (66, 112, 172, 255)
CHAIN = (40, 38, 36, 255)
HOLDS = [(255, 196, 40, 255), (220, 70, 60, 255), (70, 170, 90, 255),
         (80, 140, 230, 255), (200, 90, 200, 255)]


# --------------------------------------------------------------------------- vectors
def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    length = math.sqrt(_dot(a, a)) or 1.0
    return _mul(a, 1.0 / length)


def _shade(color, n):
    lam = max(0.0, _dot(n, _norm(LIGHT)))
    if lam > 0.55:
        k = 0.18 * (lam - 0.55)
        return tuple(int(c + (255 - c) * k) for c in color[:3])
    k = 0.62 + 0.4 * lam
    return tuple(int(c * k) for c in color[:3])


# --------------------------------------------------------------------------- solids
class Solid:
    def __init__(self, faces, color):
        self.faces = faces
        self.color = color


def box(x0, x1, y0, y1, z0, z1, color):
    p = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    idx = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
    return Solid([[p[i] for i in f] for f in idx], color)


def hexa(pts, color):
    """Eight corners: bottom quad 0-3, then the top quad 4-7 in the same order."""
    idx = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return Solid([[pts[i] for i in f] for f in idx], color)


def rod(a, b, half, color):
    """A square bar from a to b."""
    axis = _norm(_sub(b, a))
    t = (0, 0, 1) if abs(axis[2]) < 0.9 else (1, 0, 0)
    u = _mul(_norm(_cross(axis, t)), half)
    v = _mul(_norm(_cross(axis, u)), half)
    c = [_add(_add(p, du), dv) for p in (a, b) for du, dv in ((u, v), (_mul(u, -1), v), (_mul(u, -1), _mul(v, -1)), (u, _mul(v, -1)))]
    return hexa([c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7]], color)


def cyl(c0, c1, r, color, sides=20, r1=None, level_caps=None):
    """A cylinder or frustum between two centres. Caps are square to the axis,
    unless the axis is near vertical (or level_caps is set), when they stay
    level - a hanging bag keeps a flat top and foot as it swings."""
    axis = _sub(c1, c0)
    a = _norm(axis)
    if level_caps is None:
        level_caps = abs(a[2]) > 0.7
    if level_caps:
        u, v = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    else:
        t = (0, 0, 1) if abs(a[2]) < 0.9 else (1, 0, 0)
        u = _norm(_cross(a, t))
        v = _cross(a, u)
    r1 = r if r1 is None else r1
    ring0, ring1 = [], []
    for i in range(sides):
        ang = 2 * math.pi * i / sides
        du, dv = math.cos(ang), math.sin(ang)
        ring0.append(_add(c0, _add(_mul(u, r * du), _mul(v, r * dv))))
        ring1.append(_add(c1, _add(_mul(u, r1 * du), _mul(v, r1 * dv))))
    faces = [ring0[::-1], ring1]
    for i in range(sides):
        j = (i + 1) % sides
        faces.append([ring0[i], ring0[j], ring1[j], ring1[i]])
    return Solid(faces, color)


def turn(p, facing):
    """A model built facing south, turned to face another way."""
    x, y, z = p
    if facing == "east":
        return (-y, x, z)
    if facing == "north":
        return (-x, -y, z)
    if facing == "west":
        return (y, -x, z)
    return (x, y, z)


# --------------------------------------------------------------------------- rendering
def _faces(solids, facing):
    out = []
    for s in solids:
        pts_all = [turn(p, facing) for f in s.faces for p in f]
        centre = _mul(tuple(sum(c) for c in zip(*pts_all)), 1.0 / len(pts_all))
        for f in s.faces:
            pts = [turn(p, facing) for p in f]
            n = (0.0, 0.0, 0.0)
            for i in range(len(pts)):                     # Newell's normal
                a, b = pts[i], pts[(i + 1) % len(pts)]
                n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
            n = _norm(n)
            fc = _mul(tuple(sum(c) for c in zip(*pts)), 1.0 / len(pts))
            if _dot(n, _sub(fc, centre)) < 0:
                n = _mul(n, -1)
            if _dot(n, VIEW) <= 1e-4:
                continue
            out.append((pts, _shade(s.color, n)))
    return out


def render(solids, facing, size, origin, outline=True):
    """Draw solids (modelled facing south) turned to `facing`, on a canvas of
    `size` px with the model origin at pixel `origin`."""
    w, h = size
    ox, oy = origin
    W, H = w * SS, h * SS
    col = np.zeros((H, W, 3), np.float32)
    zb = np.full((H, W), -1e9, np.float32)
    fid = np.full((H, W), -1, np.int32)
    for k, (pts, rgb) in enumerate(_faces(solids, facing)):
        p2 = np.array([((ox + p[0] * S) * SS, (oy - (UP[1] * p[1] + UP[2] * p[2]) * S) * SS) for p in pts], np.float32)
        dz = np.array([_dot(p, VIEW) for p in pts], np.float32)
        for t in range(1, len(p2) - 1):
            tri = np.array([p2[0], p2[t], p2[t + 1]])
            tz = np.array([dz[0], dz[t], dz[t + 1]])
            x0 = max(int(np.floor(tri[:, 0].min())), 0)
            x1 = min(int(np.ceil(tri[:, 0].max())) + 1, W)
            y0 = max(int(np.floor(tri[:, 1].min())), 0)
            y1 = min(int(np.ceil(tri[:, 1].max())) + 1, H)
            if x0 >= x1 or y0 >= y1:
                continue
            ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
            (ax, ay), (bx, by), (cx, cy) = tri
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-6:
                continue
            w0 = ((by - cy) * (xs - cx) + (cx - bx) * (ys - cy)) / den
            w1 = ((cy - ay) * (xs - cx) + (ax - cx) * (ys - cy)) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
            z = w0 * tz[0] + w1 * tz[1] + w2 * tz[2]
            sub = zb[y0:y1, x0:x1]
            win = inside & (z > sub + 1e-5)
            sub[win] = z[win]
            col[y0:y1, x0:x1][win] = rgb
            fid[y0:y1, x0:x1][win] = k
    mask = fid >= 0
    # a soft tint where the visible face changes
    edge = np.zeros_like(mask)
    for dy, dx in ((0, 1), (1, 0)):
        a = fid[:H - dy, :W - dx]
        b = fid[dy:, dx:]
        edge[:H - dy, :W - dx] |= (a != b) & (a >= 0) & (b >= 0)
    edge = edge | np.roll(edge, 1, 0) | np.roll(edge, 1, 1)
    col[edge & mask] *= 0.8
    rgba = np.zeros((H, W, 4), np.float32)
    if outline:
        r = int(round(OUTLINE_PX * SS))
        grown = mask.copy()
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if (dy or dx) and dy * dy + dx * dx <= r * r:
                    grown |= np.roll(np.roll(mask, dy, 0), dx, 1)
        rgba[grown, :3] = DARK_RGB
        rgba[grown, 3] = 255
    rgba[mask, :3] = col[mask]
    rgba[mask, 3] = 255
    pm = rgba.copy()
    pm[..., :3] *= pm[..., 3:4] / 255.0
    pm = pm.reshape(h, SS, w, SS, 4).mean(axis=(1, 3))
    a = pm[..., 3:4]
    rgb = np.where(a > 0, pm[..., :3] * 255.0 / np.maximum(a, 1e-6), 0)
    return Image.fromarray(np.concatenate([rgb, a], axis=2).clip(0, 255).astype(np.uint8), "RGBA")


def _save(img, out, name):
    img.save(os.path.join(out, name + ".png"))


def _facing_suffix(f):
    return f.capitalize()


# --------------------------------------------------------------------------- 1. trampoline
TRAMP_W = 384                      # 3x3 at 128 px
T_CX, T_CY = 192, 176              # the rim's centre, lifted so the near legs show
T_RX, T_RY = 172, 140
T_PAD = 30
T_STEEL = (150, 156, 166, 255)
T_PADC = (58, 118, 196, 255)
T_MAT = (34, 34, 40, 255)
T_DARK = (26, 22, 20, 255)
# One bounce is 8 frames of 8 ticks; the job lifts the pawn off the same clock,
# so the mat dips exactly as they land. Keep these in step with the def and
# JobDriver_Exercise.
TRAMP_FRAMES = 8
TRAMP_SAG = (1.0, 0.55, 0.15, 0.0, 0.0, 0.0, 0.1, 0.35)


def _t_darker(c, f):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f), c[3])


def _t_lighter(c, a):
    return (int(c[0] + (255 - c[0]) * a), int(c[1] + (255 - c[1]) * a), int(c[2] + (255 - c[2]) * a), c[3])


def trampoline(sag=0.0):
    c = Canvas(TRAMP_W, TRAMP_W)
    CX, CY, RX, RY, PAD = T_CX, T_CY, T_RX, T_RY, T_PAD
    c.ellipse(CX, CY + 40, RX + 6, RY + 4, (0, 0, 0, 60))                   # shadow on the ground
    for a in (35, 145):                                                     # the near legs, under the rim
        x = CX + math.cos(math.radians(a)) * RX * 0.92
        y = CY + math.sin(math.radians(a)) * RY * 0.92
        for x0, x1 in ((x - 14, x - 18), (x + 14, x + 18)):
            c.line(x0, y, x1, y + 44, T_DARK, 7)
            c.line(x0, y, x1, y + 44, T_STEEL, 3.5)
        c.line(x - 17, y + 40, x + 17, y + 40, T_DARK, 6)
        c.line(x - 17, y + 40, x + 17, y + 40, T_STEEL, 3)
    c.ellipse(CX, CY + 8, RX + 4, RY + 4, T_DARK)                           # the rim's side
    c.ellipse(CX, CY + 8, RX, RY, _t_darker(T_PADC, 0.72))
    c.ellipse(CX, CY, RX + 4, RY + 4, T_DARK)                               # its padded top
    c.ellipse(CX, CY, RX, RY, T_PADC)
    for i in range(16):                                                     # pad seams
        a = math.radians(i * 22.5)
        c.line(CX + math.cos(a) * (RX - PAD + 3), CY + math.sin(a) * (RY - PAD * 0.8 + 3),
               CX + math.cos(a) * (RX - 3), CY + math.sin(a) * (RY - 3), _t_darker(T_PADC, 0.8), 1.6)
    c.ellipse(CX, CY - 6, RX - 12, RY - 14, _t_lighter(T_PADC, 0.12))
    c.ellipse(CX, CY, RX - 10, RY - 10, T_PADC)
    mrx, mry = RX - PAD, RY - PAD * 0.8
    c.ellipse(CX, CY, mrx + 3, mry + 3, T_DARK)                             # the mat
    c.ellipse(CX, CY, mrx, mry, T_MAT)
    for k in range(6):                                                      # dipping toward the middle
        f = 1 - k / 6.0
        c.ellipse(CX, CY + sag * 10 * (1 - f), mrx * f, mry * f, (0, 0, 0, int(22 + 40 * sag)))
    c.ellipse(CX - 34, CY - 48 + sag * 6, mrx * 0.38, mry * 0.12, (255, 255, 255, int(12 * (1 - sag))))
    for r, colr in ((30, (210, 70, 60, 200)), (24, T_MAT), (10, (210, 70, 60, 200))):
        c.ellipse(CX, CY + sag * 10, r, r * mry / mrx, colr)
    return c


def build_trampoline(out):
    trampoline(0.0).save(os.path.join(out, "Trampoline.png"))
    for i, sag in enumerate(TRAMP_SAG):
        trampoline(sag).save(os.path.join(out, "TrampolineBounce_%d.png" % i))
    print("  Trampoline.png + TrampolineBounce_0..%d  (%dx%d)" % (TRAMP_FRAMES - 1, TRAMP_W, TRAMP_W))


# --------------------------------------------------------------------------- 2. punching bag
BAG_CANVAS, BAG_ORIGIN = (256, 256), (128, 200)
BAG_PIVOT = (0.0, 0.04, 1.85)      # the arm's tip, in the stand's (south-facing) frame
BAG_LEN = 1.49                     # pivot to the bag's foot
BAG_STEP = 0.08                    # sprite grid step at the foot, in tiles
BAG_GRID = 3                       # -3..3 each way: 49 sprites
BAG_SPRITE, BAG_SPRITE_PIVOT = (160, 224), (80, 32)


def bag_stand(post_only=False):
    post = box(-0.06, 0.06, 0.3, 0.42, 0.1, 1.95, STEEL)
    if post_only:
        return [post]
    return [box(-0.42, 0.42, -0.2, 0.45, 0.0, 0.1, STEEL_DK), post,
            box(-0.05, 0.05, -0.02, 0.42, 1.85, 1.95, STEEL),
            rod((0.0, 0.38, 1.45), (0.0, 0.14, 1.85), 0.03, STEEL)]


def bag(dx, dy):
    """The bag and its chain, hanging from the origin with the foot displaced
    (dx, dy) tiles in world directions."""
    foot = (dx, dy, -math.sqrt(max(BAG_LEN ** 2 - dx * dx - dy * dy, 0.5)))
    top = _mul(foot, 0.23 / BAG_LEN)
    return [cyl((0.0, 0.0, 0.0), top, 0.015, CHAIN, 6), cyl(foot, top, 0.2, RED)]


def build_punching_bag(out):
    for f in FACINGS:
        _save(render(bag_stand(), f, BAG_CANVAS, BAG_ORIGIN), out, "PunchingBagStand_" + f)
    # Facing north the post stands between the camera and the bag.
    _save(render(bag_stand(post_only=True), "north", BAG_CANVAS, BAG_ORIGIN), out, "PunchingBagPostNorth")
    n = 0
    for i in range(-BAG_GRID, BAG_GRID + 1):
        for j in range(-BAG_GRID, BAG_GRID + 1):
            img = render(bag(i * BAG_STEP, j * BAG_STEP), "south", BAG_SPRITE, BAG_SPRITE_PIVOT)
            _save(img, out, "PunchingBag_%d_%d" % (i + BAG_GRID, j + BAG_GRID))
            n += 1
    print("  PunchingBagStand_{north,east,south,west}, PunchingBagPostNorth, %d bag sprites" % n)


# --------------------------------------------------------------------------- 3. weight bench
BENCH_CANVAS, BENCH_ORIGIN = (320, 320), (160, 200)
BENCH_FRAMES = 8
BENCH_LIFT = (0.0, 0.3, 0.7, 1.0, 1.0, 0.7, 0.3, 0.0)


def bench_frame():
    s = [box(-0.14, 0.14, -0.75, -0.62, 0.0, 0.36, STEEL_DK),
         box(-0.14, 0.14, 0.55, 0.68, 0.0, 0.36, STEEL_DK),
         box(-0.2, 0.2, -0.88, 0.78, 0.36, 0.5, PAD)]
    for sx in (-1, 1):
        s.append(box(sx * 0.46 - 0.04, sx * 0.46 + 0.04, 0.62, 0.72, 0.0, 1.02, STEEL))
        s.append(box(sx * 0.46 - 0.1, sx * 0.46 + 0.1, 0.5, 0.86, 0.0, 0.05, STEEL_DK))
    return s


def barbell(lift):
    z = 1.0 + lift * 0.35
    s = [cyl((-0.86, 0.66, z), (0.86, 0.66, z), 0.025, STEEL, 8)]
    for sx in (-1, 1):
        s.append(cyl((sx * 0.6, 0.66, z), (sx * 0.66, 0.66, z), 0.22, PLATE))
        s.append(cyl((sx * 0.67, 0.66, z), (sx * 0.72, 0.66, z), 0.17, PLATE))
        s.append(cyl((sx * 0.54, 0.66, z), (sx * 0.59, 0.66, z), 0.04, STEEL_DK, 8))
    return s


def build_weight_bench(out):
    for f in FACINGS:
        suffix = _facing_suffix(f)
        _save(render(bench_frame(), f, BENCH_CANVAS, BENCH_ORIGIN), out, "WeightBench_" + f)
        # The bar is its own overlay, drawn over the colonist lying under it.
        _save(render(barbell(0.0), f, BENCH_CANVAS, BENCH_ORIGIN), out, "WeightBenchBarRacked%s_0" % suffix)
        for i, lift in enumerate(BENCH_LIFT):
            _save(render(barbell(lift), f, BENCH_CANVAS, BENCH_ORIGIN), out, "WeightBenchBar%s_%d" % (suffix, i))
    print("  WeightBench_{north,east,south,west} + bar frames per facing")


# --------------------------------------------------------------------------- 4. exercise bike
BIKE_CANVAS, BIKE_ORIGIN = (256, 256), (128, 170)
BIKE_FRAMES = 8


def exercise_bike(phase=0.0):
    s = [box(-0.3, 0.3, -0.42, -0.34, 0.0, 0.06, STEEL_DK),
         box(-0.28, 0.28, 0.34, 0.42, 0.0, 0.06, STEEL_DK),
         box(-0.04, 0.04, -0.38, 0.38, 0.02, 0.12, STEEL_DK),
         cyl((-0.05, -0.2, 0.34), (0.05, -0.2, 0.34), 0.25, (70, 74, 84, 255)),
         cyl((-0.056, -0.2, 0.34), (0.056, -0.2, 0.34), 0.205, (96, 102, 114, 255)),
         cyl((-0.075, -0.2, 0.34), (0.075, -0.2, 0.34), 0.05, STEEL, 12),
         rod((0.0, 0.23, 0.1), (0.0, 0.11, 0.78), 0.03, STEEL),
         box(-0.1, 0.1, 0.0, 0.24, 0.78, 0.85, PAD),
         rod((0.0, -0.11, 0.3), (0.0, -0.27, 0.98), 0.03, STEEL),
         box(-0.26, 0.26, -0.34, -0.27, 0.97, 1.03, PAD),
         box(-0.07, 0.07, -0.32, -0.25, 1.03, 1.11, (40, 44, 52, 255))]
    for k in range(3):                                   # spokes, turning
        a = phase * 2 * math.pi + k * 2 * math.pi / 3
        dy, dz = math.cos(a) * 0.18, math.sin(a) * 0.18
        for sx in (0.062, -0.062):
            s.append(cyl((sx, -0.2, 0.34), (sx, -0.2 + dy, 0.34 + dz), 0.022, STEEL, 6))
    a = phase * 2 * math.pi                              # cranks and pedals
    for side, off in ((1, 0.0), (-1, math.pi)):
        py, pz = math.cos(a + off) * 0.1, math.sin(a + off) * 0.1
        s.append(cyl((side * 0.06, 0.02, 0.3), (side * 0.06, 0.02 + py, 0.3 + pz), 0.02, CHAIN, 6))
        x0 = side * 0.06 if side > 0 else side * 0.06 - 0.08
        s.append(box(x0, x0 + 0.08, py, 0.06 + py, 0.28 + pz, 0.32 + pz, PAD))
    return s


def build_exercise_bike(out):
    for f in FACINGS:
        suffix = _facing_suffix(f)
        _save(render(exercise_bike(0.0), f, BIKE_CANVAS, BIKE_ORIGIN), out, "ExerciseBike_" + f)
        for i in range(BIKE_FRAMES):
            _save(render(exercise_bike(i / float(BIKE_FRAMES)), f, BIKE_CANVAS, BIKE_ORIGIN),
                  out, "ExerciseBikePedal%s_%d" % (suffix, i))
    print("  ExerciseBike_{north,east,south,west} + pedal frames per facing")


# --------------------------------------------------------------------------- 5. bouldering wall
# A 2x1 panel with the crash mat drawn on the row in front, where the
# climber's interaction cell is.
WALL_CANVAS, WALL_ORIGIN = (512, 512), (256, 300)


def bouldering_wall():
    b0y, top_y, top_z = -0.2, 0.3, 2.3                 # leans back a little
    s = [box(-1.0, 1.0, -1.45, -0.18, 0.0, 0.18, MATC),
         hexa([(-1.0, b0y, 0.0), (1.0, b0y, 0.0), (1.0, b0y + 0.08, 0.0), (-1.0, b0y + 0.08, 0.0),
               (-1.0, top_y, top_z), (1.0, top_y, top_z), (1.0, top_y + 0.08, top_z), (-1.0, top_y + 0.08, top_z)], PLY)]
    for x in (-0.85, 0.0, 0.85):                         # braces behind
        s.append(hexa([(x - 0.04, 0.46, 0.0), (x + 0.04, 0.46, 0.0), (x + 0.04, 0.5, 0.0), (x - 0.04, 0.5, 0.0),
                       (x - 0.04, top_y + 0.08, top_z - 0.05), (x + 0.04, top_y + 0.08, top_z - 0.05),
                       (x + 0.04, top_y + 0.12, top_z - 0.05), (x - 0.04, top_y + 0.12, top_z - 0.05)], WOOD))
    k = 0
    for i in range(8):
        t = 0.1 + 0.105 * i
        for m in range(8):
            gx = -0.8 + 0.23 * m
            j = (i * 7 + int(gx * 100) * 13) % 17
            x = gx + (j - 8) * 0.008
            tt = t + ((j * 5) % 9 - 4) * 0.004
            y = b0y + (top_y - b0y) * tt - 0.02
            z = top_z * tt
            s.append(box(x - 0.035, x + 0.035, y - 0.03, y, z - 0.03, z + 0.03, HOLDS[(k + j) % 5]))
            k += 1
    return s


def build_bouldering_wall(out):
    for f in FACINGS:
        _save(render(bouldering_wall(), f, WALL_CANVAS, WALL_ORIGIN), out, "BoulderingWall_" + f)
    print("  BoulderingWall_{north,east,south,west}  (%dx%d)" % WALL_CANVAS)


def build_all(out):
    build_trampoline(out)
    build_punching_bag(out)
    build_weight_bench(out)
    build_exercise_bike(out)
    build_bouldering_wall(out)
