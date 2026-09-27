"""Resampling helpers for drawing a facing from another drawing.

RimWorld's camera looks down with a slight tilt from the south: a table's top
reads a little foreshortened with its south side showing below it, and a
face that points east or west is seen at a slant if at all. These map an
already-drawn picture onto such a surface - squashed, or slanted into a
parallelogram - so the view and the picture on it can never disagree.
Pure Python, like pnglib, so nothing beyond the standard library is needed."""
import math


def sample(px, w, h, x, y):
    """Bilinear sample of an RGBA buffer, premultiplied so edges do not fringe."""
    if x < -0.5 or y < -0.5 or x > w - 0.5 or y > h - 0.5:
        return (0, 0, 0, 0)
    x = min(max(x - 0.5, 0.0), w - 1.0); y = min(max(y - 0.5, 0.0), h - 1.0)
    x0, y0 = int(x), int(y); x1, y1 = min(x0 + 1, w - 1), min(y0 + 1, h - 1)
    fx, fy = x - x0, y - y0
    acc = [0.0, 0.0, 0.0, 0.0]
    for xx, yy, wt in ((x0, y0, (1 - fx) * (1 - fy)), (x1, y0, fx * (1 - fy)),
                       (x0, y1, (1 - fx) * fy), (x1, y1, fx * fy)):
        if wt <= 0: continue
        i = (yy * w + xx) * 4; a = px[i + 3] / 255.0 * wt
        acc[0] += px[i] * a; acc[1] += px[i + 1] * a; acc[2] += px[i + 2] * a; acc[3] += a
    if acc[3] <= 0: return (0, 0, 0, 0)
    return (int(acc[0] / acc[3]), int(acc[1] / acc[3]), int(acc[2] / acc[3]), int(acc[3] * 255))


def blit_quad(c, px, w, h, src, O, U, V, alpha=1.0):
    """Draw src rect (x0, y0, x1, y1) of an RGBA buffer into canvas c as the
    parallelogram O + s*U + t*V: s runs the source left to right, t its
    bottom to top. Sampled at the canvas's supersampled resolution."""
    x0, y0, x1, y1 = src
    ss = c.ss
    det = U[0] * V[1] - U[1] * V[0]
    if abs(det) < 1e-9: return
    pts = [O, (O[0] + U[0], O[1] + U[1]), (O[0] + V[0], O[1] + V[1]),
           (O[0] + U[0] + V[0], O[1] + U[1] + V[1])]
    bx0 = max(0, int(min(p[0] for p in pts) * ss)); bx1 = min(c.w * ss, int(math.ceil(max(p[0] for p in pts) * ss)))
    by0 = max(0, int(min(p[1] for p in pts) * ss)); by1 = min(c.h * ss, int(math.ceil(max(p[1] for p in pts) * ss)))
    for sy in range(by0, by1):
        py = (sy + 0.5) / ss - O[1]
        for sx in range(bx0, bx1):
            pxx = (sx + 0.5) / ss - O[0]
            s = (pxx * V[1] - py * V[0]) / det
            t = (U[0] * py - U[1] * pxx) / det
            if s < 0 or s > 1 or t < 0 or t > 1: continue
            col = sample(px, w, h, x0 + s * (x1 - x0), y1 - t * (y1 - y0))
            if col[3]:
                c._blend(sx, sy, (col[0], col[1], col[2], int(col[3] * alpha)))


def blit_rect(c, px, w, h, src, dst, alpha=1.0):
    """Stretch src rect into the axis-aligned dst rect (x0, y0, x1, y1)."""
    X0, Y0, X1, Y1 = dst
    blit_quad(c, px, w, h, src, (X0, Y1), (X1 - X0, 0), (0, Y0 - Y1), alpha)
