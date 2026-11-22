#!/usr/bin/env python3
"""Render the v3 front page: THE WORLD IN ONE DAY — Sunday 22 November 2026.

Layout (1024x1024, all fresh code in this session):
  masthead strip, huge date headline, red deck line, 6 boxed key numbers,
  colored region strip, THE DAY IN UTC strip, 3 lead cards with large drawn
  scenes, 10 small cards with drawn scene banners, dotted world map with
  numbered pins, 23-story wire list, DATE CHECK box, footer.
Deterministic: no randomness, no timestamps, fixed fonts, fixed colors.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 24
CW = W - 2 * MARGIN  # 976

PAPER = (248, 245, 238)
INK = (20, 20, 19)
CRIMSON = (139, 30, 30)
NAVY = (20, 33, 61)
GOLD = (183, 121, 31)
MUTED = (107, 101, 92)
RULE = (180, 172, 158)
CARD_BG = (255, 253, 247)
SKY_NIGHT = (16, 24, 48)
SKY_DAY = (214, 228, 240)
SEA = (46, 92, 128)

FONT_DIR = "/usr/share/fonts/truetype/liberation"


def font(name, size):
    path = os.path.join(FONT_DIR, name)
    assert os.path.exists(path), "missing font: " + path
    return ImageFont.truetype(path, size)


SERIF = "LiberationSerif-Regular.ttf"
SERIF_B = "LiberationSerif-Bold.ttf"
SERIF_I = "LiberationSerif-Italic.ttf"
SANS = "LiberationSans-Regular.ttf"
SANS_B = "LiberationSans-Bold.ttf"

_cache = {}


def F(name, size):
    key = (name, size)
    if key not in _cache:
        _cache[key] = font(name, size)
    return _cache[key]


def text_w(text, fnt):
    return fnt.getbbox(text)[2]


def wrap(text, fnt, width):
    """Greedy word wrap to a pixel width; returns a list of lines."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    for word in words[1:]:
        trial = cur + " " + word
        if text_w(trial, fnt) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def draw_lines(d, x, y, lines, fnt, fill, leading):
    """Draw lines top-to-bottom; returns y after the last line."""
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def point_in_poly(px, py, poly):
    """Ray casting; poly is a list of (x, y)."""
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py):
            xint = (xj - xi) * (py - yi) / (yj - yi) + xi
            if px < xint:
                inside = not inside
        j = i
    return inside


def clip_text(d, text, fnt, x, y, max_w, fill):
    """Draw text truncated with an ellipsis if it exceeds max_w."""
    if text_w(text, fnt) <= max_w:
        d.text((x, y), text, font=fnt, fill=fill)
        return
    ell = "…"
    while text and text_w(text + ell, fnt) > max_w:
        text = text[:-1]
    d.text((x, y), text + ell, font=fnt, fill=fill)


# ---------------------------------------------------------------- scenes
# Every scene draws into the box (x0, y0, w, h) with relative coordinates,
# so the same scene works at lead size and at small-card banner size.

def _sky(d, x0, y0, w, h, top, bottom):
    for i in range(h):
        t = i / max(h - 1, 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.line([(x0, y0 + i), (x0 + w, y0 + i)], fill=(r, g, b))


def scene_cop31(d, x0, y0, w, h):
    """Conference table: pale sky, globe, long table, seated delegates, clock."""
    _sky(d, x0, y0, w, h, (198, 220, 235), (232, 238, 242))
    cx, cy, r = x0 + w * 0.16, y0 + h * 0.34, h * 0.26
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(46, 120, 90))
    d.ellipse([cx - r * 0.55, cy - r * 0.8, cx + r * 0.5, cy + r * 0.7], fill=(120, 180, 140))
    # long table
    ty = y0 + h * 0.62
    d.rectangle([x0 + w * 0.06, ty, x0 + w * 0.94, ty + h * 0.10], fill=(120, 72, 32))
    d.rectangle([x0 + w * 0.06, ty + h * 0.10, x0 + w * 0.94, ty + h * 0.13], fill=(90, 52, 22))
    # delegates: heads + shoulders in a row
    cols = [(139, 30, 30), (31, 78, 121), (183, 121, 31), (30, 107, 74),
            (91, 74, 138), (122, 60, 30), (20, 90, 110), (160, 40, 90)]
    for i, c in enumerate(cols):
        hx = x0 + w * (0.10 + i * 0.105)
        d.ellipse([hx - h * 0.05, ty - h * 0.22, hx + h * 0.05, ty - h * 0.12], fill=(210, 180, 150))
        d.pieslice([hx - h * 0.09, ty - h * 0.14, hx + h * 0.09, ty + h * 0.02], 180, 360, fill=c)
    # wall clock
    ccx, ccy, cr = x0 + w * 0.88, y0 + h * 0.24, h * 0.17
    d.ellipse([ccx - cr, ccy - cr, ccx + cr, ccy + cr], fill=(255, 255, 255), outline=INK, width=2)
    d.line([(ccx, ccy), (ccx, ccy - cr * 0.7)], fill=INK, width=2)
    d.line([(ccx, ccy), (ccx + cr * 0.55, ccy)], fill=INK, width=2)


def scene_bahrain(d, x0, y0, w, h):
    """Night over Bahrain: dark sky, radar dishes, missile arcs, fire glow."""
    _sky(d, x0, y0, w, h, (10, 16, 38), (30, 44, 78))
    for sx, sy in [(0.12, 0.18), (0.35, 0.10), (0.62, 0.15), (0.85, 0.08), (0.5, 0.22)]:
        d.ellipse([x0 + w * sx - 1, y0 + h * sy - 1, x0 + w * sx + 1, y0 + h * sy + 1], fill=(230, 230, 200))
    # missile arcs (dotted)
    for k in range(9):
        t = k / 8
        ax = x0 + w * (0.08 + 0.55 * t)
        ay = y0 + h * (0.85 - 0.55 * t * t * 1.4)
        d.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=(255, 190, 80))
    for k in range(7):
        t = k / 6
        ax = x0 + w * (0.95 - 0.5 * t)
        ay = y0 + h * (0.88 - 0.5 * t * t * 1.3)
        d.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=(255, 150, 60))
    # radar dishes on the ground
    gy = y0 + h * 0.88
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(18, 22, 34))
    for bx in (0.22, 0.55, 0.82):
        px = x0 + w * bx
        d.line([(px, gy), (px, gy - h * 0.16)], fill=(150, 150, 150), width=3)
        d.pieslice([px - h * 0.13, gy - h * 0.30, px + h * 0.13, gy - h * 0.04], 200, 340, fill=(200, 200, 200))
    # fire glow at a base
    fx = x0 + w * 0.68
    d.polygon([(fx - h * 0.10, gy), (fx, gy - h * 0.28), (fx + h * 0.10, gy)], fill=(255, 120, 20))
    d.polygon([(fx - h * 0.05, gy), (fx, gy - h * 0.16), (fx + h * 0.05, gy)], fill=(255, 200, 60))


def scene_kyiv(d, x0, y0, w, h):
    """Night city under drones: dark sky, lit windows, drone dots, flashes."""
    _sky(d, x0, y0, w, h, (8, 12, 30), (24, 34, 66))
    for sx, sy in [(0.08, 0.12), (0.3, 0.08), (0.55, 0.16), (0.78, 0.10), (0.92, 0.2)]:
        d.ellipse([x0 + w * sx - 1, y0 + h * sy - 1, x0 + w * sx + 1, y0 + h * sy + 1], fill=(220, 220, 190))
    # drones with trails
    for dx, dy, ln in [(0.18, 0.28, 0.10), (0.45, 0.20, 0.08), (0.68, 0.32, 0.12), (0.85, 0.24, 0.07)]:
        d.line([(x0 + w * dx, y0 + h * dy), (x0 + w * (dx + ln), y0 + h * (dy + 0.05))], fill=(255, 200, 90), width=2)
        d.ellipse([x0 + w * dx - 3, y0 + h * dy - 3, x0 + w * dx + 3, y0 + h * dy + 3], fill=(255, 220, 120))
    # building silhouettes with lit windows
    gy = y0 + h * 0.92
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(10, 12, 22))
    bx = x0
    import random as _rnd
    _rnd.seed(7)
    while bx < x0 + w:
        bw = w * _rnd.uniform(0.09, 0.16)
        bh = h * _rnd.uniform(0.28, 0.55)
        d.rectangle([bx, gy - bh, bx + bw, gy], fill=(22, 28, 48))
        for _ in range(6):
            wx = bx + _rnd.uniform(2, max(3, bw - 6))
            wy = gy - bh + _rnd.uniform(3, max(4, bh - 8))
            if _rnd.random() < 0.6:
                d.rectangle([wx, wy, wx + 3, wy + 4], fill=(255, 210, 110))
        bx += bw + 2
    # explosion flash
    ex, ey = x0 + w * 0.72, gy - h * 0.12
    d.polygon([(ex, ey - h * 0.14), (ex + h * 0.05, ey), (ex, ey + h * 0.10),
               (ex - h * 0.05, ey)], fill=(255, 160, 40))


def scene_tanker(d, x0, y0, w, h):
    """Suezmax tanker burning at anchor: blue sea, grey hull, stern fire."""
    _sky(d, x0, y0, w, h, (170, 200, 220), (220, 230, 235))
    sy = y0 + h * 0.62
    d.rectangle([x0, sy, x0 + w, y0 + h], fill=SEA)
    for i in range(4):
        wy = sy + h * (0.08 + i * 0.09)
        d.line([(x0 + w * 0.05, wy), (x0 + w * 0.95, wy)], fill=(140, 180, 210), width=1)
    # hull
    hx0, hx1 = x0 + w * 0.10, x0 + w * 0.88
    d.polygon([(hx0, sy - h * 0.06), (hx1, sy - h * 0.06), (hx1 - w * 0.05, sy + h * 0.16),
               (hx0 + w * 0.04, sy + h * 0.16)], fill=(60, 60, 66))
    d.rectangle([hx0, sy - h * 0.06, hx1, sy - h * 0.02], fill=(120, 30, 30))
    # deck tanks
    for tx in (0.22, 0.38, 0.54, 0.70):
        d.rectangle([x0 + w * tx, sy - h * 0.20, x0 + w * (tx + 0.10), sy - h * 0.06], fill=(200, 200, 200))
    # stern fire + smoke
    fx = x0 + w * 0.14
    d.polygon([(fx - h * 0.08, sy - h * 0.05), (fx, sy - h * 0.30), (fx + h * 0.08, sy - h * 0.05)], fill=(255, 110, 20))
    d.polygon([(fx - h * 0.04, sy - h * 0.05), (fx, sy - h * 0.18), (fx + h * 0.04, sy - h * 0.05)], fill=(255, 200, 70))
    for sx, sy2, sr in [(0.16, 0.22, 0.05), (0.20, 0.12, 0.07), (0.13, 0.06, 0.04)]:
        d.ellipse([x0 + w * sx - h * sr, y0 + h * sy2 - h * sr, x0 + w * sx + h * sr, y0 + h * sy2 + h * sr], fill=(90, 90, 95))


def scene_sparta(d, x0, y0, w, h):
    """Cargo ship burning at dusk: orange horizon, dark hull, smoke column."""
    _sky(d, x0, y0, w, h, (240, 180, 110), (250, 220, 180))
    sy = y0 + h * 0.66
    d.rectangle([x0, sy, x0 + w, y0 + h], fill=(52, 88, 120))
    d.line([(x0, sy), (x0 + w, sy)], fill=(220, 200, 160), width=2)
    # hull
    d.polygon([(x0 + w * 0.12, sy - h * 0.04), (x0 + w * 0.86, sy - h * 0.04),
               (x0 + w * 0.80, sy + h * 0.12), (x0 + w * 0.18, sy + h * 0.12)], fill=(40, 40, 44))
    d.rectangle([x0 + w * 0.30, sy - h * 0.18, x0 + w * 0.62, sy - h * 0.04], fill=(180, 180, 175))
    # smoke column
    for sx, sy2, sr in [(0.48, 0.28, 0.06), (0.52, 0.18, 0.08), (0.46, 0.08, 0.05)]:
        d.ellipse([x0 + w * sx - h * sr, y0 + h * sy2 - h * sr, x0 + w * sx + h * sr, y0 + h * sy2 + h * sr], fill=(70, 70, 75))
    # flames on deck
    fx = x0 + w * 0.70
    d.polygon([(fx - h * 0.07, sy - h * 0.04), (fx, sy - h * 0.24), (fx + h * 0.07, sy - h * 0.04)], fill=(255, 130, 30))
    # small rescue boat
    bx = x0 + w * 0.06
    d.polygon([(bx, sy + h * 0.10), (bx + w * 0.12, sy + h * 0.10), (bx + w * 0.10, sy + h * 0.18), (bx + w * 0.02, sy + h * 0.18)], fill=(200, 60, 40))


def scene_hongkong(d, x0, y0, w, h):
    """Dusk skyline with ballot box: towers, lit windows, red ballot box."""
    _sky(d, x0, y0, w, h, (120, 90, 140), (240, 190, 140))
    gy = y0 + h * 0.92
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(40, 36, 44))
    import random as _rnd
    _rnd.seed(11)
    bx = x0
    while bx < x0 + w:
        bw = w * _rnd.uniform(0.10, 0.18)
        bh = h * _rnd.uniform(0.30, 0.62)
        d.rectangle([bx, gy - bh, bx + bw, gy], fill=(52, 48, 62))
        for _ in range(5):
            wx = bx + _rnd.uniform(2, max(3, bw - 5))
            wy = gy - bh + _rnd.uniform(3, max(4, bh - 7))
            if _rnd.random() < 0.55:
                d.rectangle([wx, wy, wx + 3, wy + 4], fill=(255, 200, 120))
        bx += bw + 2
    # ballot box in front
    bx0, by0 = x0 + w * 0.36, y0 + h * 0.52
    bw, bh = w * 0.28, h * 0.34
    d.rectangle([bx0, by0, bx0 + bw, by0 + bh], fill=(178, 34, 34))
    d.rectangle([bx0 - w * 0.02, by0 - h * 0.04, bx0 + bw + w * 0.02, by0], fill=(120, 20, 20))
    d.line([(bx0 + bw * 0.3, by0 - h * 0.02), (bx0 + bw * 0.7, by0 - h * 0.02)], fill=(255, 255, 255), width=2)
    d.text((bx0 + bw * 0.5, by0 + bh * 0.18), "✓", font=F(SANS_B, max(10, int(h * 0.5))), fill=(255, 255, 255), anchor="mm")


def scene_riemann(d, x0, y0, w, h):
    """Chalkboard: dark green board, white zeta, chalk formulas."""
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(38, 66, 52))
    d.rectangle([x0, y0, x0 + w, y0 + h], outline=(120, 90, 50), width=3)
    d.text((x0 + w * 0.08, y0 + h * 0.08), "ζ(s) = 0", font=F(SERIF_B, max(12, int(h * 0.34))), fill=(255, 255, 255))
    d.text((x0 + w * 0.55, y0 + h * 0.14), "Re(s) = ½", font=F(SERIF_I, max(10, int(h * 0.24))), fill=(230, 230, 210))
    d.line([(x0 + w * 0.08, y0 + h * 0.62), (x0 + w * 0.92, y0 + h * 0.62)], fill=(220, 220, 200), width=2)
    d.text((x0 + w * 0.08, y0 + h * 0.68), "17.4m lines · 175,187 modules", font=F(SANS, max(8, int(h * 0.13))), fill=(210, 210, 190))
    # chalk question mark (the challenge)
    d.text((x0 + w * 0.82, y0 + h * 0.62), "?", font=F(SERIF_B, max(12, int(h * 0.34))), fill=(255, 120, 90))


def scene_power(d, x0, y0, w, h):
    """Dark city with a power pylon: night skyline, few lit windows, pylon."""
    _sky(d, x0, y0, w, h, (12, 14, 28), (40, 44, 66))
    gy = y0 + h * 0.92
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(12, 14, 24))
    import random as _rnd
    _rnd.seed(21)
    bx = x0
    while bx < x0 + w:
        bw = w * _rnd.uniform(0.10, 0.17)
        bh = h * _rnd.uniform(0.25, 0.50)
        d.rectangle([bx, gy - bh, bx + bw, gy], fill=(24, 28, 44))
        for _ in range(4):
            wx = bx + _rnd.uniform(2, max(3, bw - 5))
            wy = gy - bh + _rnd.uniform(3, max(4, bh - 7))
            if _rnd.random() < 0.35:
                d.rectangle([wx, wy, wx + 3, wy + 4], fill=(255, 210, 110))
        bx += bw + 2
    # pylon silhouette
    px = x0 + w * 0.78
    d.polygon([(px - h * 0.10, gy), (px, y0 + h * 0.10), (px + h * 0.10, gy)], outline=(160, 160, 160), width=2)
    d.line([(px - h * 0.16, y0 + h * 0.22), (px + h * 0.16, y0 + h * 0.22)], fill=(160, 160, 160), width=2)
    d.line([(px - h * 0.20, y0 + h * 0.34), (px + h * 0.20, y0 + h * 0.34)], fill=(160, 160, 160), width=2)


def scene_race(d, x0, y0, w, h):
    """Race track: grey asphalt curve, red car, checkered edge."""
    _sky(d, x0, y0, w, h, (200, 215, 230), (235, 238, 240))
    d.rectangle([x0, y0 + h * 0.55, x0 + w, y0 + h], fill=(90, 90, 92))
    d.line([(x0, y0 + h * 0.55), (x0 + w, y0 + h * 0.78)], fill=(255, 255, 255), width=2)
    d.line([(x0, y0 + h * 0.80), (x0 + w, y0 + h * 0.95)], fill=(255, 255, 255), width=2)
    # checkered flag strip at top
    for i in range(10):
        cx = x0 + w * i / 10
        d.rectangle([cx, y0, cx + w / 10, y0 + h * 0.10], fill=(20, 20, 20) if i % 2 == 0 else (255, 255, 255))
    # red car
    cx, cy = x0 + w * 0.45, y0 + h * 0.62
    d.polygon([(cx - w * 0.22, cy), (cx - w * 0.14, cy - h * 0.14), (cx + w * 0.10, cy - h * 0.14),
               (cx + w * 0.22, cy)], fill=(200, 30, 30))
    d.rectangle([cx - w * 0.22, cy, cx + w * 0.22, cy + h * 0.10], fill=(178, 24, 24))
    for wx in (-0.14, 0.10):
        d.ellipse([cx + w * wx - h * 0.07, cy + h * 0.06, cx + w * wx + h * 0.07, cy + h * 0.20], fill=(20, 20, 20))


def scene_gaza(d, x0, y0, w, h):
    """Desert road with a tank: sandy ground, grey tank, dust."""
    _sky(d, x0, y0, w, h, (235, 215, 180), (245, 235, 210))
    gy = y0 + h * 0.60
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(205, 175, 130))
    d.polygon([(x0, y0 + h), (x0 + w * 0.35, gy), (x0 + w * 0.65, gy), (x0 + w, y0 + h)], fill=(170, 140, 100))
    # tank
    tx, ty = x0 + w * 0.42, gy + h * 0.10
    d.rectangle([tx - w * 0.20, ty, tx + w * 0.20, ty + h * 0.12], fill=(90, 92, 80))
    d.rectangle([tx - w * 0.10, ty - h * 0.12, tx + w * 0.10, ty], fill=(100, 102, 88))
    d.line([(tx + w * 0.10, ty - h * 0.08), (tx + w * 0.30, ty - h * 0.10)], fill=(70, 72, 60), width=3)
    for wx in (-0.14, -0.02, 0.10):
        d.ellipse([tx + w * wx - h * 0.05, ty + h * 0.10, tx + w * wx + h * 0.05, ty + h * 0.20], fill=(50, 52, 44))
    # dust puffs
    for dx, dy, dr in [(0.72, 0.72, 0.05), (0.80, 0.78, 0.04), (0.66, 0.82, 0.04)]:
        d.ellipse([x0 + w * dx - h * dr, y0 + h * dy - h * dr, x0 + w * dx + h * dr, y0 + h * dy + h * dr], fill=(220, 195, 155))


def scene_tennis(d, x0, y0, w, h):
    """Tennis court: green court, white lines, net, yellow ball."""
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(58, 120, 70))
    d.rectangle([x0 + w * 0.06, y0 + h * 0.10, x0 + w * 0.94, y0 + h * 0.90], outline=(255, 255, 255), width=2)
    d.line([(x0 + w * 0.06, y0 + h * 0.50), (x0 + w * 0.94, y0 + h * 0.50)], fill=(255, 255, 255), width=2)
    d.line([(x0 + w * 0.50, y0 + h * 0.10), (x0 + w * 0.50, y0 + h * 0.90)], fill=(255, 255, 255), width=2)
    # net
    d.line([(x0 + w * 0.06, y0 + h * 0.50), (x0 + w * 0.94, y0 + h * 0.50)], fill=(30, 30, 30), width=4)
    # ball
    bx, by = x0 + w * 0.78, y0 + h * 0.24
    d.ellipse([bx - h * 0.09, by - h * 0.09, bx + h * 0.09, by + h * 0.09], fill=(210, 230, 60))


def scene_fire(d, x0, y0, w, h):
    """Factory fire at night: sawtooth roof, orange flames, smoke."""
    _sky(d, x0, y0, w, h, (14, 16, 30), (40, 36, 52))
    gy = y0 + h * 0.88
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(16, 16, 20))
    # factory with sawtooth roof
    fx0, fx1 = x0 + w * 0.08, x0 + w * 0.92
    d.rectangle([fx0, gy - h * 0.34, fx1, gy], fill=(70, 66, 70))
    for i in range(4):
        sx = fx0 + w * 0.21 * i
        d.polygon([(sx, gy - h * 0.34), (sx + w * 0.10, gy - h * 0.56), (sx + w * 0.21, gy - h * 0.34)], fill=(90, 86, 90))
    # flames
    for fx, fh in [(0.28, 0.34), (0.50, 0.44), (0.72, 0.30)]:
        px = x0 + w * fx
        d.polygon([(px - h * 0.07, gy - h * 0.30), (px, gy - h * (0.30 + fh)), (px + h * 0.07, gy - h * 0.30)], fill=(255, 120, 20))
        d.polygon([(px - h * 0.035, gy - h * 0.30), (px, gy - h * (0.30 + fh * 0.6)), (px + h * 0.035, gy - h * 0.30)], fill=(255, 200, 70))
    # smoke
    for sx, sy2, sr in [(0.50, 0.18, 0.06), (0.55, 0.08, 0.05), (0.44, 0.06, 0.04)]:
        d.ellipse([x0 + w * sx - h * sr, y0 + h * sy2 - h * sr, x0 + w * sx + h * sr, y0 + h * sy2 + h * sr], fill=(80, 80, 85))


def scene_sudan(d, x0, y0, w, h):
    """Desert with tents: sand dunes, white tents, harsh sun."""
    _sky(d, x0, y0, w, h, (240, 200, 140), (250, 230, 190))
    d.ellipse([x0 + w * 0.82, y0 + h * 0.08, x0 + w * 0.82 + h * 0.16, y0 + h * 0.08 + h * 0.16], fill=(255, 220, 120))
    gy = y0 + h * 0.62
    d.rectangle([x0, gy, x0 + w, y0 + h], fill=(215, 175, 120))
    d.polygon([(x0, gy + h * 0.10), (x0 + w * 0.5, gy - h * 0.08), (x0 + w, gy + h * 0.12), (x0 + w, y0 + h), (x0, y0 + h)], fill=(200, 160, 105))
    # tents
    for tx, ts in [(0.18, 0.16), (0.48, 0.20), (0.74, 0.14)]:
        px = x0 + w * tx
        d.polygon([(px - w * ts, gy + h * 0.14), (px, gy - h * 0.10), (px + w * ts, gy + h * 0.14)], fill=(245, 240, 225))
        d.polygon([(px - w * ts * 0.4, gy + h * 0.14), (px, gy + h * 0.02), (px + w * ts * 0.4, gy + h * 0.14)], fill=(90, 70, 50))


SCENES = {
    "cop31": scene_cop31, "bahrain": scene_bahrain, "kyiv": scene_kyiv,
    "tanker": scene_tanker, "sparta": scene_sparta, "hongkong": scene_hongkong,
    "riemann": scene_riemann, "power": scene_power, "race": scene_race,
    "gaza": scene_gaza, "tennis": scene_tennis, "fire": scene_fire,
    "sudan": scene_sudan,
}


# ---------------------------------------------------------------- layout

KICKERS = {
    1: "COP31: FINAL TEXT", 2: "BAHRAIN: IRAN STRIKES", 3: "KYIV: 186 DRONES",
    4: "SHIP ABLAZE", 5: "STILL BURNING", 6: "856 CANDIDATES", 7: "ζ CHALLENGED",
    8: "POWER CUTS", 9: "VERSTAPPEN WINS", 10: "GROUND PUSH",
    11: "ATP FINAL", 12: "FACTORY FIRE", 13: "RSF ACCUSED",
}

KICKER_COLORS = {
    1: (31, 78, 121), 2: CRIMSON, 3: NAVY, 4: (122, 60, 30), 5: (90, 30, 30),
    6: (31, 78, 121), 7: (38, 66, 52), 8: (60, 60, 60), 9: (139, 30, 30),
    10: (90, 70, 40), 11: (31, 78, 121), 12: (139, 30, 30), 13: (90, 60, 30),
}


def draw_masthead(d, data):
    d.rectangle([0, 0, W, 26], fill=NAVY)
    d.text((MARGIN, 6), data["meta"]["paper"], font=F(SANS_B, 12), fill=(255, 255, 255))
    right = data["meta"]["count_line"]
    d.text((W - MARGIN - text_w(right, F(SANS, 10)), 7), right, font=F(SANS, 10), fill=(220, 220, 210))


def draw_headline(d, data):
    d.text((W // 2, 34), data["meta"]["date"], font=F(SERIF_B, 64), fill=INK, anchor="ma")
    d.text((W // 2, 114), data["meta"]["deck"], font=F(SERIF_I, 15), fill=CRIMSON, anchor="ma")
    d.line([(MARGIN, 140), (W - MARGIN, 140)], fill=RULE, width=1)


def draw_key_strip(d, data):
    """6 boxed cells with big numerals. Asserted to fit inside the page."""
    y0, y1 = 142, 188
    gap = 4
    bw = (CW - 5 * gap) // 6
    for i, item in enumerate(data["key"]):
        x0 = MARGIN + i * (bw + gap)
        x1 = x0 + bw if i < 5 else W - MARGIN
        d.rectangle([x0, y0, x1, y1], fill=CARD_BG, outline=RULE, width=1)
        num = item["n"]
        nf = F(SERIF_B, 26)
        assert text_w(num, nf) <= (x1 - x0) - 8, "key number too wide: " + num
        d.text(((x0 + x1) // 2, y0 + 4), num, font=nf, fill=CRIMSON, anchor="ma")
        lab = wrap(item["label"], F(SANS, 8), (x1 - x0) - 10)
        assert len(lab) <= 2, "key label too long: " + item["label"]
        ly = y0 + 32
        for line in lab:
            d.text(((x0 + x1) // 2, ly), line, font=F(SANS, 8), fill=MUTED, anchor="ma")
            ly += 10


def draw_region_strip(d, data):
    y0, y1 = 190, 212
    n = len(data["regions"])
    bw = CW // n
    for i, reg in enumerate(data["regions"]):
        x0 = MARGIN + i * bw
        x1 = x0 + bw if i < n - 1 else W - MARGIN
        d.rectangle([x0, y0, x1, y1], fill=reg["color"])
        label = reg["name"] + " " + str(reg["count"])
        lf = F(SANS_B, 11)
        assert text_w(label, lf) <= (x1 - x0) - 6, "region label too wide: " + label
        d.text(((x0 + x1) // 2, y0 + 5), label, font=lf, fill=(255, 255, 255), anchor="ma")


def draw_utc_strip(d, data):
    """THE DAY IN UTC — first 6 timed beats, asserted to fit the bar."""
    y0, y1 = 214, 232
    d.rectangle([0, y0, W, y1], fill=NAVY)
    label = "THE DAY IN UTC"
    d.text((MARGIN, y0 + 4), label, font=F(SANS_B, 10), fill=(255, 200, 80))
    beats = data["utc"][:6]
    text = "  ·  ".join(b["t"] + " " + b["e"] for b in beats)
    bf = F(SANS, 9)
    x = MARGIN + text_w(label, F(SANS_B, 10)) + 14
    assert text_w(text, bf) <= (W - MARGIN) - x, "UTC strip too long"
    d.text((x, y0 + 4), text, font=bf, fill=(235, 235, 225))


def _card_frame(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=CARD_BG, outline=RULE, width=1)


def _badge(d, x, y, num):
    """Crimson numbered badge, 20px circle."""
    d.ellipse([x, y, x + 20, y + 20], fill=CRIMSON)
    d.text((x + 10, y + 3), str(num), font=F(SANS_B, 11), fill=(255, 255, 255), anchor="ma")


def _dateline(d, x, y, story, width):
    left = "%d · %s · %s" % (story["id"], story["place"], story["section"])
    lf = F(SANS_B, 8)
    d.text((x, y), left, font=lf, fill=INK)
    tag = story["tag"]
    tf = F(SANS_B, 8)
    tx = x + width - text_w(tag, tf)
    d.text((tx, y), tag, font=tf, fill=CRIMSON if tag in ("CLAIM", "CHALLENGED") else MUTED)


def draw_lead_card(d, x0, y0, w, story):
    """Lead card, 252px tall: 128px scene, kicker, dateline, headline, summary, source.
    Source is placed right after the summary (never a fixed y) so it cannot
    overlap the summary's last line."""
    h = 252
    _card_frame(d, x0, y0, x0 + w, y0 + h)
    SCENES[story["scene"]](d, x0 + 1, y0 + 1, w - 2, 128)
    ky = y0 + 129
    d.rectangle([x0 + 1, ky, x0 + w - 1, ky + 16], fill=KICKER_COLORS[story["id"]])
    d.text((x0 + 8, ky + 3), KICKERS[story["id"]], font=F(SANS_B, 10), fill=(255, 255, 255))
    _badge(d, x0 + w - 26, ky - 2, story["id"])
    ix = x0 + 8
    iw = w - 16
    _dateline(d, ix, ky + 20, story, iw)
    head = wrap(story["headline"], F(SERIF_B, 17), iw)
    assert len(head) <= 2, "lead headline too long: #%d" % story["id"]
    y = draw_lines(d, ix, ky + 34, head, F(SERIF_B, 17), INK, 18)
    summ = wrap(story["summary"], F(SANS, 10), iw)
    assert len(summ) <= 3, "lead summary too long: #%d (%d lines)" % (story["id"], len(summ))
    y = draw_lines(d, ix, y + 2, summ, F(SANS, 10), (40, 40, 38), 11)
    d.text((ix, y + 2), "(" + story["source"] + ")", font=F(SANS, 8), fill=MUTED)
    assert y + 12 <= y0 + h, "lead card #%d overflows" % story["id"]
    return y0 + h


def draw_small_card(d, x0, y0, w, story):
    """Small card, 126px tall: 48px scene banner, kicker, headline, summary, source.
    Source is placed right after the summary (never a fixed y) so it cannot
    overlap the summary's last line."""
    h = 126
    _card_frame(d, x0, y0, x0 + w, y0 + h)
    SCENES[story["scene"]](d, x0 + 1, y0 + 1, w - 2, 48)
    ky = y0 + 49
    d.rectangle([x0 + 1, ky, x0 + w - 1, ky + 13], fill=KICKER_COLORS[story["id"]])
    d.text((x0 + 6, ky + 2), KICKERS[story["id"]], font=F(SANS_B, 8), fill=(255, 255, 255))
    _badge(d, x0 + w - 22, ky - 4, story["id"])
    ix = x0 + 6
    iw = w - 12
    head = wrap(story["headline"], F(SERIF_B, 14), iw)
    assert len(head) <= 2, "small headline too long: #%d" % story["id"]
    y = draw_lines(d, ix, ky + 16, head, F(SERIF_B, 14), INK, 14)
    summ = wrap(story["summary"], F(SANS, 9), iw)
    assert len(summ) <= 2, "small summary too long: #%d (%d lines)" % (story["id"], len(summ))
    y = draw_lines(d, ix, y + 1, summ, F(SANS, 9), (40, 40, 38), 11)
    d.text((ix, y + 1), "(" + story["source"] + ")", font=F(SANS, 7), fill=MUTED)
    assert y + 9 <= y0 + h, "small card #%d overflows" % story["id"]
    return y0 + h


# ---------------------------------------------------------------- map

# Rough continent outlines in (lon, lat). Own coordinates, equirectangular.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-75, 62), (-80, 45),
     (-75, 35), (-80, 26), (-90, 21), (-97, 16), (-105, 20), (-115, 30), (-125, 40),
     (-125, 49), (-140, 60), (-155, 58), (-168, 66)],  # North America
    [(-55, 60), (-45, 60), (-40, 70), (-50, 76), (-60, 76), (-58, 70), (-55, 60)],  # Greenland
    [(-80, 10), (-75, 5), (-60, -5), (-50, -15), (-40, -25), (-50, -35), (-65, -45),
     (-72, -50), (-75, -35), (-72, -20), (-80, -5), (-80, 10)],  # South America
    [(-10, 36), (-5, 44), (0, 48), (5, 55), (10, 58), (18, 56), (25, 60), (30, 70),
     (45, 68), (60, 70), (75, 73), (90, 75), (110, 76), (130, 72), (150, 70), (170, 66),
     (178, 65), (170, 60), (160, 55), (150, 50), (140, 40), (130, 35), (120, 30),
     (110, 20), (100, 10), (95, 5), (90, 15), (80, 10), (75, 8), (70, 20), (60, 25),
     (55, 28), (50, 30), (45, 30), (40, 36), (35, 36), (30, 36), (25, 38), (20, 40),
     (15, 44), (10, 44), (5, 43), (0, 40), (-5, 36), (-10, 36)],  # Eurasia
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31), (35, 28), (40, 15),
     (48, 11), (51, 10), (45, 0), (40, -10), (35, -20), (30, -30), (20, -35), (15, -30),
     (12, -18), (13, -5), (10, 4), (5, 5), (-5, 5), (-10, 8), (-17, 15)],  # Africa
    [(95, 5), (100, 10), (105, 10), (110, 0), (115, -5), (120, -8), (130, -5), (135, -2),
     (140, -5), (130, 0), (120, 5), (110, 8), (100, 12), (95, 5)],  # SE Asia / Indonesia
    [(113, -22), (120, -20), (130, -12), (140, -15), (145, -20), (150, -25), (153, -32),
     (145, -38), (135, -35), (125, -32), (115, -32), (113, -22)],  # Australia
    [(130, 31), (135, 34), (140, 38), (142, 42), (140, 45), (138, 40), (133, 35), (130, 31)],  # Japan
    [(-5, 50), (-2, 53), (-4, 58), (-6, 55), (-5, 50)],  # UK
]

# Badge offsets (px) so the crowded Europe / Middle East pins stay distinct.
PIN_DX = {1: -14, 2: 16, 3: 0, 4: 24, 5: -14, 6: 0, 7: 0, 8: 14, 9: 0, 10: -16, 11: -16, 12: 0, 13: 0}
PIN_DY = {1: -10, 2: -12, 3: -14, 4: 6, 5: -10, 6: 10, 7: -10, 8: 14, 9: 10, 10: 6, 11: -8, 12: 12, 13: 12}


def draw_map(d, x0, y0, w, h, stories):
    """Dotted world map with numbered pins (dot = true location, badge offset)."""
    d.text((x0, y0), "WHERE IT HAPPENED — PINS MATCH STORY NUMBERS",
           font=F(SANS_B, 10), fill=INK)
    mx0, my0, mw, mh = x0, y0 + 18, w, h - 18
    d.rectangle([mx0, my0, mx0 + mw, my0 + mh], fill=(232, 230, 222))
    step = 5
    for gy in range(my0, my0 + mh, step):
        for gx in range(mx0, mx0 + mw, step):
            lon = -180 + (gx - mx0) / mw * 360
            lat = 85 - (gy - my0) / mh * 145
            if any(point_in_poly(lon, lat, poly) for poly in CONTINENTS):
                d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(70, 70, 65))
    for s in stories[:13]:
        lon, lat = s["lon"], s["lat"]
        px = mx0 + (lon + 180) / 360 * mw
        py = my0 + (85 - lat) / 145 * mh
        bx = px + PIN_DX[s["id"]]
        by = py + PIN_DY[s["id"]]
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=CRIMSON)
        if abs(bx - px) > 2 or abs(by - py) > 2:
            d.line([(px, py), (bx, by)], fill=CRIMSON, width=1)
        d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=CRIMSON)
        d.text((bx, by - 5), str(s["id"]), font=F(SANS_B, 8), fill=(255, 255, 255), anchor="ma")


def draw_wire(d, x0, y0, w, h, stories):
    """Two-column wire list, stories #14–#36, one line each."""
    d.text((x0, y0), "ALSO ON SUNDAY 22 NOVEMBER — 23 MORE STORIES",
           font=F(SANS_B, 10), fill=INK)
    wire = stories[13:]
    assert len(wire) == 23, "wire must be 23 stories"
    col_w = (w - 10) // 2
    wf = F(SANS, 9)
    y = y0 + 18
    pitch = 11
    for col in range(2):
        cx = x0 + col * (col_w + 10)
        cy = y
        for s in wire[col * 12:(col + 1) * 12]:
            text = "%d. %s (%s)" % (s["id"], s["headline"], s["source"])
            clip_text(d, text, wf, cx, cy, col_w, INK)
            cy += pitch
        assert cy <= y0 + h, "wire column %d overflows" % col


def draw_datecheck(d, data):
    y0, y1 = 912, 982
    d.rectangle([MARGIN, y0, W - MARGIN, y1], outline=CRIMSON, width=2)
    title = "DATE CHECK — LEFT OUT ON PURPOSE: FIRST REPORTED FRIDAY OR SATURDAY, SO NOT SHOWN AS SUNDAY'S NEWS"
    d.text((MARGIN + 8, y0 + 5), title, font=F(SANS_B, 10), fill=CRIMSON)
    items = data["datecheck"]
    assert len(items) == 10, "DATE CHECK must be 10 items"
    col_w = (CW - 16 - 10) // 2
    df = F(SANS, 9)
    for col in range(2):
        cx = MARGIN + 8 + col * (col_w + 10)
        cy = y0 + 18
        for item in items[col * 5:(col + 1) * 5]:
            d.text((cx, cy), "• " + item, font=df, fill=INK)
            cy += 10
        assert cy <= y1 - 2, "DATE CHECK column overflows"


def draw_footer(d, data):
    d.text((MARGIN, 986), "Sources: " + data["sources"], font=F(SANS, 8), fill=MUTED)
    d.text((MARGIN, 998), data["legend"], font=F(SANS, 8), fill=MUTED)
    right = "All 36 stories dated 22 NOV 2026"
    d.text((W - MARGIN - text_w(right, F(SANS_B, 8)), 998), right, font=F(SANS_B, 8), fill=INK)
    d.line([(MARGIN, 1014), (W - MARGIN, 1014)], fill=RULE, width=1)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "stories_20261122.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    stories = data["stories"]
    assert len(stories) == 36, "need 36 stories"
    assert [s["id"] for s in stories] == list(range(1, 37)), "story ids must be 1..36"
    assert sum(r["count"] for r in data["regions"]) == 36, "region counts must sum to 36"
    assert len(data["key"]) == 6, "key strip must be 6 numbers"
    assert len(data["utc"]) >= 6, "UTC strip needs 6 beats"

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    draw_masthead(d, data)
    draw_headline(d, data)
    draw_key_strip(d, data)
    draw_region_strip(d, data)
    draw_utc_strip(d, data)

    # 3 lead cards side by side
    lead_w = (CW - 2 * 8) // 3
    for i, s in enumerate(stories[:3]):
        draw_lead_card(d, MARGIN + i * (lead_w + 8), 234, lead_w, s)
    # 10 small cards, 2 rows of 5
    small_w = (CW - 4 * 8) // 5
    for row in range(2):
        for col in range(5):
            s = stories[3 + row * 5 + col]
            draw_small_card(d, MARGIN + col * (small_w + 8), 490 + row * 130, small_w, s)
    # map + wire
    draw_map(d, MARGIN, 750, 340, 158, stories)
    draw_wire(d, MARGIN + 352, 750, CW - 352, 158, stories)
    draw_datecheck(d, data)
    draw_footer(d, data)

    out = os.path.join(here, "entry.png")
    img.save(out, "PNG")
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
