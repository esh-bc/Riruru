#!/usr/bin/env python3
"""Shared utils — HTML style, flood, economy guards. # NEW
Benchmark: HTML (not MarkdownV2) to avoid parse-entity crashes.
All new replies use HTML + ff() + tree branches.
"""
import ast
import html
import math
import operator
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta

_SC = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ',
    'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴩ',
    'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ',
    '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻',
    '6': '𝟼', '7': '𝟽', '8': '𝟾', '9': '𝟿',
}

def ff(text: str) -> str:
    return ''.join(_SC.get(c.lower(), c) for c in str(text))

def esc(s) -> str:
    return html.escape(str(s), quote=False)

def mention_html(uid: int, name: str) -> str:
    return f'<a href="tg://user?id={int(uid)}">{esc(name or "User")}</a>'

def hcard(title: str, rows: list) -> str:
    """Quoted box card (house style): ✨ ╭── frame + ├── ⇛ rows."""
    out = [f'✨ ╭── [ 🌸 {ff(title)} ]', '│', '']
    for i, (emo, k, v) in enumerate(rows):
        branch = '└──' if i == len(rows) - 1 else '├──'
        out.append(f'{branch} {emo} ⇛ <b>{ff(k)}:</b> {v}')
    return '\n'.join(out)

def err_wrong(use: str) -> str:
    return f'ʙᴀᴋᴀ~ ʏᴏᴜ ᴅɪᴅ ɪᴛ ᴡʀᴏɴɢ 🙈 <code>{esc(use)}</code>'

def err_cool(mins: int = 0, secs: int = 0) -> str:
    if mins:
        t = f'{mins} ᴍᴏʀᴇ ᴍɪɴᴜᴛᴇꜱ'
    else:
        t = f'{secs} ꜱᴇᴄᴏɴᴅꜱ'
    return f'ꜱʟᴏᴡ ᴅᴏᴡɴ~ ʀɪʀᴜʀᴜ ɴᴇᴇᴅꜱ {t} ⏳'

# ── Flood (bugfix #2): 1s per-user silent ignore ──
_user_last_cmd: dict = {}

def flood_ok(uid: int, min_gap: float = 1.0) -> bool:
    now = time.time()
    last = _user_last_cmd.get(uid, 0)
    if now - last < min_gap:
        print(f"  FLOOD-BLOCK src uid={uid}")
        return False
    _user_last_cmd[uid] = now
    return True

# ── Time parse: 30m / 2h / 1d ──
def parse_dur(s: str):
    m = re.fullmatch(r'(\d+)([mhd])', (s or '').strip().lower())
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    if u == 'm':
        return timedelta(minutes=n), n * 60
    if u == 'h':
        return timedelta(hours=n), n * 3600
    return timedelta(days=n), n * 86400

def utcnow_iso() -> str:
    return datetime.utcnow().isoformat()

# ── Safe calc (ast, no eval) + Indian "X ka Y%" ──
_ALLOWED_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_ALLOWED_UN = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def safe_calc(expr: str):
    expr = (expr or '').strip()
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*ka\s*(\d+(?:\.\d+)?)\s*%', expr, re.I)
    if m:
        return float(m.group(1)) * float(m.group(2)) / 100.0
    expr = expr.replace('^', '**').replace('sqrt', 'math_sqrt')
    tree = ast.parse(expr, mode='eval')
    def _ev(n):
        if isinstance(n, ast.Expression):
            return _ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_BIN:
            l, r = _ev(n.left), _ev(n.right)
            if isinstance(n.op, ast.Div) and r == 0:
                raise ZeroDivisionError
            return _ALLOWED_BIN[type(n.op)](l, r)
        if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_UN:
            return _ALLOWED_UN[type(n.op)](_ev(n.operand))
        if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'math_sqrt' and len(n.args) == 1:
            v = _ev(n.args[0])
            if v < 0:
                raise ValueError('sqrt negative')
            return math.sqrt(v)
        raise ValueError('bad expr')
    val = _ev(tree)
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return round(val, 4) if isinstance(val, float) else val

MEDALS = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

def medal(i: int) -> str:
    return MEDALS[i] if 0 <= i < len(MEDALS) else f'{i+1}.'
