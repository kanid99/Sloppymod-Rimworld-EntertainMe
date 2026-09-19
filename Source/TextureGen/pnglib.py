"""Minimal dependency-free PNG writer + supersampled drawing canvas.

Used by generate_textures.py to build the mod's placeholder art without
requiring Pillow. Everything is RGBA, drawn at 4x and box-filtered down so
circles and diagonals come out smooth at RimWorld's texture sizes.
"""

import math
import struct
import zlib


def write_png(path, width, height, rgba):
    raw = b"".join(
        b"\x00" + bytes(rgba[y * width * 4:(y + 1) * width * 4])
        for y in range(height)
    )

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as handle:
        handle.write(blob)


class Canvas:
    """Draws in final-image coordinates; internally supersampled by `ss`."""

    def __init__(self, width, height, ss=4):
        self.w = width
        self.h = height
        self.ss = ss
        self.buf = bytearray(width * ss * height * ss * 4)

    # --- low level ------------------------------------------------------
    def _blend(self, x, y, color):
        sw, sh = self.w * self.ss, self.h * self.ss
        if x < 0 or y < 0 or x >= sw or y >= sh:
            return
        r, g, b, a = color
        if a <= 0:
            return
        i = (y * sw + x) * 4
        buf = self.buf
        if a >= 255 and buf[i + 3] == 0:
            buf[i:i + 4] = bytes((r, g, b, 255))
            return
        sa = a / 255.0
        da = buf[i + 3] / 255.0
        out_a = sa + da * (1 - sa)
        if out_a <= 0:
            buf[i:i + 4] = b"\x00\x00\x00\x00"
            return
        for k, sc in enumerate((r, g, b)):
            dc = buf[i + k]
            buf[i + k] = int(round((sc * sa + dc * da * (1 - sa)) / out_a))
        buf[i + 3] = int(round(out_a * 255))

    # --- shapes (coordinates in final-image pixels) ---------------------
    def rect(self, x0, y0, x1, y1, color, radius=0.0):
        s = self.ss
        X0, Y0, X1, Y1 = (int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s))
        r = radius * s
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                if r > 0:
                    cx = min(max(x + 0.5, X0 + r), X1 - r)
                    cy = min(max(y + 0.5, Y0 + r), Y1 - r)
                    if math.hypot(x + 0.5 - cx, y + 0.5 - cy) > r:
                        continue
                self._blend(x, y, color)

    def frame(self, x0, y0, x1, y1, color, width=1.0, radius=0.0):
        """Hollow rounded rectangle, drawn as four inset-clipped bands."""
        s = self.ss
        X0, Y0, X1, Y1 = (int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s))
        r, wd = radius * s, width * s
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                cx = min(max(x + 0.5, X0 + r), X1 - r)
                cy = min(max(y + 0.5, Y0 + r), Y1 - r)
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r > 0 and d > r:
                    continue
                edge = min(x + 0.5 - X0, X1 - x - 0.5, y + 0.5 - Y0, Y1 - y - 0.5)
                if r > 0:
                    edge = min(edge, r - d + wd if d > 0 else edge)
                if edge <= wd:
                    self._blend(x, y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        s = self.ss
        X0, X1 = int((cx - rx) * s) - 1, int((cx + rx) * s) + 1
        Y0, Y1 = int((cy - ry) * s) - 1, int((cy + ry) * s) + 1
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                dx = (x + 0.5) / s - cx
                dy = (y + 0.5) / s - cy
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    self._blend(x, y, color)

    def circle(self, cx, cy, r, color):
        self.ellipse(cx, cy, r, r, color)

    def ring(self, cx, cy, r_outer, r_inner, color):
        s = self.ss
        X0, X1 = int((cx - r_outer) * s) - 1, int((cx + r_outer) * s) + 1
        Y0, Y1 = int((cy - r_outer) * s) - 1, int((cy + r_outer) * s) + 1
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                d = math.hypot((x + 0.5) / s - cx, (y + 0.5) / s - cy)
                if r_inner <= d <= r_outer:
                    self._blend(x, y, color)

    def wedge(self, cx, cy, r_outer, r_inner, a0, a1, color):
        """Angles in degrees, 0 = +x, counter-clockwise."""
        s = self.ss
        X0, X1 = int((cx - r_outer) * s) - 1, int((cx + r_outer) * s) + 1
        Y0, Y1 = int((cy - r_outer) * s) - 1, int((cy + r_outer) * s) + 1
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                dx = (x + 0.5) / s - cx
                dy = (y + 0.5) / s - cy
                d = math.hypot(dx, dy)
                if not (r_inner <= d <= r_outer):
                    continue
                ang = math.degrees(math.atan2(-dy, dx)) % 360
                lo, hi = a0 % 360, a1 % 360
                inside = lo <= ang < hi if lo < hi else (ang >= lo or ang < hi)
                if inside:
                    self._blend(x, y, color)

    def poly(self, points, color):
        s = self.ss
        pts = [(px * s, py * s) for px, py in points]
        Y0 = int(min(p[1] for p in pts)) - 1
        Y1 = int(max(p[1] for p in pts)) + 1
        X0 = int(min(p[0] for p in pts)) - 1
        X1 = int(max(p[0] for p in pts)) + 1
        for y in range(Y0, Y1):
            yc = y + 0.5
            spans = []
            for i in range(len(pts)):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % len(pts)]
                if (ay <= yc < by) or (by <= yc < ay):
                    t = (yc - ay) / (by - ay)
                    spans.append(ax + t * (bx - ax))
            spans.sort()
            for i in range(0, len(spans) - 1, 2):
                for x in range(max(X0, int(spans[i])), min(X1, int(spans[i + 1]) + 1)):
                    if spans[i] <= x + 0.5 <= spans[i + 1]:
                        self._blend(x, y, color)

    def line(self, x0, y0, x1, y1, color, width=1.0):
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        nx, ny = -(y1 - y0) / length * width / 2, (x1 - x0) / length * width / 2
        self.poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                   (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], color)

    # --- output ---------------------------------------------------------
    def _downsample(self):
        s, w, h = self.ss, self.w, self.h
        sw = w * s
        out = bytearray(w * h * 4)
        n = s * s
        for y in range(h):
            for x in range(w):
                r = g = b = a = 0
                for dy in range(s):
                    row = ((y * s + dy) * sw + x * s) * 4
                    for dx in range(s):
                        i = row + dx * 4
                        sa = self.buf[i + 3]
                        r += self.buf[i] * sa
                        g += self.buf[i + 1] * sa
                        b += self.buf[i + 2] * sa
                        a += sa
                o = (y * w + x) * 4
                if a == 0:
                    continue
                out[o] = min(255, r // a)
                out[o + 1] = min(255, g // a)
                out[o + 2] = min(255, b // a)
                out[o + 3] = a // n
        return out

    def pixels(self):
        return self._downsample()

    def save(self, path):
        write_png(path, self.w, self.h, self._downsample())


def rotate(pixels, width, height, turns):
    """Rotate an RGBA buffer clockwise by `turns` * 90 degrees."""
    turns %= 4
    if turns == 0:
        return pixels, width, height
    for _ in range(turns):
        out = bytearray(len(pixels))
        nw, nh = height, width
        for y in range(height):
            for x in range(width):
                # Rotating clockwise, a source row becomes a destination
                # column: the flip is against the NEW width, which is the old
                # height. Using the new height here silently works for square
                # images and mangles every other shape.
                nx, ny = nw - 1 - y, x
                si = (y * width + x) * 4
                di = (ny * nw + nx) * 4
                out[di:di + 4] = pixels[si:si + 4]
        pixels, width, height = out, nw, nh
    return pixels, width, height


def read_png(path):
    """Read an 8-bit RGBA PNG back into (pixels, width, height).

    Only the shape this library writes is supported: colour type 6, depth 8,
    no interlacing. All five scanline filters are handled anyway, in case a
    file is ever replaced with hand-drawn art from another tool.
    """
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("%s is not a PNG" % path)

    pos, idat, width, height = 8, [], None, None
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if depth != 8 or ctype != 6 or interlace:
                raise ValueError("%s: need 8-bit RGBA, non-interlaced" % path)
        elif tag == b"IDAT":
            idat.append(chunk)
        elif tag == b"IEND":
            break
        pos += 12 + length

    raw = zlib.decompress(b"".join(idat))
    stride = width * 4
    out = bytearray(stride * height)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if filt == 1:
            for i in range(4, stride):
                line[i] = (line[i] + line[i - 4]) & 255
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif filt == 3:
            for i in range(stride):
                left = line[i - 4] if i >= 4 else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif filt == 4:
            for i in range(stride):
                left = line[i - 4] if i >= 4 else 0
                up = prev[i]
                corner = prev[i - 4] if i >= 4 else 0
                pa, pb, pc = abs(up - corner), abs(left - corner), abs(left + up - 2 * corner)
                pred = left if (pa <= pb and pa <= pc) else (up if pb <= pc else corner)
                line[i] = (line[i] + pred) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return bytes(out), width, height
