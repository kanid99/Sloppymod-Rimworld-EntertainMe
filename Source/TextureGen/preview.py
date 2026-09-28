"""Builds the texture overview (promo/TexturePreview.png) from the same drawings
used for the in-game art. The mod's About/Preview.png is Source/Promo's banner."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pnglib import Canvas  # noqa: E402

# 5x7 bitmap font, only the glyphs the preview text needs.
FONT = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.###.",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": "#####|..#..|..#..|..#..|..#..|..#..|#####",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "N": "#...#|##..#|##..#|#.#.#|#..##|#..##|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|#####",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": ".###.|#....|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|..#..|..#..|..#..",
    "9": ".###.|#...#|#...#|.####|....#|#...#|.###.",
    "-": ".....|.....|.....|#####|.....|.....|.....",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "J": "....#|....#|....#|....#|#...#|#...#|.###.",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|##.##|#...#",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "#####|...#.|..##.|....#|....#|#...#|.###.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    ".": ".....|.....|.....|.....|.....|.....|..#..",
    "(": "...#.|..#..|.#...|.#...|.#...|..#..|...#.",
    ")": ".#...|..#..|...#.|...#.|...#.|..#..|.#...",
    ",": ".....|.....|.....|.....|.....|..#..|.#...",
    "'": "..#..|..#..|.....|.....|.....|.....|.....",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "!": "..#..|..#..|..#..|..#..|..#..|.....|..#..",
    "*": ".....|#.#.#|.###.|#####|.###.|#.#.#|.....",
    "/": "....#|...#.|...#.|..#..|.#...|.#...|#....",
    " ": ".....|.....|.....|.....|.....|.....|.....",
}


def text(canvas, string, x, y, scale, color):
    for ch in string.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            raise KeyError("no glyph for %r - add it to FONT" % ch)
        for row, bits in enumerate(glyph.split("|")):
            for col, bit in enumerate(bits):
                if bit == "#":
                    canvas.rect(x + col * scale, y + row * scale,
                                x + (col + 1) * scale, y + (row + 1) * scale, color)
        x += 6 * scale
    return x


def text_width(string, scale):
    return len(string) * 6 * scale - scale


def blit(canvas, src, sw, sh, dx, dy, scale):
    """Nearest-neighbour blit of an RGBA buffer onto an ss=1 canvas."""
    for y in range(int(sh * scale)):
        sy = int(y / scale)
        for x in range(int(sw * scale)):
            sx = int(x / scale)
            i = (sy * sw + sx) * 4
            a = src[i + 3]
            if a:
                canvas._blend(int(dx) + x, int(dy) + y,
                              (src[i], src[i + 1], src[i + 2], a))


def build(sprites, out_path):
    """sprites: dict name -> (pixels, w, h) produced by generate_textures."""
    W, H = 640, 600
    c = Canvas(W, H, ss=1)

    c.rect(0, 0, W, H, (30, 33, 41, 255))
    for i in range(-10, 40):                      # faint diagonal weave
        c.line(i * 24, 0, i * 24 + 220, H, (255, 255, 255, 5), 10)
    c.rect(0, 0, W, 96, (24, 26, 33, 255))
    c.rect(0, 94, W, 97, (232, 198, 78, 255))

    title = "ENTERTAINING IDEAS"
    text(c, title, (W - text_width(title, 4)) / 2, 20, 4, (240, 236, 228, 255))
    sub = "NEOLITHIC TO ARCHOTECH"
    text(c, sub, (W - text_width(sub, 2)) / 2, 58, 2, (178, 186, 202, 255))
    tag = "13 IDEAS - 16 BUILDINGS"
    text(c, tag, (W - text_width(tag, 2)) / 2, 76, 2, (232, 198, 78, 255))

    row_a = ["KnuckleboneMat", "ShadowLanternTheater", "CocktailArcade",
             "MassageChair", "SoakingTub", "KaraokeMachine"]
    slot = W / len(row_a)
    for i, name in enumerate(row_a):
        px, sw, sh = sprites[name]
        scale = min(88.0 / sw, 88.0 / sh)
        blit(c, px, sw, sh, i * slot + (slot - sw * scale) / 2, 110, scale)

    row_b = ["Aquarium", "HologamePod", "GravballCourt", "VistaDay"]
    slot = W / len(row_b)
    for i, name in enumerate(row_b):
        px, sw, sh = sprites[name]
        scale = min(140.0 / sw, 84.0 / sh)
        blit(c, px, sw, sh, i * slot + (slot - sw * scale) / 2, 212, scale)

    for i, name in enumerate(["PinballClassic", "PinballBoomalope",
                              "PinballMechRampage", "PinballArchotech",
                              "SkittlesLane"]):
        px, sw, sh = sprites[name]
        scale = min(208.0 / sh, 58.0 / sw)          # tall, but kept to its slot
        blit(c, px, sw, sh, 20 + i * 62 + (58 - sw * scale) / 2, 322 + 208 - sh * scale, scale)

    px, sw, sh = sprites["DreamloopHolotheater"]
    scale = 268.0 / sw
    blit(c, px, sw, sh, 344, 356, scale)
    px, sw, sh = sprites["DreamloopProjection"]
    scale = 268.0 / sw
    blit(c, px, sw, sh, 344, 460, scale)

    c.save(out_path)
    print("  Preview.png  (%dx%d)" % (W, H))
