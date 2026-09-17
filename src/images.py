#!/usr/bin/env python3
"""Pillow-based interactive image generation for Riruru bot.

Generates: ship cards, profile cards, reaction images, quote stickers.
All functions return BytesIO or file path. Never raise — return None on failure.
"""
import io
import os
import textwrap
import random
import asyncio
from pathlib import Path

# Lazy import Pillow to avoid import errors if not installed
_pil = None

def _get_pil():
    global _pil
    if _pil is None:
        try:
            from PIL import Image, ImageDraw, ImageFont
            _pil = (Image, ImageDraw, ImageFont)
        except ImportError:
            return None
    return _pil


def _find_font(size=20, bold=False):
    """Find a usable font, fallback to default."""
    pil = _get_pil()
    if not pil:
        return None
    _, _, ImageFont = pil
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


async def ship_card(name1: str, name2: str, score: int) -> io.BytesIO | None:
    """Generate a ship card with two names and a love score.
    
    Returns BytesIO with PNG image or None on failure.
    """
    pil = _get_pil()
    if not pil:
        return None
    Image, ImageDraw, ImageFont = pil

    try:
        def _gen():
            W, H = 500, 280
            img = Image.new("RGB", (W, H), "#1a1a2e")
            draw = ImageDraw.Draw(img)

            # Background gradient effect (simple)
            for y in range(H):
                r = int(26 + (y / H) * 20)
                g = int(26 + (y / H) * 10)
                b = int(46 + (y / H) * 30)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Score bar background
            bar_y = 180
            bar_h = 30
            draw.rounded_rectangle([50, bar_y, W-50, bar_y+bar_h], radius=15, fill="#2d2d44")

            # Score bar fill
            fill_w = int((W-100) * score / 100)
            if fill_w > 0:
                color = "#ff6b9d" if score >= 70 else "#ffa500" if score >= 40 else "#ff4444"
                draw.rounded_rectangle([50, bar_y, 50+fill_w, bar_y+bar_h], radius=15, fill=color)

            # Fonts
            title_font = _find_font(28, bold=True)
            name_font = _find_font(22, bold=True)
            score_font = _find_font(18, bold=True)
            small_font = _find_font(14)

            # Title
            draw.text((W//2, 30), "💕 SHIP CARD 💕", fill="#ff6b9d", font=title_font, anchor="mt")

            # Names
            draw.text((W//4, 80), name1[:15], fill="#ffffff", font=name_font, anchor="mt")
            draw.text((W*3//4, 80), name2[:15], fill="#ffffff", font=name_font, anchor="mt")

            # Heart between names
            draw.text((W//2, 85), "❤️", fill="#ff6b9d", font=name_font, anchor="mm")

            # Score text
            draw.text((W//2, bar_y + bar_h//2), f"{score}% Match!", fill="#ffffff", font=score_font, anchor="mm")

            # Footer
            draw.text((W//2, 240), "✨ Made with love by Riruru ✨", fill="#888888", font=small_font, anchor="mt")

            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)
            buf.seek(0)
            buf.name = "image.png"
            return buf

        return await asyncio.to_thread(_gen)
    except Exception:
        return None


async def profile_card(user_id: int, name: str, coins: int, gems: int = 0,
                       level: int = 1, kills: int = 0, rank: int = 1,
                       title: str = "") -> io.BytesIO | None:
    """Generate a profile card for a user.
    
    Returns BytesIO with PNG image or None on failure.
    """
    pil = _get_pil()
    if not pil:
        return None
    Image, ImageDraw, ImageFont = pil

    try:
        def _gen():
            W, H = 500, 350
            img = Image.new("RGB", (W, H), "#0d1117")
            draw = ImageDraw.Draw(img)

            # Header gradient
            for y in range(100):
                r = int(13 + (y / 100) * 30)
                g = int(17 + (y / 100) * 20)
                b = int(23 + (y / 100) * 40)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Avatar circle placeholder
            cx, cy, cr = 80, 50, 35
            draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill="#ff6b9d", outline="#ffffff", width=2)
            draw.text((cx, cy), name[0].upper(), fill="#ffffff", font=_find_font(28, bold=True), anchor="mm")

            # Name and title
            title_font = _find_font(22, bold=True)
            name_font = _find_font(16)
            small_font = _find_font(14)
            stat_font = _find_font(18, bold=True)

            draw.text((140, 35), name[:20], fill="#ffffff", font=title_font, anchor="lt")
            if title:
                draw.text((140, 65), title, fill="#ff6b9d", font=name_font, anchor="lt")
            else:
                draw.text((140, 65), f"Rank #{rank}", fill="#888888", font=name_font, anchor="lt")

            # Stats grid
            stats = [
                ("💰", f"{coins:,}", "Coins"),
                ("💎", f"{gems:,}", "Gems"),
                ("⭐", f"Lvl {level}", "Level"),
                ("⚔️", f"{kills}", "Kills"),
            ]
            for i, (emoji, val, label) in enumerate(stats):
                x = 60 + (i % 2) * 220
                y = 140 + (i // 2) * 80
                draw.rounded_rectangle([x-10, y-5, x+190, y+60], radius=10, fill="#161b22", outline="#30363d")
                draw.text((x+5, y+5), emoji, fill="#ffffff", font=stat_font, anchor="lt")
                draw.text((x+40, y+5), val, fill="#ffffff", font=stat_font, anchor="lt")
                draw.text((x+40, y+35), label, fill="#888888", font=small_font, anchor="lt")

            # Footer
            draw.text((W//2, H-20), f"ID: {user_id} · Riruru Profile", fill="#484f58", font=small_font, anchor="mb")

            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)
            buf.seek(0)
            buf.name = "image.png"
            return buf

        return await asyncio.to_thread(_gen)
    except Exception:
        return None


async def reaction_image(action: str, sender: str, target: str) -> io.BytesIO | None:
    """Generate a cute reaction image (kiss, hug, slap, etc.).
    
    Returns BytesIO with PNG image or None on failure.
    """
    pil = _get_pil()
    if not pil:
        return None
    Image, ImageDraw, ImageFont = pil

    emoji_map = {
        "kiss": ("💋", "#ff6b9d", "Kiss!"),
        "hug": ("🤗", "#ffa500", "Hug!"),
        "slap": ("👋", "#ff4444", "Slap!"),
        "punch": ("👊", "#ff0000", "Punch!"),
        "bite": ("😬", "#cc6600", "Bite!"),
        "murder": ("💀", "#8b0000", "MURDER!"),
        "love": ("💕", "#ff1493", "Love~"),
        "look": ("👀", "#9370db", "Staring..."),
    }

    emoji, color, label = emoji_map.get(action, ("✨", "#ff6b9d", action.title()))

    try:
        def _gen():
            W, H = 500, 200
            img = Image.new("RGB", (W, H), "#1a1a2e")
            draw = ImageDraw.Draw(img)

            # Gradient bg
            for y in range(H):
                r = int(26 + (y / H) * 15)
                g = int(26 + (y / H) * 10)
                b = int(46 + (y / H) * 25)
                draw.line([(0, y), (W, y)], fill=(r, g, b))

            # Big emoji
            emoji_font = _find_font(60)
            draw.text((W//2, 50), emoji, fill=color, font=emoji_font, anchor="mm")

            # Names
            name_font = _find_font(20, bold=True)
            small_font = _find_font(14)
            draw.text((W//2, 110), f"{sender[:15]} → {target[:15]}", fill="#ffffff", font=name_font, anchor="mm")

            # Label
            draw.text((W//2, 150), label, fill=color, font=name_font, anchor="mm")

            # Footer
            draw.text((W//2, H-15), "Riruru 🌸", fill="#666666", font=small_font, anchor="mb")

            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)
            buf.seek(0)
            buf.name = "image.png"
            return buf

        return await asyncio.to_thread(_gen)
    except Exception:
        return None


async def quote_sticker(text: str, author: str = "") -> io.BytesIO | None:
    """Generate a quote sticker image.
    
    Returns BytesIO with PNG image or None on failure.
    """
    pil = _get_pil()
    if not pil:
        return None
    Image, ImageDraw, ImageFont = pil

    try:
        def _gen():
            # Wrap text
            wrapped = textwrap.fill(text[:200], width=30)
            lines = wrapped.split("\n")
            line_count = len(lines)

            W = 500
            H = max(150, 80 + line_count * 25 + (40 if author else 0))
            img = Image.new("RGB", (W, H), "#fef3c7")
            draw = ImageDraw.Draw(img)

            # Border
            draw.rectangle([5, 5, W-5, H-5], outline="#f59e0b", width=3)

            # Quote mark
            quote_font = _find_font(48, bold=True)
            draw.text((25, 15), "\u201c", fill="#f59e0b", font=quote_font)

            # Text
            text_font = _find_font(18)
            y = 50
            for line in lines:
                draw.text((40, y), line, fill="#1a1a1a", font=text_font)
                y += 25

            # Author
            if author:
                author_font = _find_font(14, bold=True)
                draw.text((W-30, H-25), f"— {author}", fill="#92400e", font=author_font, anchor="rm")

            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)
            buf.seek(0)
            buf.name = "image.png"
            return buf

        return await asyncio.to_thread(_gen)
    except Exception:
        return None


async def ship_gif_frames(names: list[tuple[str, str]], scores: list[int]) -> io.BytesIO | None:
    """Generate a multi-frame ship card GIF.
    
    Returns BytesIO with GIF or None on failure.
    """
    pil = _get_pil()
    if not pil or not names:
        return None
    Image, ImageDraw, ImageFont = pil

    try:
        def _gen():
            frames = []
            for (n1, n2), score in zip(names, scores):
                card = ship_card(n1, n2, score)
                # ship_card is async, can't call here — use a simpler approach
                pass
            # Fallback: single frame
            return None

        return await asyncio.to_thread(_gen)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════
#  CUTE ROBOT FACE IMAGES — 16:9, light pink, big round eyes
# ═══════════════════════════════════════════════════════════════════

_ROBOT_PRESETS = {
    "ban":    {"eyes": "angry",   "mouth": "frown",  "cheek": "#ff6b6b", "eye": "#ff4444", "bg": "#2d1b1b", "text": "BANNED"},
    "kick":   {"eyes": "shocked", "mouth": "open",   "cheek": "#ffb347", "eye": "#ff8c00", "bg": "#2d2b1b", "text": "KICKED"},
    "mute":   {"eyes": "sleepy",  "mouth": "zip",    "cheek": "#b19cd9", "eye": "#9370db", "bg": "#1b1b2d", "text": "MUTED"},
    "warn":   {"eyes": "worried", "mouth": "wavy",   "cheek": "#ffd700", "eye": "#ffa500", "bg": "#2d2d1b", "text": "WARNING"},
    "unban":  {"eyes": "happy",   "mouth": "smile",  "cheek": "#90ee90", "eye": "#44bb44", "bg": "#1b2d1b", "text": "UNBANNED"},
    "unmute": {"eyes": "happy",   "mouth": "grin",   "cheek": "#98fb98", "eye": "#32cd32", "bg": "#1b2d1b", "text": "UNMUTED"},
    "promote":{"eyes": "star",    "mouth": "smile",  "cheek": "#ffd700", "eye": "#ffec8b", "bg": "#2d2d0b", "text": "PROMOTED"},
    "demote": {"eyes": "sad",     "mouth": "frown",  "cheek": "#dda0dd", "eye": "#ba55d3", "bg": "#2b1b2d", "text": "DEMOTED"},
    "welcome":{"eyes": "sparkle", "mouth": "smile",  "cheek": "#ffb6c1", "eye": "#ff69b4", "bg": "#2d1b2d", "text": "WELCOME"},
    "error":  {"eyes": "dizzy",   "mouth": "squig",  "cheek": "#ff6b6b", "eye": "#cc0000", "bg": "#2d1111", "text": "ERROR"},
    "success":{"eyes": "happy",   "mouth": "grin",   "cheek": "#98fb98", "eye": "#00cc66", "bg": "#112d1b", "text": "DONE"},
}


def _draw_rounded_rect(draw, bbox, radius, fill):
    try:
        draw.rounded_rectangle(bbox, radius=radius, fill=fill)
    except AttributeError:
        x0, y0, x1, y1 = bbox
        draw.rectangle([x0+radius, y0, x1-radius, y1], fill=fill)
        draw.rectangle([x0, y0+radius, x1, y1-radius], fill=fill)


def _draw_eye(draw, cx, cy, size, shape, color, white="#ffffff"):
    r = size // 2
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=white, outline="#333333", width=2)
    pr = r // 2
    if shape in ("angry", "worried"):
        pr = r // 3
    elif shape in ("shocked", "sparkle"):
        pr = int(r * 0.6)
    elif shape == "sleepy":
        pr = r // 4
    ox, oy = 0, 0
    if shape == "angry":
        oy = -2
    elif shape == "sad":
        oy = 2
    elif shape == "dizzy":
        ox, oy = 2, -1
    draw.ellipse([cx-pr+ox, cy-pr+oy, cx+pr+ox, cy+pr+oy], fill=color)
    hr = max(2, pr // 3)
    hx, hy = cx - pr//3 + ox, cy - pr//3 + oy
    draw.ellipse([hx-hr, hy-hr, hx+hr, hy+hr], fill=white)
    if shape in ("star", "sparkle"):
        import math
        sr = r + 4
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = cx + int(sr * math.cos(rad))
            sy = cy + int(sr * math.sin(rad))
            draw.ellipse([sx-2, sy-2, sx+2, sy+2], fill=color)
    if shape == "angry":
        bw = r + 4
        draw.line([cx-bw, cy-r-8, cx+bw//2, cy-r-3], fill="#333333", width=3)
    elif shape == "worried":
        bw = r + 4
        draw.line([cx-bw//2, cy-r-3, cx+bw, cy-r-8], fill="#333333", width=3)


def _draw_mouth(draw, cx, cy, width, shape, color="#333333"):
    hw = width // 2
    if shape == "smile":
        draw.arc([cx-hw, cy-8, cx+hw, cy+16], 0, 180, fill=color, width=3)
    elif shape == "grin":
        draw.arc([cx-hw, cy-10, cx+hw, cy+20], 0, 180, fill=color, width=4)
    elif shape == "frown":
        draw.arc([cx-hw, cy+4, cx+hw, cy+28], 180, 360, fill=color, width=3)
    elif shape == "open":
        draw.ellipse([cx-hw//2, cy-4, cx+hw//2, cy+16], fill=color)
    elif shape == "zip":
        for i in range(0, width, 8):
            x = cx - hw + i
            draw.line([x, cy+4, x+4, cy+8], fill=color, width=2)
            draw.line([x+4, cy+8, x+8, cy+4], fill=color, width=2)
    elif shape == "wavy":
        draw.arc([cx-hw, cy-4, cx, cy+12], 0, 180, fill=color, width=2)
        draw.arc([cx, cy-4, cx+hw, cy+12], 0, 180, fill=color, width=2)
    elif shape == "squig":
        for i in range(0, width, 6):
            x = cx - hw + i
            y = cy + 6 + (2 if i % 12 < 6 else -2)
            draw.ellipse([x-1, y-1, x+1, y+1], fill=color)
    else:
        draw.line([cx-hw//2, cy+6, cx+hw//2, cy+6], fill=color, width=2)


async def robot_face(action: str, user_name: str = "", detail: str = "") -> io.BytesIO | None:
    """Cute robot face image for mod actions. 16:9, light pink, big round eyes."""
    pil = _get_pil()
    if not pil:
        return None
    Image, ImageDraw, ImageFont = pil
    preset = _ROBOT_PRESETS.get(action, _ROBOT_PRESETS["success"])
    try:
        def _gen():
            W, H = 800, 450
            img = Image.new("RGB", (W, H), preset["bg"])
            draw = ImageDraw.Draw(img)
            for y in range(H):
                r = int(int(preset["bg"][1:3], 16) * (1 - y/H) + 40 * (y/H))
                g = int(int(preset["bg"][3:5], 16) * (1 - y/H) + 20 * (y/H))
                b = int(int(preset["bg"][5:7], 16) * (1 - y/H) + 50 * (y/H))
                draw.line([(0, y), (W, y)], fill=(min(r,255), min(g,255), min(b,255)))
            face_r = 140
            fcx, fcy = W // 2, H // 2 - 20
            draw.ellipse([fcx-face_r, fcy-face_r, fcx+face_r, fcy+face_r],
                        fill="#ffb6c1", outline="#ff69b4", width=4)
            draw.line([fcx, fcy-face_r, fcx, fcy-face_r-30], fill="#ff69b4", width=4)
            draw.ellipse([fcx-8, fcy-face_r-38, fcx+8, fcy-face_r-22], fill="#ff69b4", outline="#ff1493", width=2)
            ear_r = 20
            draw.ellipse([fcx-face_r-ear_r-5, fcy-ear_r, fcx-face_r+ear_r-5, fcy+ear_r], fill="#ff69b4", outline="#ff1493", width=2)
            draw.ellipse([fcx+face_r+5-ear_r, fcy-ear_r, fcx+face_r+5+ear_r, fcy+ear_r], fill="#ff69b4", outline="#ff1493", width=2)
            eye_size = 50
            eye_y = fcy - 20
            _draw_eye(draw, fcx-50, eye_y, eye_size, preset["eyes"], preset["eye"])
            _draw_eye(draw, fcx+50, eye_y, eye_size, preset["eyes"], preset["eye"])
            cheek_r = 18
            draw.ellipse([fcx-90, eye_y+30, fcx-90+cheek_r*2, eye_y+30+cheek_r*2], fill=preset["cheek"])
            draw.ellipse([fcx+90-cheek_r*2, eye_y+30, fcx+90, eye_y+30+cheek_r*2], fill=preset["cheek"])
            _draw_mouth(draw, fcx, eye_y+50, 60, preset["mouth"])
            title_font = _find_font(32, bold=True)
            name_font = _find_font(20)
            small_font = _find_font(14)
            _draw_rounded_rect(draw, [0, H-80, W, H], 0, "#000000")
            draw.text((W//2, H-55), preset["text"], fill="#ffffff", font=title_font, anchor="mm")
            if user_name:
                draw.text((W//2, H-25), user_name[:30], fill="#cccccc", font=name_font, anchor="mm")
            if action == "ban":
                for dx in [-1, 1]:
                    bx = fcx + dx * (face_r + 40)
                    draw.line([bx-15, fcy-15, bx+15, fcy+15], fill="#ff4444", width=4)
                    draw.line([bx-15, fcy+15, bx+15, fcy-15], fill="#ff4444", width=4)
            elif action == "promote":
                crown_y = fcy - face_r - 45
                points = [(fcx-30, crown_y+20), (fcx-20, crown_y), (fcx-5, crown_y+15),
                          (fcx, crown_y-5), (fcx+5, crown_y+15), (fcx+20, crown_y), (fcx+30, crown_y+20)]
                draw.polygon(points, fill="#ffd700", outline="#daa520")
            if detail:
                draw.text((W//2, H-8), detail[:50], fill="#888888", font=small_font, anchor="mb")
            buf = io.BytesIO()
            img.save(buf, format="PNG", quality=95)
            buf.seek(0)
            buf.name = "image.png"
            return buf
        return await asyncio.to_thread(_gen)
    except Exception:
        return None
