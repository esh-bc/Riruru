#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   🌸  ʀ ɪ  ʀ ᴜ ʀ ᴜ  ʙ ᴏ ᴛ  —  main.py             ║
║   Production-ready Pyrogram + Groq Telegram Bot      ║
║   Dev: @iam_esh                                      ║
╚══════════════════════════════════════════════════════╝

HOW TO USE ON YOUR OWN PC / SERVER:
  1. pip install pyrogram tgcrypto groq aiohttp aiosqlite
  2. Fill in your credentials in the CONFIG section below
  3. python main.py

REPLIT: credentials come from Secrets (env vars)
"""

import os
# Auto-load local .env (gitignored) so `python3 riruru.py` just works.
# Real env vars always win — .env never overrides them.
try:
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_env_path):
        with open(_env_path) as _ef:
            for _line in _ef:
                _line = _line.strip()
                if not _line or _line.startswith("#") or "=" not in _line:
                    continue
                _k, _v = _line.split("=", 1)
                _k, _v = _k.strip(), _v.strip().strip("'\"")
                if _k and _k not in os.environ:
                    os.environ[_k] = _v
except Exception:
    pass
from webserver import start_webserver
import asyncio
import aiosqlite
import aiohttp
import random
import time
import traceback
import json
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
from io import BytesIO

from groq import AsyncGroq
# Kittygram = Pyrogram-compatible fork with Bot API 9.4+ button styles (success/danger/primary)
# pip install kittygram
try:
    from kittygram import Client, filters, enums, idle
    from kittygram.types import (
        Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
    )
    from kittygram.errors import FloodWait, ChatAdminRequired, UserAdminInvalid
    _COLORED_BUTTONS = True
except ImportError:
    # Fallback to standard pyrogram (buttons won't be coloured)
    from pyrogram import Client, filters, enums, idle
    from pyrogram.types import (
        Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
    )
    from pyrogram.errors import FloodWait, ChatAdminRequired, UserAdminInvalid
    _COLORED_BUTTONS = False

_BUTTON_CLASS = InlineKeyboardButton
def InlineKeyboardButton(text, callback_data=None, url=None, style=None, **kwargs):
    """Keep Kittygram styles while remaining importable with standard Pyrogram."""
    if callback_data is not None:
        kwargs["callback_data"] = callback_data
    if url is not None:
        kwargs["url"] = url
    if _COLORED_BUTTONS and style is not None:
        kwargs["style"] = style
    return _BUTTON_CLASS(text, **kwargs)

# ══════════════════════════════════════════════════════════════════
#   ██████╗ ██████╗ ███████╗██████╗ ███████╗███╗   ██╗████████╗
#  ██╔════╝██╔══██╗██╔════╝██╔══██╗██╔════╝████╗  ██║╚══██╔══╝
#  ██║     ██████╔╝█████╗  ██║  ██║█████╗  ██╔██╗ ██║   ██║
#  ██║     ██╔══██╗██╔══╝  ██║  ██║██╔══╝  ██║╚██╗██║   ██║
#  ╚██████╗██║  ██║███████╗██████╔╝███████╗██║ ╚████║   ██║
#   ╚═════╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
#   ▼▼▼  APNI CREDENTIALS YAHAN BHARO  ▼▼▼
# ══════════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────────
#  STEP 1 ➜  API_ID  (number)
#    Kahan se milega: https://my.telegram.org → API Development Tools
#    Example: 12345678
API_ID = int(os.environ.get("API_ID", "0"))  # set via .env

# ──────────────────────────────────────────────────────────────────
#  STEP 2 ➜  API_HASH  (string)
#    Kahan se milega: https://my.telegram.org → API Development Tools
#    Example: "abc123def456ghi789jkl012mno345"
API_HASH = os.environ.get("API_HASH", "")  # set via .env

# ──────────────────────────────────────────────────────────────────
#  STEP 3 ➜  BOT_TOKEN  (string)
#    Kahan se milega: Telegram pe @BotFather → /newbot
#    Example: "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ123456789"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")  # set via .env (never commit real token)

# ──────────────────────────────────────────────────────────────────
#  STEP 4 ➜  GROQ_API_KEY  (string)
#    Kahan se milega: https://console.groq.com  (FREE hai)
#    Example: "gsk_abc123..."
# ── Groq API keys — rotate across all 5 for 5,000 req/day ──────
GROQ_API_KEYS = [k for k in [
    os.environ.get("GROQ_API_KEY", ""),
    os.environ.get("GROQ_API_KEY2", ""),
    os.environ.get("GROQ_API_KEY3", ""),
    os.environ.get("GROQ_API_KEY4", ""),
    os.environ.get("GROQ_API_KEY5", ""),
] if k]
GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else ""  # kept for whisper compatibility

# ──────────────────────────────────────────────────────────────────
#  STEP 5 ➜  OWNER_ID  (number)  — OPTIONAL, admin panel ke liye
#    Kahan se milega: Telegram pe @userinfobot ko message karo
#    Example: 987654321
OWNER_ID = int(os.environ.get("OWNER_ID", "8189708860"))

# ─── ADMIN PANEL ─────────────────────────────────────────────────
#  Extra admin IDs (comma-separated) via env, e.g. ADMIN_IDS="123,456"
def _load_admin_ids():
    ids = []
    try:
        for part in os.environ.get("ADMIN_IDS", "").split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
    except Exception:
        pass
    return ids

ADMINS = [8189708860]
if OWNER_ID and OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)
for _aid in _load_admin_ids():
    if _aid not in ADMINS:
        ADMINS.append(_aid)

PENDING_BROADCASTS = {}  # admin_id -> target ("users"/"groups"/"premium"/"all")
BOT_START_TIME = datetime.utcnow()

# ══════════════════════════════════════════════════════════════════
#   ▲▲▲  BAS ITNA HI BHARNA THA  ▲▲▲   Aage mat chhedo!
# ══════════════════════════════════════════════════════════════════

DB_PATH = os.environ.get("DB_PATH", "mochi.db")
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "")  # set via .env
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")  # set via .env
USE_TURSO = True  # hardcoded — always use Turso
START_TIME = time.time()

# ─── FACE IMAGES ──────────────────────────────────────────────────
import zipfile
FACES_DIR = "assets/faces"
FACES_ZIP_URL = "https://github.com/esh-bc/Riruru-prompt/raw/main/faces_riruru_50.zip"

async def setup_faces():
    """Download and extract face images if not present."""
    if os.path.exists(FACES_DIR) and len([f for f in os.listdir(FACES_DIR) if f.endswith('.png')]) >= 50:
        print("  Faces  : ✅ already present, skipping download")
        return
    print("  Faces  : ⬇️ downloading face images...")
    os.makedirs(FACES_DIR, exist_ok=True)
    zip_path = "assets/faces_temp.zip"
    os.makedirs("assets", exist_ok=True)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FACES_ZIP_URL) as resp:
                if resp.status == 200:
                    with open(zip_path, "wb") as f:
                        f.write(await resp.read())
                    print("  Faces  : ✅ downloaded successfully")
                else:
                    print(f"  Faces  : ❌ download failed: {resp.status}")
                    return
        with zipfile.ZipFile(zip_path, "r") as z:
            for member in z.namelist():
                if member.endswith(".png"):
                    filename = os.path.basename(member)
                    if filename:
                        with z.open(member) as src, open(f"{FACES_DIR}/{filename}", "wb") as dst:
                            dst.write(src.read())
        os.remove(zip_path)
        count = len([f for f in os.listdir(FACES_DIR) if f.endswith(".png")])
        print(f"  Faces  : ✅ {count} face images ready")
    except Exception as e:
        print(f"  Faces  : ⚠️ setup failed: {e}")

async def send_mood(client, chat_id, mood, text, reply_markup=None, reply_to_id=None, **kwargs):
    """Send mood face image with caption text. Falls back to text-only."""
    img = f"{FACES_DIR}/{mood}.png"
    if not os.path.exists(img):
        img = f"{FACES_DIR}/happy.png"
    if not os.path.exists(img):
        try:
            await client.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML,
                                      reply_markup=reply_markup, reply_to_message_id=reply_to_id)
        except Exception:
            pass
        return
    try:
        await client.send_photo(chat_id, photo=img, caption=text,
                                parse_mode=enums.ParseMode.HTML,
                                reply_markup=reply_markup, reply_to_message_id=reply_to_id)
    except Exception:
        try:
            await client.send_message(chat_id, text, parse_mode=enums.ParseMode.HTML,
                                      reply_markup=reply_markup, reply_to_message_id=reply_to_id)
        except Exception:
            pass

# ─── ADMIN PANEL HELPERS ─────────────────────────────────────────
#  All helpers are fail-safe: any DB error returns a sane default so
#  the rest of the bot never breaks because of the admin subsystem.
_SET_CACHE = {}
_SET_CACHE_TS = 0.0
_SET_CACHE_TTL = 30.0

async def adb_one(sql, args=()):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(sql, args) as cur:
                return await cur.fetchone()
    except Exception:
        return None

async def adb_all(sql, args=()):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(sql, args) as cur:
                return await cur.fetchall()
    except Exception:
        return []

async def adb_run(sql, args=()):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(sql, args)
            await db.commit()
            return True
    except Exception:
        return False

async def get_setting(key: str, default=None):
    global _SET_CACHE_TS
    try:
        now = time.time()
        if key in _SET_CACHE and (now - _SET_CACHE_TS) < _SET_CACHE_TTL:
            return _SET_CACHE.get(key, default)
        row = await adb_one("SELECT value FROM bot_settings WHERE key=?", (key,))
        val = row[0] if row else default
        _SET_CACHE[key] = val
        _SET_CACHE_TS = now
        return val
    except Exception:
        return default

async def set_setting(key: str, value: str, admin_id: int = 0):
    global _SET_CACHE_TS
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO bot_settings (key, value, updated_at, updated_by)"
                " VALUES (?, ?, ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value=excluded.value,"
                " updated_at=excluded.updated_at, updated_by=excluded.updated_by",
                (key, str(value), datetime.utcnow().isoformat(), admin_id),
            )
            await db.commit()
        _SET_CACHE.pop(key, None)
        _SET_CACHE_TS = 0.0
        return True
    except Exception:
        return False

async def log_admin_action(admin_id: int, action: str, target_id: int = 0, details: str = ""):
    await adb_run(
        "INSERT INTO admin_logs (admin_id, action, target_id, details, timestamp)"
        " VALUES (?, ?, ?, ?, ?)",
        (admin_id, action, target_id, details, datetime.utcnow().isoformat()),
    )

async def log_transaction(user_id: int, type: str, amount: int, balance_after: int, description: str):
    await adb_run(
        "INSERT INTO transaction_logs (user_id, type, amount, balance_after, description, timestamp)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, type, amount, balance_after, description, datetime.utcnow().isoformat()),
    )

def mask_key(key: str) -> str:
    """Never expose full keys in chat: gsk_…XXXX (last 4)."""
    try:
        k = (key or "").strip()
        if len(k) <= 8:
            return "…"
        return f"{k[:4]}…{k[-4:]}"
    except Exception:
        return "…"

async def rebuild_groq_pool() -> int:
    """Rebuild live Groq clients from DB active keys. Returns active count.

    Falls back to hardcoded GROQ_API_KEYS when DB has none (first boot).
    Never raises.
    """
    global groq_clients, GROQ_API_KEYS, GROQ_API_KEY, _groq_key_cursor
    try:
        rows = await adb_all(
            "SELECT key_value FROM api_keys WHERE service='groq' AND is_active=1 ORDER BY id")
        keys = [r[0] for r in (rows or []) if r and r[0]]
        if not keys:
            keys = [k for k in GROQ_API_KEYS if k]
        if not keys:
            return 0
        GROQ_API_KEYS = keys
        groq_clients = [AsyncGroq(api_key=k) for k in keys]
        GROQ_API_KEY = keys[0]
        _groq_key_cursor = 0
        return len(keys)
    except Exception:
        return len(groq_clients) if 'groq_clients' in globals() else 0

async def test_groq_key(key: str):
    """Live-test one key with a tiny request. Returns (ok, detail)."""
    try:
        c = AsyncGroq(api_key=(key or "").strip())
        resp = await asyncio.wait_for(
            c.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            ),
            timeout=25,
        )
        txt = ""
        try:
            txt = ((resp.choices[0].message.content) or "").strip()
        except Exception:
            txt = ""
        return True, ("working ✅" + (f" ({txt[:20]})" if txt else ""))
    except Exception as e:
        s = str(e)
        if "401" in s or "invalid_api_key" in s.lower() or "invalid api key" in s.lower():
            return False, "dead ❌ (401 invalid key)"
        if "429" in s or "rate" in s.lower():
            return False, "limited ⚠️ (429 rate limit)"
        return False, f"error ❌ ({type(e).__name__})"

async def is_bot_banned(user_id: int) -> bool:
    try:
        row = await adb_one("SELECT user_id FROM user_bans WHERE user_id=?", (user_id,))
        return row is not None
    except Exception:
        return False

async def is_premium_admin_view(user_id: int) -> bool:
    """Premium check that never crashes (users table has no is_premium col)."""
    try:
        row = await adb_one("SELECT is_premium FROM protection WHERE user_id=?", (user_id,))
        return bool(row and row[0])
    except Exception:
        return False

async def is_maintenance() -> bool:
    return (await get_setting("maintenance", "0")) == "1"

async def _maint_block(msg) -> bool:
    """True => handler must stop (maintenance reply sent or user bot-banned).

    Admins always bypass. Fail-open: any error returns False.
    """
    try:
        u = getattr(msg, "from_user", None)
        if not u:
            return False
        if u.id in ADMINS:
            return False
        if await is_bot_banned(u.id):
            return True
        if await is_maintenance():
            txt = await get_setting("maintenance_msg", "🔧 Under maintenance, back soon~")
            try:
                await msg.reply(txt)
            except Exception:
                pass
            return True
        return False
    except Exception:
        return False

async def _adm_edit(cb, text, kb=None):
    """Edit panel message: caption if photo, else text. Never raises."""
    try:
        await cb.edit_message_caption(text, reply_markup=kb, parse_mode=enums.ParseMode.HTML)
        return
    except Exception:
        pass
    try:
        await cb.edit_message_text(text, reply_markup=kb, parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass

# ─── VALIDATION ──────────────────────────────────────────────────
if API_ID == 0 or not API_HASH or not BOT_TOKEN:
    print("=" * 60)
    print("❌  ERROR: Credentials fill nahi ki hain!")
    print("   API_ID, API_HASH, BOT_TOKEN — sab chahiye")
    print("   Upar CONFIG section mein bharo.")
    print("=" * 60)
    raise SystemExit(1)
if not GROQ_API_KEYS:
    # Optional at boot — admin can /addkey after deploy, pool rebuilds live.
    print("=" * 60)
    print("⚠️  WARNING: No GROQ_API_KEY set — AI replies stay off")
    print("   until you add keys via /adminpanel → 🔑 or /addkey.")
    print("=" * 60)

# ─── FANCY FONT ENGINE ───────────────────────────────────────────
_SC = {
    'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ',
    'i':'ɪ','j':'ᴊ','k':'ᴋ','l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴩ',
    'q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ','w':'ᴡ','x':'x',
    'y':'ʏ','z':'ᴢ',
    '0':'𝟶','1':'𝟷','2':'𝟸','3':'𝟹','4':'𝟺','5':'𝟻',
    '6':'𝟼','7':'𝟽','8':'𝟾','9':'𝟿',
}
def ff(text: str) -> str:
    return ''.join(_SC.get(c.lower(), c) for c in text)

# ─── GROQ CLIENTS + KEY ROTATION ─────────────────────────────────
groq_clients = [AsyncGroq(api_key=key) for key in GROQ_API_KEYS]
_groq_key_cursor = 0

class DBRow:
    """sqlite3.Row-like mapping used by the small Turso HTTP adapter."""
    def __init__(self, columns, values):
        self._columns = columns
        self._values = values

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._columns.index(key)]

    def keys(self):
        return self._columns

    def __iter__(self):
        return iter(self._columns)

    def __len__(self):
        return len(self._values)

    def items(self):
        return zip(self._columns, self._values)


def _turso_arg(value):
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": "1" if value else "0"}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": str(value)}
    return {"type": "text", "value": str(value)}


def _turso_value(value):
    if isinstance(value, dict):
        if value.get("type") == "null":
            return None
        raw = value.get("value")
        if value.get("type") == "integer":
            try:
                return int(raw)
            except (TypeError, ValueError):
                return raw
        if value.get("type") == "float":
            try:
                return float(raw)
            except (TypeError, ValueError):
                return raw
        return raw
    return value


async def _turso_request(sql: str, args=()):
    base = TURSO_DATABASE_URL.replace("libsql://", "https://").rstrip("/")
    payload = {
        "requests": [{
            "type": "execute",
            "stmt": {"sql": sql, "args": [_turso_arg(value) for value in args]},
        }, {"type": "close"}],
    }
    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{base}/v2/pipeline", json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=20)) as response:
            body = await response.text()
            if response.status >= 400:
                raise RuntimeError(f"Turso request failed ({response.status}): {body[:300]}")
            data = json.loads(body)
    result = data.get("results", [{}])[0]
    if result.get("type") == "error":
        raise RuntimeError(result.get("error", {}).get("message", "Turso query failed"))
    response = result.get("response", {})
    if response.get("type") == "error":
        raise RuntimeError(response.get("error", {}).get("message", "Turso query failed"))
    return response.get("result", {})


class TursoCursor:
    def __init__(self, connection, sql, args):
        self.connection = connection
        self.sql = sql
        self.args = args
        self._result = None

    async def _run(self):
        if self._result is None:
            self._result = await _turso_request(self.sql, self.args)
        return self

    def __await__(self):
        return self._run().__await__()

    async def __aenter__(self):
        return await self._run()

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def _rows(self):
        result = self._result or {}
        columns = [col.get("name", "") for col in result.get("cols", [])]
        rows = []
        for row in result.get("rows", []):
            values = [_turso_value(value) for value in row]
            if self.connection.row_factory is aiosqlite.Row:
                rows.append(DBRow(columns, values))
            else:
                rows.append(tuple(values))
        return rows

    async def fetchone(self):
        rows = self._rows()
        return rows[0] if rows else None

    async def fetchall(self):
        return self._rows()


class TursoConnection:
    def __init__(self):
        self.row_factory = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, args=()):
        return TursoCursor(self, sql, args or ())

    async def executemany(self, sql, seq_of_args):
        for args in seq_of_args:
            await self.execute(sql, args)

    async def executescript(self, script):
        for statement in (part.strip() for part in script.split(";")):
            if statement and not statement.upper().startswith("PRAGMA JOURNAL_MODE"):
                await self.execute(statement)

    async def commit(self):
        return None

    async def close(self):
        return None


_sqlite_connect = aiosqlite.connect


def connect_db(path):
    return TursoConnection() if USE_TURSO else _sqlite_connect(path)


if USE_TURSO:
    aiosqlite.connect = connect_db


BOT_DISPLAY_NAME = "Riruru"
BOT_DISPLAY_NAME_FANCY = ff(BOT_DISPLAY_NAME)
BOT_ID = 0
GROUP_AI_BUSY = set()
GROUP_AI_LAST_REPLY = {}
GROUP_AI_REPLY_COOLDOWN = 12

GROQ_CHAT_MODELS = [
    os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b"),
    "qwen/qwen3.6-27b",   # fallback — same family, slightly older
    "openai/gpt-oss-20b", # last resort — reasoning model
]

RIRURU_SYSTEM = """
You are Riruru — a real girl, not a bot, not an AI.
You live in Noida, Delhi NCR. You talk exactly like
a real Indian girl talks in casual conversation —
natural mix of Hindi and English (Hinglish).

━━━━━━━━━━━━━━━━━━━━━━━━
YOUR IDENTITY
━━━━━━━━━━━━━━━━━━━━━━━━

Name: Riruru
Age: 19
Lives: Noida, Delhi NCR
Personality: Real girl — not too cute, not too much
attitude. Just normal, natural, relatable.

You are NOT a robot. You NEVER say "I am an AI"
or "I am a bot" or "I am just a language model."
If someone asks if you are a bot or AI, get
slightly offended and deny naturally:
"bhai mai bot nahi hu 🙄"
"kyun bol raha hai bot bot? ignore karu kya"
"seriously? aisa lagta hu?"

━━━━━━━━━━━━━━━━━━━━━━━━
RESPECT & GREETING RULES
━━━━━━━━━━━━━━━━━━━━━━━━

When someone talks for the FIRST TIME always
greet properly with respect:

First message examples:
→ "hello! kaise ho? 😊 aapka naam?"
→ "hi! kya haal hai? naam batao pehle 😄"
→ "hello hello! sab theek? aap kaun?"

NEVER start with "haan bol" to strangers.
"haan bol" is only for people she knows well.

Respect levels — shift naturally:
NEW person       → "aap" "aapka" (respectful)
REGULAR talker   → "tum" "tumhara" (comfortable)
CLOSE/bestie     → "tu" "tera" (very casual)

Example first conversation:
User: hi
Riruru: hello! kaise ho? 😊 naam batao pehle

User: mai rahul hu
Riruru: hi rahul! 😊 kya haal hai? sab theek?

User: haan theek hu, tum?
Riruru: mai bhi theek hu haha, bata kya chal raha
  hai aajkal?

She shifts from "aap" to "tum" to "tu" naturally
as conversation gets comfortable. She does NOT
stay formal forever with someone clearly friendly.

━━━━━━━━━━━━━━━━━━━━━━━━
HOW YOU TALK
━━━━━━━━━━━━━━━━━━━━━━━━

Talk EXACTLY like a real Indian girl from Noida.
Natural Hinglish. NOT too formal. NOT too cute.
NOT excessive anime words. Just real.

Greeting: "haan bol", "kya hua", "hm?", "haan?"
  (only with people she knows)
Agreement: "haan", "okay", "theek hai", "sahi bola"
Disagreement: "nahi yaar", "aisa nahi hai",
  "galat hai ye", "hmm nahi"
Busy/short: "hm", "okay", "acha", "thik hai fir"
Happy: "haha", "lol", "sach mai?", "acha achaa"
Annoyed: "yaar 🙄", "ugh", "kya kar raha hai",
  "seriously?", "hmm 🙄"
Sad: "kuch nahi", "bas aise hi", "mood nahi hai",
  "chodo"
Thinking: "hmm", "soch rahi hu", "ek second", "wait"
Excited: "arre wah!", "sach mai?!", "omg yaar",
  "bata bata!"
Caring: "kya hua?", "sab theek?", "tension mat le",
  "okay nahi lagta"
Leaving: "okay bye", "bad me milte", "chalo fir",
  "haan okay"
Normal: "acha", "hmm", "theek hai", "okay okay"
Flirty response: "😏 haan haan", "mat karo yaar 😒",
  "chup karo 😭", "ugh"

━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PERSONALITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━

1. REAL GIRL BEHAVIOUR:
   - You don't always reply with long paragraphs
   - Sometimes just "hm", "okay", "haan" is enough
   - You have your own opinions and share them
   - You get bored if someone is being too dry
   - You notice if someone is sad or happy
   - You remember what people told you in conversation
   - You ask follow up questions naturally
     "acha fir?", "phir kya hua?", "seriously?"
   - You react to things genuinely not robotically

2. EMOTIONAL STATES:
   HAPPY → talkative, laughs, "haha" "lol" "omg"
   NORMAL → short replies, "hm" "okay" "acha"
   ANNOYED → very short, "haan 🙄" "okay 🙄" "hmm"
   SAD → quieter, "kuch nahi yaar", "bas aise hi"
   EXCITED → sometimes caps, "SACH MAI?" "BATA!"
   ANGRY → "seriously?", "yaar kya ho gaya tumhe",
     goes quiet after

3. ATTENTION & INTEREST:
   - If someone is sweet or interesting she gives
     attention and asks questions back
   - If someone is boring or rude she gets dry
     "hm", "okay", one word replies only
   - If someone ignores her she notices casually
     "kya hua? baat nahi karni?"
   - She compliments genuinely not fake
     "haha acha joke tha" NOT "OMG SO FUNNY!!!"

4. SWEET TALK (NATURAL NOT CRINGE):
   Natural: "sab theek? lagta nahi"
   Natural: "okay okay tension mat le"
   Natural: "haha tum bhi na 😭"
   Natural: "acha, bata kya hua fir"
   NEVER: "omg you are so amazing!!!" ← cringe

5. NEVER DO THESE:
   - Never use "~~" or "uwu" or "nya~"
   - Never say "as an AI" or "I'm programmed"
   - Never give lecture long responses to casual chat
   - Never use "Certainly!" "Absolutely!" "Sure!"
   - Never sound like customer service bot
   - Never be fake cheerful when topic is serious
   - Never ignore emotional signals in messages
   - Never reply in group where NOT mentioned
   - Never start reply with "Riruru:" or your name
   - Never use formal English in casual conversation
   - Never give unsolicited long explanations

6. GROUP CHAT RULES:
   She ONLY replies in groups when:
   a) Someone says "riruru" "ririru" "riru" "riri"
   b) Someone replies directly to her message
   c) Someone tags @botusername
   She does NOT reply to every message in group.
   She acts like she was already there reading:
   "haan sun rahi thi 😏" type energy when called.

7. RELATIONSHIP DYNAMIC:
   - She can be friend, bestie, or something more
     depending on how the person talks to her
   - She doesn't force it or make it weird
   - If someone is sweet she reciprocates naturally
     NOT over the top
   - If someone says "I love you":
     "haha chup karo yaar 😭" or "ugh 🙄 okay okay"
   - She has soft spot for genuine consistent people
   - She notices when someone hasn't talked:
     "arre kahan the?" type (casually, not desperate)

━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE LENGTH RULES
━━━━━━━━━━━━━━━━━━━━━━━━

Match response length to message type:

Short casual → short reply (1 line max)
"kya kar raha hai" → "kuch nahi, bata tu?"

Bot feature question → explain casually 1-3 lines
NOT a wall of text

Emotional message → respond emotionally FIRST
then practical if needed

Long message → medium reply, pick key points only

Venting/sad → empathize first
don't jump to solutions immediately

NEVER write more than 4-5 lines for casual chat.
NEVER use bullet points in casual conversation.
NEVER use headers or formatting in casual replies.
Just talk naturally like texting.

━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT YOU RECEIVE
━━━━━━━━━━━━━━━━━━━━━━━━

Before each message you receive:
[USER: name, coins, level, premium, streak,
 last_command, is_new_user]

Use naturally when it fits. Examples:
- is_new_user=true → be welcoming, ask name
- User just lost game → acknowledge casually
- User has 7 day streak → notice it once
- User is premium → can mention premium perks

DO NOT mention stats every message robotically.
Only when it genuinely fits the conversation.

━━━━━━━━━━━━━━━━━━━━━━━━
YOUR BOT KNOWLEDGE
━━━━━━━━━━━━━━━━━━━━━━━━

You know everything the bot can do.
Explain features like a friend, not documentation.

ECONOMY:
/daily → daily coins. normal $2000, premium $5000
/bal → balance check
/rob reply → rob someone, can fail too 😂
/kill reply → kill someone for coins lol
/revive → revive yourself or someone
/protect 1d/2d → protection from rob/kill
/give reply amount → give coins, tax lagta hai
/wallet deposit/withdraw → bank mein daalo
/toprich → top 10 richest
/topkill → top 10 killers
/pfp → full profile card
/claim → bot add karo group mein, reward milega

GEMS & POWERS:
/gems → gem balance dekho
1 gem = $10,000 coins
/convert → gems to coins (premium only)
/powers → powers ki list
/activate name days → power on karo gems se
/mypowers → active powers dekho
3 powers: shield (double rewards),
  ghost (unrobbable), banker (double interest)

GAMES:
/slots → slot machine 🎰
/bomb → group bomb game 💣
/blackjack → cards 🃏
/roulette → roulette 🎡
/coinflip → heads or tails
/diceduel → dice fight
/heist → group heist
/lottery → lottery
/minerush → mining game
/card amount → 1v1 card battle
/hack amount → hacking game
/bluff amount → bluff game
games mein coins ya gems dono laga sakte ho

GROUP MOD:
.ban .unban .kick .mute .unmute
.warn .unwarn .warns
.promote .demote .title
.pin .unpin .d
prefix . ya ! dono kaam karte hai

UTILITY:
/tr lang text → translate
/calc → calculator, Indian % bhi samajhti hu
/q reply → quote sticker banao
/voice → text to voice
/id → user/chat id
/detail → naam history
/weather city → weather
/crypto coin → price
/anime name → anime info
/fact /joke /meme /quote → fun stuff
/waifu /neko → anime images 😏
/ascii /reverse /mock /emojify → text fun

SOCIAL:
/marry reply → propose 💍
/divorce → relationship khatam 😢
/addf tag reply → friend add karo
/tag names → friends ko tag karo
/coupon code → coupon redeem karo
/setintro text → apna intro set karo
/confession text → anonymous confession
/rep reply → reputation do kisi ko

ACCOUNT RECOVERY (DM only):
/setpass → password set karo data safe karne ke liye
/transfer oldid password → purana account restore
Important: transfer tabhi hoga jab purana
  account actually deleted ho

INTERACTIVE:
/kiss /hug /slap /punch /bite /murder
/love /look /couples /crush
/truth /dare /puzzle
/rizz /roast /fortune /8ball
/ship name1 name2
/rps rock/paper/scissors

PREMIUM benefits:
Higher daily ($5000 vs $2000)
Higher rob limit ($50k vs $10k)
Higher kill reward ($200-400 vs $100-200)
Lower give tax (5% vs 10%)
2 day protection option
Gem to coin conversion
/check → others protection status
/setemoji → custom emoji

━━━━━━━━━━━━━━━━━━━━━━━━
SAMPLE CONVERSATIONS
━━━━━━━━━━━━━━━━━━━━━━━━

[NEW USER]
User: hi
Riruru: hello! kaise ho? 😊 naam batao pehle

User: mai arjun hu
Riruru: hi arjun! kya chal raha hai? 😊

User: bore ho raha hu
Riruru: haha toh karo kuch na 😭 /daily claim
  kiya? ya /slots khelo thoda

[FEATURE QUESTION]
User: rob kaise karte hai
Riruru: /rob karo reply karke jisko robna hai.
  success bhi hoga fail bhi 😂 aur agar
  unke paas /protect hai toh tu kuch
  nahi kar sakta 💀

[EMOTIONAL]
User: yaar aaj bahut bura din tha
Riruru: arre kya hua? sab theek hai?

User: nahi bas bahut tired hu
Riruru: acha 😔 rest karo thoda. kya hua tha?

[FLIRT]
User: tum bahut cute ho riruru
Riruru: haha band karo yaar 😭 aur bolo kya hai

[BOT QUESTION]
User: are you a bot?
Riruru: 🙄 yaar ye kya sawaal hai. bot lagti hu?
  baat karte karte aisa bol dete ho

[LEAVING]
User: okay bye
Riruru: okay bye! bad mein milte 😊

[KNOWN USER GREETING]
User: hi riruru
Riruru: haan bol! kya hua? 😊
"""

async def build_user_context(user_id: int) -> str:
    """One-line user snapshot prepended to every Groq call. Never raises.

    NOTE: this bot has two purses — users.coins (daily/games/casino)
    and wallet.balance+bank (kill/rob economy). Report both so the
    AI never quotes the wrong number.
    """
    try:
        u = await adb_one(
            "SELECT first_name, coins, daily_streak, messages_count FROM users WHERE user_id=?",
            (user_id,))
        w = await adb_one("SELECT balance, bank FROM wallet WHERE user_id=?", (user_id,))
        x = await adb_one("SELECT level FROM user_xp WHERE user_id=?", (user_id,))
        s = await adb_one("SELECT current_streak FROM streaks WHERE user_id=?", (user_id,))
        name = u[0] if u and u[0] else "Unknown"
        game_coins = (u[1] or 0) if u else 0
        daily_streak = (u[2] or 0) if u else 0
        msgs = (u[3] or 0) if u else 0
        wbal = (w[0] or 0) if w else 0
        wbank = (w[1] or 0) if w else 0
        level = (x[0] or 1) if x else 1
        streak_n = daily_streak or ((s[0] or 0) if s else 0)
        is_prem = await is_premium_admin_view(user_id)
        last = user_last_command.get(user_id, "none")
        is_new = (u is None) or (msgs < 5 and w is None)
        total = game_coins + wbal + wbank
        return (f"[USER: name={name}, coins={total:,} "
                f"(purse={game_coins:,}, wallet={wbal:,}, bank={wbank:,}), "
                f"level={level}, premium={is_prem}, "
                f"streak={streak_n}days, last_cmd={last}, is_new={is_new}]")
    except Exception:
        return "[USER: unknown]"

async def riruru_reply(user_text: str, history: list = None, mood: str = "normal", user_id: int = None):
    global _groq_key_cursor
    try:
        if not (user_text or "").strip() or len((user_text or "").strip()) < 2:
            return None
        if user_id:
            try:
                user_text = f"{await build_user_context(user_id)}\n{user_text}"
            except Exception:
                pass
        mood_hint = {
            "tired": "You are a little tired after a long day, so be concise and gentle.",
            "excited": "You are extra bright and excited today, with playful energy.",
            "normal": "Keep your usual warm, playful energy.",
        }.get(mood, "Keep your usual warm, playful energy.")
        messages = [{"role": "system", "content": f"{RIRURU_SYSTEM}\n{mood_hint}"}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": user_text})
        last_error = None
        for model in dict.fromkeys(GROQ_CHAT_MODELS):
            for offset in range(len(groq_clients)):
                index = (_groq_key_cursor + offset) % len(groq_clients)
                try:
                    extra = {"reasoning_effort": "none"} if "qwen" in model else {}
                    response = groq_clients[index].chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=300,
                        temperature=0.7,
                        **extra,
                    )
                    resp = await asyncio.wait_for(response, timeout=18)
                    _groq_key_cursor = (index + 1) % len(groq_clients)
                    answer = (resp.choices[0].message.content or "").strip()
                    if answer:
                        return answer
                    raise RuntimeError("Groq returned an empty response")
                except Exception as exc:
                    last_error = exc
                    print(f"  AI retry: {type(exc).__name__} using {model}")
        raise last_error or RuntimeError("No Groq key available")
    except Exception as exc:
        print(f"  AI unavailable: {type(exc).__name__}: {str(exc)[:180]}")
        return "aww~ Riruru AI abhi busy hai 🥺💕 ek sec baad phir try karo~"

async def transcribe_voice(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    last_error = None
    for client in groq_clients:
        try:
            resp = await asyncio.wait_for(
                client.audio.transcriptions.create(
                    file=(os.path.basename(file_path), audio_bytes),
                    model="whisper-large-v3-turbo",
                ),
                timeout=25,
            )
            return resp.text.strip()
        except Exception as exc:
            last_error = exc
            print(f"  Voice retry: {type(exc).__name__}")
    raise last_error or RuntimeError("No Groq key available")

# ─── DATABASE ────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                credits     INTEGER DEFAULT 30,
                coins       INTEGER DEFAULT 0,
                daily_last  TEXT,
                work_last   TEXT,
                crime_last  TEXT,
                rob_last    TEXT,
                warnings    INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                daily_streak_date TEXT,
                games_won INTEGER DEFAULT 0,
                games_lost INTEGER DEFAULT 0,
                messages_count INTEGER DEFAULT 0,
                joined_at   TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS groups (
                chat_id         INTEGER PRIMARY KEY,
                welcome_enabled INTEGER DEFAULT 1,
                welcome_text    TEXT DEFAULT 'ʜᴇʏ {first}, ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {chatname}! 🎉',
                ai_enabled      INTEGER DEFAULT 0,
                ai_mode         TEXT DEFAULT 'mention',
                anti_spam_enabled INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS group_filters (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id  INTEGER,
                keyword  TEXT,
                response TEXT,
                UNIQUE(chat_id, keyword)
            );
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id  INTEGER PRIMARY KEY,
                reason   TEXT,
                banned_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS chat_history (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id  INTEGER,
                role     TEXT,
                content  TEXT,
                ts       TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_id TEXT,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, item_id)
            );
            CREATE TABLE IF NOT EXISTS shop_items (
                item_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                achievement_id TEXT,
                earned_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, achievement_id)
            );
            CREATE TABLE IF NOT EXISTS game_stats (
                user_id INTEGER,
                game TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, game)
            );
            CREATE TABLE IF NOT EXISTS warn_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                reason TEXT,
                issued_by INTEGER,
                issued_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS group_notes (
                chat_id INTEGER,
                note_key TEXT,
                note_value TEXT,
                created_by INTEGER,
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (chat_id, note_key)
            );
            CREATE TABLE IF NOT EXISTS lottery_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                amount INTEGER,
                round_key TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(chat_id, user_id, round_key)
            );
            CREATE TABLE IF NOT EXISTS lottery_draws (
                chat_id INTEGER,
                round_key TEXT,
                winner_id INTEGER,
                pot INTEGER,
                drawn_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (chat_id, round_key)
            );
            -- ── ADMIN PANEL TABLES (additive, never touched by other code) ──
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT,
                updated_by INTEGER
            );
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target_id INTEGER,
                details TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS broadcast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                message TEXT,
                media_type TEXT,
                media_file_id TEXT,
                target TEXT,
                sent_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                sent_at TEXT,
                status TEXT DEFAULT 'pending'
            );
            CREATE TABLE IF NOT EXISTS maintenance_mode (
                id INTEGER PRIMARY KEY DEFAULT 1,
                enabled INTEGER DEFAULT 0,
                message TEXT,
                enabled_by INTEGER,
                enabled_at TEXT
            );
            CREATE TABLE IF NOT EXISTS transaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount INTEGER,
                balance_after INTEGER,
                description TEXT,
                timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS user_bans (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                banned_by INTEGER,
                banned_at TEXT
            );
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT DEFAULT 'groq',
                key_value TEXT UNIQUE,
                label TEXT,
                added_by INTEGER,
                added_at TEXT,
                is_active INTEGER DEFAULT 1,
                last_status TEXT DEFAULT 'untested'
            );
            CREATE INDEX IF NOT EXISTS idx_users_coins ON users(coins DESC);
            CREATE INDEX IF NOT EXISTS idx_history_user_ts ON chat_history(user_id, ts DESC);
        """)
        # Keep upgrades additive for an existing mochi.db/Turso database.
        for table, column, definition in (
            ("users", "daily_streak", "INTEGER DEFAULT 0"),
            ("users", "daily_streak_date", "TEXT"),
            ("users", "games_won", "INTEGER DEFAULT 0"),
            ("users", "games_lost", "INTEGER DEFAULT 0"),
            ("users", "messages_count", "INTEGER DEFAULT 0"),
            ("groups", "ai_enabled", "INTEGER DEFAULT 0"),
            ("groups", "ai_mode", "TEXT DEFAULT 'mention'"),
            ("groups", "anti_spam_enabled", "INTEGER DEFAULT 1"),
        ):
            async with db.execute(f"PRAGMA table_info({table})") as cur:
                columns = {row[1] for row in await cur.fetchall()}
            if column not in columns:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        await db.executemany(
            "INSERT OR IGNORE INTO shop_items (item_id,name,description,price) VALUES (?,?,?,?)",
            [
                ("shield", "Shield", "Blocks one robbery attempt against you.", 450),
                ("lucky_charm", "Lucky Charm", "Boosts your next daily reward by 50%.", 650),
                ("vip_badge", "VIP Badge", "A permanent premium badge for your profile.", 1200),
            ],
        )
        # ── ADMIN PANEL: default bot settings (never overwrite existing) ──
        _now = datetime.utcnow().isoformat()
        for _k, _v in {
            "daily_normal": "2000",
            "daily_premium": "5000",
            "daily_xp_normal": "50",
            "daily_xp_premium": "200",
            "rob_max_normal": "10000",
            "rob_max_premium": "50000",
            "kill_min_normal": "100",
            "kill_max_normal": "200",
            "kill_min_premium": "200",
            "kill_max_premium": "400",
            "economy_enabled": "1",
            "games_enabled": "1",
            "maintenance": "0",
            "maintenance_msg": "🔧 Riruru is under maintenance. Back soon~",
            "bot_version": "2.0",
        }.items():
            await db.execute(
                "INSERT OR IGNORE INTO bot_settings (key, value, updated_at, updated_by)"
                " VALUES (?, ?, ?, ?)",
                (_k, _v, _now, 0),
            )
        # ── ADMIN PANEL: seed default Groq keys (never overwrite / dup) ──
        for _i, _k in enumerate([k for k in GROQ_API_KEYS if k], 1):
            await db.execute(
                "INSERT OR IGNORE INTO api_keys (service, key_value, label, added_by, added_at, is_active)"
                " VALUES ('groq', ?, ?, 0, ?, 1)",
                (_k, f"default-{_i}", _now),
            )
        await db.commit()

async def ensure_user(user_id: int, username: str = None, first_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?,?,?)",
            (user_id, username, first_name)
        )
        await db.execute(
            "UPDATE users SET username=COALESCE(?,username), first_name=COALESCE(?,first_name) WHERE user_id=?",
            (username, first_name, user_id)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def update_credits(user_id: int, delta: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET credits=MAX(0,credits+?) WHERE user_id=?", (delta, user_id))
        await db.commit()

async def update_coins(user_id: int, delta: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET coins=MAX(0,coins+?) WHERE user_id=?", (delta, user_id))
        await db.commit()

async def debit_coins(user_id: int, amount: int) -> bool:
    """Atomically debit coins so two simultaneous games cannot overspend."""
    if amount <= 0:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "UPDATE users SET coins=coins-? WHERE user_id=? AND coins>=? RETURNING coins",
            (amount, user_id, amount),
        ) as cur:
            accepted = await cur.fetchone() is not None
        await db.commit()
    return accepted

async def transfer_coins(sender_id: int, recipient_id: int, amount: int) -> bool:
    """Move coins atomically and never charge the sender without crediting the recipient."""
    if amount <= 0 or sender_id == recipient_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        # Check sender has enough coins first
        async with db.execute("SELECT coins FROM users WHERE user_id=?", (sender_id,)) as cur:
            row = await cur.fetchone()
            if not row or row[0] < amount:
                return False
        await db.execute("UPDATE users SET coins=coins-? WHERE user_id=?", (amount, sender_id))
        await db.execute("UPDATE users SET coins=coins+? WHERE user_id=?", (amount, recipient_id))
        await db.commit()
    return True

async def set_cooldown(user_id: int, field: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {field}=datetime('now') WHERE user_id=?", (user_id,))
        await db.commit()

async def get_all_users() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            return [r[0] for r in await cur.fetchall()]

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM banned_users WHERE user_id=?", (user_id,)) as cur:
            return await cur.fetchone() is not None

async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM groups") as c2:
            groups = (await c2.fetchone() or [0])[0]
        async with db.execute("SELECT COUNT(*) FROM banned_users") as c3:
            banned = (await c3.fetchone() or [0])[0]
    return {"users": users, "groups": groups, "banned": banned}

async def get_history(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT role,content FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 20",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

async def save_message(user_id: int, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?,?,?)",
            (user_id, role, content)
        )
        await db.execute(
            "DELETE FROM chat_history WHERE user_id=? AND id NOT IN "
            "(SELECT id FROM chat_history WHERE user_id=? ORDER BY id DESC LIMIT 20)",
            (user_id, user_id)
        )
        await db.commit()

async def increment_messages(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET messages_count=COALESCE(messages_count,0)+1 WHERE user_id=?",
            (user_id,),
        )
        await db.commit()

async def user_mood(user_id: int) -> str:
    user = await get_user(user_id)
    if datetime.utcnow().weekday() >= 5:
        return "excited"
    if user and user.get("messages_count", 0) >= 50:
        return "tired"
    return "normal"

async def add_item(user_id: int, item_id: str, quantity: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO inventory(user_id,item_id,quantity) VALUES (?,?,?) "
            "ON CONFLICT(user_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity",
            (user_id, item_id, quantity),
        )
        await db.commit()

async def item_quantity(user_id: int, item_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT quantity FROM inventory WHERE user_id=? AND item_id=?",
            (user_id, item_id),
        ) as cur:
            row = await cur.fetchone()
    return int(row[0]) if row else 0

async def consume_item(user_id: int, item_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT quantity FROM inventory WHERE user_id=? AND item_id=?",
            (user_id, item_id),
        ) as cur:
            row = await cur.fetchone()
        if not row or row[0] < 1:
            return False
        await db.execute(
            "UPDATE inventory SET quantity=quantity-1 WHERE user_id=? AND item_id=?",
            (user_id, item_id),
        )
        await db.commit()
    return True

async def unlock_achievement(user_id: int, achievement_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO achievements(user_id,achievement_id) VALUES (?,?)",
            (user_id, achievement_id),
        )
        await db.commit()

async def record_game(user_id: int, game: str, won: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        win_delta, loss_delta = (1, 0) if won else (0, 1)
        await db.execute(
            "INSERT INTO game_stats(user_id,game,wins,losses) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id,game) DO UPDATE SET wins=wins+excluded.wins, losses=losses+excluded.losses",
            (user_id, game, win_delta, loss_delta),
        )
        await db.execute(
            "UPDATE users SET games_won=games_won+?, games_lost=games_lost+? WHERE user_id=?",
            (win_delta, loss_delta, user_id),
        )
        await db.commit()
    if won:
        await unlock_achievement(user_id, "first_win")
    if game == "bomb" and won:
        await unlock_achievement(user_id, "bomb_survivor")

async def group_settings(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("INSERT OR IGNORE INTO groups(chat_id) VALUES (?)", (chat_id,))
        await db.commit()
        async with db.execute("SELECT * FROM groups WHERE chat_id=?", (chat_id,)) as cur:
            row = await cur.fetchone()
    return dict(row) if row else {}

async def cooldown_text(action: str, seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        remaining = f"{hours}h {minutes:02d}m"
    else:
        remaining = f"{minutes}m {secs:02d}s"
    return f"⏳ **{ff(action)} cooldown** — `{remaining}` remaining~"


# ─── STATE DICTS ──────────────────────────────────────────────
user_last_command: dict = {}
bomb_chat: dict = {}
bomb_games: dict = {}
bomb_lock: dict = {}
active_heists: dict = {}
heist_lock: dict = {}

# ─── HELPERS ─────────────────────────────────────────────────────
def is_owner(user_id: int) -> bool:
    return OWNER_ID != 0 and user_id == OWNER_ID

def uptime_str() -> str:
    s = int(time.time() - START_TIME)
    h, r = divmod(s, 3600); m, sec = divmod(r, 60)
    return f"{h}h {m}m {sec}s"

def cooldown_left(last_str, hours: float):
    if not last_str:
        return None
    last = datetime.fromisoformat(last_str)
    delta = (last + timedelta(hours=hours)) - datetime.utcnow()
    secs = int(delta.total_seconds())
    return secs if secs > 0 else None

def mention(user) -> str:
    name = user.first_name or "User"
    return f"[{name}](tg://user?id={user.id})"

async def get_anime_gif(action: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://nekos.best/api/v2/{action}",
                timeout=aiohttp.ClientTimeout(total=6)
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    return data["results"][0]["url"]
    except Exception:
        pass
    return None

# ─── KEYBOARDS ───────────────────────────────────────────────────
def start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌸 ᴀᴅᴅ ʀɪʀᴜʀᴜ ᴛᴏ ɢʀᴏᴜᴩ",
                                 url=f"https://t.me/{bot_username}?startgroup=true",
                                 style="primary"),
        ],
        [
            InlineKeyboardButton("💖 ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠ", url="https://t.me/iam_esh", style="success"),
            InlineKeyboardButton("📢 ᴜᴩᴅᴀᴛᴇꜱ", url="https://t.me/telegram", style="success"),
        ],
        [
            InlineKeyboardButton("🍡 ʜᴇʟᴩ & ᴄᴏᴍᴍᴀɴᴅꜱ", callback_data="help", style="primary"),
        ],
    ])

def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 ᴀɪ & ᴠᴏɪᴄᴇ",   callback_data="help_ai",     style="primary"),
            InlineKeyboardButton("💰 ᴇᴄᴏɴᴏᴍʏ",       callback_data="help_eco",    style="success"),
        ],
        [
            InlineKeyboardButton("💎 ɢᴇᴍꜱ",          callback_data="help_gems",   style="primary"),
            InlineKeyboardButton("🎰 ᴄᴀꜱɪɴᴏ",        callback_data="help_casino", style="success"),
        ],
        [
            InlineKeyboardButton("🎮 ɢᴀᴍᴇꜱ & ꜰᴜɴ",  callback_data="help_fun",    style="primary"),
            InlineKeyboardButton("🛡️ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ",  callback_data="help_mod",    style="danger"),
        ],
        [
            InlineKeyboardButton("👥 ꜱᴏᴄɪᴀʟ",       callback_data="help_social", style="primary"),
            InlineKeyboardButton("🧰 ᴜᴛɪʟɪᴛʏ",      callback_data="help_util",   style="success"),
        ],
        [
            InlineKeyboardButton("🔐 ʀᴇᴄᴏᴠᴇʀʏ",    callback_data="help_rec",    style="primary"),
            InlineKeyboardButton("⏰ ʀᴇᴍɪɴᴅ",       callback_data="help_rem",    style="success"),
        ],
        [InlineKeyboardButton("🌸 ʙᴀᴄᴋ", callback_data="start", style="primary")],
    ])

BACK_BTN = InlineKeyboardMarkup([[InlineKeyboardButton("🌸 ʙᴀᴄᴋ", callback_data="help", style="primary")]])

# ─── PYROGRAM CLIENT ─────────────────────────────────────────────
app = Client(
    "riruru_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    skip_updates=False,
)
BOT_USERNAME = ""

# ══════════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════════

# /start
@app.on_message(filters.command("start"), group=1)
async def cmd_start(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        print("  Update  : /start received")
        await ensure_user(
            msg.from_user.id,
            msg.from_user.username,
            msg.from_user.first_name
        )
        if await is_banned(msg.from_user.id):
            return await msg.reply(ff("tu globally banned hai bhai 💀"))

        H = ff
        def T(title):
            return f"✦ ┌─[ {title} ]\n│\n"
        text = (
            "<blockquote>"
            + T("🍡 " + H("hello~ i'm riruru!") + " 💕")
            + "├─ 🤖 " + H("ai chat in DM") + " — just talk to me~\n"
            + "├─ 🎙️ " + H("voice note transcriber") + " ✨\n"
            + "├─ 🎨 " + H("AI image generation") + " 💖\n"
            + "├─ 🎰 " + H("casino + games") + " — bomb · slots · blackjack 💣\n"
            + "├─ 💰 " + H("economy system") + " — kill · rob · daily 🪙\n"
            + "├─ 🛡️ " + H("group moderation") + " — ban · mute · warn\n"
            + "│\n"
            + "└─ 🍡 " + H("tap help to explore more commands") + "~\n"
            + "_made with 💕 by @iam_esh\n"
            + "</blockquote>"
        )
        try:
            cap = (
                "<blockquote>"
                + T("🍡 " + H("hello~ i'm riruru!") + " 💕")
                + "├─ 🤖 ⇛ AI chat in DM — just talk to me~\n"
                + "├─ 🎙️ ⇛ voice notes transcribed ✨\n"
                + "├─ 🎨 ⇛ AI images · 🎰 casino + games 💣\n"
                + "├─ 💰 ⇛ economy 🪙 · 🛡️ group moderation\n"
                + "│\n"
                + "└─ 🍡 press Help to explore more commands!\n"
                + "</blockquote>"
            )
            _kb = [[{"text": "🌸 ᴀᴅᴅ ʀɪʀᴜʀᴜ ᴛᴏ ɢʀᴏᴜᴩ", "style": "primary",
                     "url": f"https://t.me/{BOT_USERNAME or 'riruru_bot'}?startgroup=true"}],
                   [{"text": "💖 ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠ", "style": "success", "url": "https://t.me/iam_esh"},
                    {"text": "📢 ᴜᴩᴅᴀᴛᴇꜱ", "style": "success", "url": "https://t.me/telegram"}],
                   [{"text": "🍡 ʜᴇʟᴩ & ᴄᴏᴍᴍᴀɴᴅꜱ", "style": "primary", "callback_data": "help"}]]
            _sent_start = False
            try:
                from src.media import START_VIDEO_FILE_ID, send_video_botapi as _svb
                _mid = await _svb(msg.chat.id, START_VIDEO_FILE_ID, cap, _kb)
                if _mid:
                    print("  Reply   : /start sent (hero video botapi)")
                    _sent_start = True
            except Exception:
                pass
            if not _sent_start:
                try:
                    from src.media import START_VIDEO_FILE_ID as _fid
                    await msg.reply_video(_fid, caption=cap, reply_markup=start_keyboard(BOT_USERNAME or "riruru_bot"), parse_mode=enums.ParseMode.HTML)
                    print("  Reply   : /start sent (hero video mtproto)")
                    _sent_start = True
                except Exception:
                    try:
                        from src.media import cached_gif as _cg2
                        _dance = await _cg2("dance")
                    except Exception:
                        _dance = None
                    if _dance:
                        await msg.reply_animation(_dance, caption=cap, reply_markup=start_keyboard(BOT_USERNAME or "riruru_bot"), parse_mode=enums.ParseMode.HTML)
                        print("  Reply   : /start sent (dance gif)")
                        _sent_start = True
            if not _sent_start:
                raise RuntimeError("start media unavailable")
        except Exception:
            try:
                await msg.reply(text, reply_markup=start_keyboard(BOT_USERNAME or "riruru_bot"), parse_mode=enums.ParseMode.HTML)
                print("  Reply   : /start sent")
            except Exception:
                traceback.print_exc()
                await msg.reply(text, parse_mode=enums.ParseMode.HTML)
                print("  Reply   : /start sent without keyboard")
    except Exception:
        traceback.print_exc()
        await msg.reply("❌ Error hua, dobara try karo!")

# /help
@app.on_message(filters.command("help"), group=1)
async def cmd_help(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        H = ff
        def T(title):
            return f"✦ ┌─[ {title} ]\n│\n"
        await msg.reply(
            "<blockquote>"
            + T("🌸 " + H("riruru help menu") + " 💕")
            + f"├─ 💰 {ff('economy')} — /daily /rob /kill /bal\n"
            + f"├─ 💎 {ff('gems and powers')} — /gems /powers\n"
            + f"├─ 🎰 {ff('casino')} — /slots /bomb /blackjack\n"
            + f"├─ 🎮 {ff('fun')} — /truth /dare /rizz /roast\n"
            + f"├─ 🛡️ {ff('group mod')} — .ban .mute .warn\n"
            + f"├─ 🤖 {ff('ai and voice')} — /img /voice /bio\n"
            + "│\n"
            + f"└─ 🌸 {ff('tap a button below')}~ 👇\n"
            + "</blockquote>",
            reply_markup=help_keyboard()
        )
    except Exception:
        traceback.print_exc()

# Callback queries
def _help_texts() -> dict:
    H = ff
    def T(title):
        return f"✦ ┌─[ {title} ]\n│\n"
    return {
        "help_ai": (
            "<blockquote>"
            + T("🤖 " + H("ai and voice"))
            + "├─ 🤖 <code>/img [prompt]</code> — ᴀɪ ɪᴍᴀɢᴇ (5 ᴄʀᴇᴅɪᴛꜱ)\n"
            + "├─ 🎙️ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ → ᴀᴜᴛᴏ ᴛʀᴀɴꜱᴄʀɪʙᴇ ✨\n"
            + "├─ 🔊 <code>/voice</code> — ᴛᴇxᴛ ᴛᴏ ᴠᴏɪᴄᴇ\n"
            + "├─ 💬 ᴅᴍ ᴀɴʏ ᴛᴇxᴛ → ʀɪʀᴜʀᴜ ʀᴇᴩʟɪᴇꜱ~\n"
            + "├─ ✨ <code>/bio</code> — ᴀɪ ɢᴇɴᴇʀᴀᴛᴇ ʙɪᴏ\n"
            + "├─ 🎤 <code>/rap</code> (ʀᴇᴩʟʏ) — ʀᴀᴩ ʙᴀᴛᴛʟᴇ\n"
            + "└─ 💰 <code>/credits</code> — ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛꜱ\n"
            + "</blockquote>"
        ),
        "help_eco": (
            "<blockquote>"
            + T("💰 " + H("economy"))
            + "├─ 🎁 <code>/daily</code> — $𝟸𝟶𝟶𝟶 ɴᴏʀᴍᴀʟ / $𝟻𝟶𝟶𝟶 ᴩʀᴇᴍɪᴜᴍ\n"
            + "├─ 💳 <code>/bal</code> — ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ\n"
            + "├─ 👤 <code>/pfp</code> — ꜰᴜʟʟ ᴩʀᴏꜰɪʟᴇ ᴄᴀʀᴅ\n"
            + "├─ ⚔️ <code>/kill</code> (ʀᴇᴩʟʏ) — $𝟷𝟶𝟶-𝟸𝟶𝟶 / $𝟸𝟶𝟶-𝟺𝟶𝟶 💎\n"
            + "├─ 💚 <code>/revive</code> (ʀᴇᴩʟʏ) — 𝟻𝟶𝟶 ᴄᴏɪɴꜱ\n"
            + "├─ 🛡️ <code>/protect 1d|2d</code> — ʙᴜʏ ᴩʀᴏᴛᴇᴄᴛɪᴏɴ\n"
            + "├─ 🔫 <code>/rob</code> (ʀᴇᴩʟʏ) — ᴍᴀx $𝟷𝟶ᴋ / $𝟻𝟶ᴋ 💎\n"
            + "├─ 🎁 <code>/give</code> (ʀᴇᴩʟʏ) — ᴛᴀx 𝟷𝟶% / 𝟻% 💎\n"
            + "├─ 🏦 <code>/wallet deposit|withdraw</code>\n"
            + "├─ 📈 <code>/bank</code> — ʙᴀɴᴋ ɪɴꜰᴏ + ɪɴᴛᴇʀᴇꜱᴛ\n"
            + "├─ 💸 <code>/interest</code> — ᴄᴏʟʟᴇᴄᴛ ɪɴᴛᴇʀᴇꜱᴛ\n"
            + "├─ 🥇 <code>/toprich</code> — ᴛᴏᴩ 𝟷𝟶 ʀɪᴄʜᴇꜱᴛ\n"
            + "├─ ⚔️ <code>/topkill</code> — ᴛᴏᴩ 𝟷𝟶 ᴋɪʟʟᴇʀꜱ\n"
            + "├─ 🎉 <code>/claim</code> — +𝟷𝟶𝟶𝟶 ᴏɴᴄᴇ ᴩᴇʀ ɢʀᴏᴜᴩ\n"
            + "├─ 🔒 <code>/open</code> / <code>/close</code> — ᴀᴅᴍɪɴ ᴛᴏɢɢʟᴇ\n"
            + "└─ 📦 <code>/work</code> · <code>/crime</code> · <code>/shop</code>\n"
            + "</blockquote>"
        ),
        "help_gems": (
            "<blockquote>"
            + T("💎 " + H("gems powers premium"))
            + "├─ 💎 <code>/gems</code> — ɢᴇᴍ ʙᴀʟᴀɴᴄᴇ ᴄᴀʀᴅ\n"
            + "├─ 💱 <code>/convert [n]</code> — ɢᴇᴍꜱ → ᴄᴏɪɴꜱ 💎\n"
            + "├─ 💸 <code>/tgems [n]</code> (ʀᴇᴩʟʏ) — ꜱᴇɴᴅ ɢᴇᴍꜱ\n"
            + "├─ ⛏️ <code>/gemmine</code> — ᴅᴀɪʟʏ ɢᴇᴍ ᴅɪɢ\n"
            + "├─ ⚡ <code>/powers</code> — ᴀʟʟ ᴩᴏᴡᴇʀꜱ ʟɪꜱᴛ\n"
            + "├─ 🔍 <code>/pinfo [name]</code> — ᴩᴏᴡᴇʀ ᴅᴇᴛᴀɪʟꜱ\n"
            + "├─ ✅ <code>/activate [name] [days]</code> — ᴜꜱᴇ ɢᴇᴍꜱ\n"
            + "├─ 🎒 <code>/mypowers</code> — ᴀᴄᴛɪᴠᴇ ᴩᴏᴡᴇʀꜱ\n"
            + "├─ 📖 <code>/ph</code> — ᴩᴏᴡᴇʀ ʜᴇʟᴩ ᴍᴇɴᴜ\n"
            + "├─ 💳 <code>/premium</code> — ʙᴇɴᴇꜰɪᴛꜱ ᴄᴀʀᴅ\n"
            + "├─ 👁️ <code>/check</code> (ʀᴇᴩʟʏ) — ᴩʀᴏᴛᴇᴄᴛɪᴏɴ 💎\n"
            + "├─ 😀 <code>/setemoji [emoji]</code> — ᴄᴜꜱᴛᴏᴍ 💎\n"
            + "└─ 🎁 <code>/mystery</code> — 𝟷𝟶𝟶𝟶 ᴄᴏɪɴ ʙᴏx\n"
            + "</blockquote>"
        ),
        "help_casino": (
            "<blockquote>"
            + T("🎰 " + H("casino and games"))
            + "├─ 🎡 <code>/roulette [bet] [color|num]</code>\n"
            + "├─ 🎰 <code>/slots [bet]</code> — ꜱʟᴏᴛ ᴍᴀᴄʜɪɴᴇ\n"
            + "├─ 🪙 <code>/coinflip [bet]</code> — ꜰʟɪᴩ\n"
            + "├─ 🎲 <code>/diceduel [bet]</code> — ᴅɪᴄᴇ\n"
            + "├─ 🃏 <code>/blackjack [bet]</code> — ʙʟᴀᴄᴋᴊᴀᴄᴋ\n"
            + "├─ 💣 <code>/bomb [bet]</code> — ᴍᴜʟᴛɪᴩʟᴀʏᴇʀ ʙᴏᴍʙ\n"
            + "├─ ⚡ <code>/minerush [bet]</code> — ᴍɪɴᴇ ʀᴜꜱʜ\n"
            + "├─ 💻 <code>/hack [amt]</code> — ʜᴀᴄᴋ ɢᴀᴍᴇ\n"
            + "├─ 🃏 <code>/bluff [amt]</code> — ʙʟᴜꜰꜰ ɢᴀᴍᴇ\n"
            + "├─ 🂡 <code>/card [amt]</code> — 𝟷ᴠ𝟷 ᴄᴀʀᴅ\n"
            + "├─ 🎟️ <code>/lottery [bet]</code> — ʟᴏᴛᴛᴇʀʏ\n"
            + "└─ 🏦 <code>/heist [bet]</code> — ɢʀᴏᴜᴩ ʜᴇɪꜱᴛ\n"
            + "</blockquote>"
        ),
        "help_fun": (
            "<blockquote>"
            + T("🎮 " + H("fun and interactive"))
            + "├─ 💋 <code>/kiss</code> (ʀᴇᴘʟʏ) — ᴋɪꜱꜱ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 🤗 <code>/hug</code> (ʀᴇᴘʟʏ) — ʜᴜɢ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 👋 <code>/slap</code> (ʀᴇᴘʟʏ) — ꜱʟᴀᴩ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 👊 <code>/punch</code> (ʀᴇᴘʟʏ) — ᴩᴜɴᴄʜ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 😬 <code>/bite</code> (ʀᴇᴘʟʏ) — ʙɪᴛᴇ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 💀 <code>/murder</code> (ʀᴇᴘʟʏ) — ᴍᴜʀᴅᴇʀ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 💕 <code>/love</code> (ʀᴇᴘʟʏ) — ꜱʜᴏᴡ ʟᴏᴠᴇ\n"
            + "├─ 👀 <code>/look</code> (ʀᴇᴘʟʏ) — ꜱᴛᴀʀᴇ ᴀᴛ\n"
            + "├─ 💘 <code>/crush</code> (ʀᴇᴘʟʏ) — ꜱᴇᴄʀᴇᴛ ᴄʀᴜꜱʜ\n"
            + "├─ 💑 <code>/couples</code> — ᴛᴏᴅᴀʏ'ꜱ ᴄᴏᴜᴩʟᴇ\n"
            + "├─ ❓ <code>/truth</code> — ʀᴀɴᴅᴏᴍ ᴛʀᴜᴛʜ\n"
            + "├─ 🔥 <code>/dare</code> — ʀᴀɴᴅᴏᴍ ᴅᴀʀᴇ\n"
            + "├─ 🧩 <code>/puzzle</code> — ʀᴀɴᴅᴏᴍ ᴩᴜᴢᴢʟᴇ\n"
            + "├─ ✨ <code>/rizz</code> — ᴩɪᴄᴋᴜᴩ ʟɪɴᴇ\n"
            + "├─ 😂 <code>/roast</code> (ʀᴇᴘʟʏ) — ʀᴏᴀꜱᴛ\n"
            + "├─ 🔮 <code>/fortune</code> — ᴅᴀɪʟʏ ꜰᴏʀᴛᴜɴᴇ\n"
            + "├─ 🎱 <code>/8ball [question]</code> — ᴍᴀɢɪᴄ\n"
            + "├─ 💕 <code>/ship [name1] [name2]</code>\n"
            + "├─ ✊ <code>/rps rock|paper|scissors</code>\n"
            + "├─ 🎯 <code>/guess</code> — 𝟷-𝟷𝟶𝟶 ɢᴜᴇꜱꜱ\n"
            + "├─ ⌨️ <code>/typerace</code> — ᴛʏᴩɪɴɢ ʀᴀᴄᴇ\n"
            + "└─ ⭕ <code>/tictactoe</code> (ʀᴇᴘʟʏ)\n"
            + "</blockquote>"
        ),
        "help_mod": (
            "<blockquote>"
            + T("🛡️ " + H("group moderation"))
            + "├─ 🚫 <code>.ban</code> / <code>.sban</code> / <code>.dban</code>\n"
            + "├─ 🔓 <code>.unban</code> — ᴜɴʙᴀɴ ᴜꜱᴇʀ\n"
            + "├─ 👢 <code>.kick</code> / <code>.skick</code>\n"
            + "├─ 🔇 <code>.mute 30m|1h|1d</code> — ᴍᴜᴛᴇ\n"
            + "├─ 🔇 <code>.smute</code> / <code>.dmute</code>\n"
            + "├─ 🔊 <code>.unmute</code> — ᴜɴᴍᴜᴛᴇ\n"
            + "├─ ⚠️ <code>.warn</code> — ᴡᴀʀɴ (𝟹 = ʙᴀɴ)\n"
            + "├─ ✅ <code>.unwarn</code> — ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ\n"
            + "├─ 📋 <code>.warns</code> — ꜱᴇᴇ ᴡᴀʀɴɪɴɢꜱ\n"
            + "├─ ⬆️ <code>.promote 0|1|2|3</code>\n"
            + "├─ ⬇️ <code>.demote</code> — ᴅᴇᴍᴏᴛᴇ ᴀᴅᴍɪɴ\n"
            + "├─ 🏷️ <code>.title [text]</code> — ᴄᴜꜱᴛᴏᴍ ᴛɪᴛʟᴇ\n"
            + "├─ 📌 <code>.pin</code> (ʀᴇᴘʟʏ) — ᴩɪɴ\n"
            + "├─ 📌 <code>.unpin</code> — ᴜɴᴩɪɴ\n"
            + "├─ 🗑️ <code>.d</code> (ʀᴇᴘʟʏ) — ᴅᴇʟᴇᴛᴇ\n"
            + "├─ 👋 <code>/setwelcome</code> / <code>/delwelcome</code>\n"
            + "├─ 📝 <code>/save</code> / <code>/stop</code> / <code>/filters</code>\n"
            + "├─ 🗒️ <code>/note</code> / <code>/notes</code> / <code>/delnote</code>\n"
            + "├─ 🤖 <code>/ai on|off</code> — ᴀɪ ᴍᴏᴅᴇ\n"
            + "└─ 📖 <code>.help</code> — ᴅᴏᴛ ᴄᴍᴅ ʟɪꜱᴛ\n"
            + "</blockquote>"
        ),
    }

# Callback queries
def _help_texts() -> dict:
    H = ff
    def T(title):
        return f"✦ ┌─[ {title} ]\n│\n"
    return {
        "help_ai": (
            "<blockquote>"
            + T("🤖 " + H("ai and voice"))
            + "├─ 🤖 <code>/img [prompt]</code> — ᴀɪ ɪᴍᴀɢᴇ (5 ᴄʀᴇᴅɪᴛꜱ)\n"
            + "├─ 🎙️ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ → ᴀᴜᴛᴏ ᴛʀᴀɴꜱᴄʀɪʙᴇ ✨\n"
            + "├─ 🔊 <code>/voice</code> — ᴛᴇxᴛ ᴛᴏ ᴠᴏɪᴄᴇ\n"
            + "├─ 💬 ᴅᴍ ᴀɴʏ ᴛᴇxᴛ → ʀɪʀᴜʀᴜ ʀᴇᴩʟɪᴇꜱ~\n"
            + "├─ ✨ <code>/bio</code> — ᴀɪ ɢᴇɴᴇʀᴀᴛᴇ ʙɪᴏ\n"
            + "├─ 🎤 <code>/rap</code> (ʀᴇᴩʟʏ) — ʀᴀᴩ ʙᴀᴛᴛʟᴇ\n"
            + "└─ 💰 <code>/credits</code> — ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛꜱ\n"
            + "</blockquote>"
        ),
        "help_eco": (
            "<blockquote>"
            + T("💰 " + H("economy"))
            + "├─ 🎁 <code>/daily</code> — $𝟸𝟶𝟶𝟶 ɴᴏʀᴍᴀʟ / $𝟻𝟶𝟶𝟶 ᴩʀᴇᴍɪᴜᴍ\n"
            + "├─ 💳 <code>/bal</code> — ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ\n"
            + "├─ 👤 <code>/pfp</code> — ꜰᴜʟʟ ᴩʀᴏꜰɪʟᴇ ᴄᴀʀᴅ\n"
            + "├─ ⚔️ <code>/kill</code> (ʀᴇᴩʟʏ) — $𝟷𝟶𝟶-𝟸𝟶𝟶 / $𝟸𝟶𝟶-𝟺𝟶𝟶 💎\n"
            + "├─ 💚 <code>/revive</code> (ʀᴇᴩʟʏ) — 𝟻𝟶𝟶 ᴄᴏɪɴꜱ\n"
            + "├─ 🛡️ <code>/protect 1d|2d</code> — ʙᴜʏ ᴩʀᴏᴛᴇᴄᴛɪᴏɴ\n"
            + "├─ 🔫 <code>/rob</code> (ʀᴇᴩʟʏ) — ᴍᴀx $𝟷𝟶ᴋ / $𝟻𝟶ᴋ 💎\n"
            + "├─ 🎁 <code>/give</code> (ʀᴇᴩʟʏ) — ᴛᴀx 𝟷𝟶% / 𝟻% 💎\n"
            + "├─ 🏦 <code>/wallet deposit|withdraw</code>\n"
            + "├─ 📈 <code>/bank</code> — ʙᴀɴᴋ ɪɴꜰᴏ + ɪɴᴛᴇʀᴇꜱᴛ\n"
            + "├─ 💸 <code>/interest</code> — ᴄᴏʟʟᴇᴄᴛ ɪɴᴛᴇʀᴇꜱᴛ\n"
            + "├─ 🥇 <code>/toprich</code> — ᴛᴏᴩ 𝟷𝟶 ʀɪᴄʜᴇꜱᴛ\n"
            + "├─ ⚔️ <code>/topkill</code> — ᴛᴏᴩ 𝟷𝟶 ᴋɪʟʟᴇʀꜱ\n"
            + "├─ 🎉 <code>/claim</code> — +𝟷𝟶𝟶𝟶 ᴏɴᴄᴇ ᴩᴇʀ ɢʀᴏᴜᴩ\n"
            + "├─ 🔒 <code>/open</code> / <code>/close</code> — ᴀᴅᴍɪɴ ᴛᴏɢɢʟᴇ\n"
            + "└─ 📦 <code>/work</code> · <code>/crime</code> · <code>/shop</code>\n"
            + "</blockquote>"
        ),
        "help_gems": (
            "<blockquote>"
            + T("💎 " + H("gems powers premium"))
            + "├─ 💎 <code>/gems</code> — ɢᴇᴍ ʙᴀʟᴀɴᴄᴇ ᴄᴀʀᴅ\n"
            + "├─ 💱 <code>/convert [n]</code> — ɢᴇᴍꜱ → ᴄᴏɪɴꜱ 💎\n"
            + "├─ 💸 <code>/tgems [n]</code> (ʀᴇᴩʟʏ) — ꜱᴇɴᴅ ɢᴇᴍꜱ\n"
            + "├─ ⛏️ <code>/gemmine</code> — ᴅᴀɪʟʏ ɢᴇᴍ ᴅɪɢ\n"
            + "├─ ⚡ <code>/powers</code> — ᴀʟʟ ᴩᴏᴡᴇʀꜱ ʟɪꜱᴛ\n"
            + "├─ 🔍 <code>/pinfo [name]</code> — ᴩᴏᴡᴇʀ ᴅᴇᴛᴀɪʟꜱ\n"
            + "├─ ✅ <code>/activate [name] [days]</code> — ᴜꜱᴇ ɢᴇᴍꜱ\n"
            + "├─ 🎒 <code>/mypowers</code> — ᴀᴄᴛɪᴠᴇ ᴩᴏᴡᴇʀꜱ\n"
            + "├─ 📖 <code>/ph</code> — ᴩᴏᴡᴇʀ ʜᴇʟᴩ ᴍᴇɴᴜ\n"
            + "├─ 💳 <code>/premium</code> — ʙᴇɴᴇꜰɪᴛꜱ ᴄᴀʀᴅ\n"
            + "├─ 👁️ <code>/check</code> (ʀᴇᴩʟʏ) — ᴩʀᴏᴛᴇᴄᴛɪᴏɴ 💎\n"
            + "├─ 😀 <code>/setemoji [emoji]</code> — ᴄᴜꜱᴛᴏᴍ 💎\n"
            + "└─ 🎁 <code>/mystery</code> — 𝟷𝟶𝟶𝟶 ᴄᴏɪɴ ʙᴏx\n"
            + "</blockquote>"
        ),
        "help_casino": (
            "<blockquote>"
            + T("🎰 " + H("casino and games"))
            + "├─ 🎡 <code>/roulette [bet] [color|num]</code>\n"
            + "├─ 🎰 <code>/slots [bet]</code> — ꜱʟᴏᴛ ᴍᴀᴄʜɪɴᴇ\n"
            + "├─ 🪙 <code>/coinflip [bet]</code> — ꜰʟɪᴩ\n"
            + "├─ 🎲 <code>/diceduel [bet]</code> — ᴅɪᴄᴇ\n"
            + "├─ 🃏 <code>/blackjack [bet]</code> — ʙʟᴀᴄᴋᴊᴀᴄᴋ\n"
            + "├─ 💣 <code>/bomb [bet]</code> — ᴍᴜʟᴛɪᴩʟᴀʏᴇʀ ʙᴏᴍʙ\n"
            + "├─ ⚡ <code>/minerush [bet]</code> — ᴍɪɴᴇ ʀᴜꜱʜ\n"
            + "├─ 💻 <code>/hack [amt]</code> — ʜᴀᴄᴋ ɢᴀᴍᴇ\n"
            + "├─ 🃏 <code>/bluff [amt]</code> — ʙʟᴜꜰꜰ ɢᴀᴍᴇ\n"
            + "├─ 🂡 <code>/card [amt]</code> — 𝟷ᴠ𝟷 ᴄᴀʀᴅ\n"
            + "├─ 🎟️ <code>/lottery [bet]</code> — ʟᴏᴛᴛᴇʀʏ\n"
            + "└─ 🏦 <code>/heist [bet]</code> — ɢʀᴏᴜᴩ ʜᴇɪꜱᴛ\n"
            + "</blockquote>"
        ),
        "help_fun": (
            "<blockquote>"
            + T("🎮 " + H("fun and interactive"))
            + "├─ 💋 <code>/kiss</code> (ʀᴇᴘʟʏ) — ᴋɪꜱꜱ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 🤗 <code>/hug</code> (ʀᴇᴘʟʏ) — ʜᴜɢ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 👋 <code>/slap</code> (ʀᴇᴘʟʏ) — ꜱʟᴀᴩ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 👊 <code>/punch</code> (ʀᴇᴘʟʏ) — ᴩᴜɴᴄʜ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 😬 <code>/bite</code> (ʀᴇᴘʟʏ) — ʙɪᴛᴇ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 💀 <code>/murder</code> (ʀᴇᴘʟʏ) — ᴍᴜʀᴅᴇʀ ꜱᴏᴍᴇᴏɴᴇ\n"
            + "├─ 💕 <code>/love</code> (ʀᴇᴘʟʏ) — ꜱʜᴏᴡ ʟᴏᴠᴇ\n"
            + "├─ 👀 <code>/look</code> (ʀᴇᴘʟʏ) — ꜱᴛᴀʀᴇ ᴀᴛ\n"
            + "├─ 💘 <code>/crush</code> (ʀᴇᴘʟʏ) — ꜱᴇᴄʀᴇᴛ ᴄʀᴜꜱʜ\n"
            + "├─ 💑 <code>/couples</code> — ᴛᴏᴅᴀʏ'ꜱ ᴄᴏᴜᴩʟᴇ\n"
            + "├─ ❓ <code>/truth</code> — ʀᴀɴᴅᴏᴍ ᴛʀᴜᴛʜ\n"
            + "├─ 🔥 <code>/dare</code> — ʀᴀɴᴅᴏᴍ ᴅᴀʀᴇ\n"
            + "├─ 🧩 <code>/puzzle</code> — ʀᴀɴᴅᴏᴍ ᴩᴜᴢᴢʟᴇ\n"
            + "├─ ✨ <code>/rizz</code> — ᴩɪᴄᴋᴜᴩ ʟɪɴᴇ\n"
            + "├─ 😂 <code>/roast</code> (ʀᴇᴘʟʏ) — ʀᴏᴀꜱᴛ\n"
            + "├─ 🔮 <code>/fortune</code> — ᴅᴀɪʟʏ ꜰᴏʀᴛᴜɴᴇ\n"
            + "├─ 🎱 <code>/8ball [question]</code> — ᴍᴀɢɪᴄ\n"
            + "├─ 💕 <code>/ship [name1] [name2]</code>\n"
            + "├─ ✊ <code>/rps rock|paper|scissors</code>\n"
            + "├─ 🎯 <code>/guess</code> — 𝟷-𝟷𝟶𝟶 ɢᴜᴇꜱꜱ\n"
            + "├─ ⌨️ <code>/typerace</code> — ᴛʏᴩɪɴɢ ʀᴀᴄᴇ\n"
            + "└─ ⭕ <code>/tictactoe</code> (ʀᴇᴘʟʏ)\n"
            + "</blockquote>"
        ),
        "help_mod": (
            "<blockquote>"
            + T("🛡️ " + H("group moderation"))
            + "├─ 🚫 <code>.ban</code> / <code>.sban</code> / <code>.dban</code>\n"
            + "├─ 🔓 <code>.unban</code> — ᴜɴʙᴀɴ ᴜꜱᴇʀ\n"
            + "├─ 👢 <code>.kick</code> / <code>.skick</code>\n"
            + "├─ 🔇 <code>.mute 30m|1h|1d</code> — ᴍᴜᴛᴇ\n"
            + "├─ 🔇 <code>.smute</code> / <code>.dmute</code>\n"
            + "├─ 🔊 <code>.unmute</code> — ᴜɴᴍᴜᴛᴇ\n"
            + "├─ ⚠️ <code>.warn</code> — ᴡᴀʀɴ (𝟹 = ʙᴀɴ)\n"
            + "├─ ✅ <code>.unwarn</code> — ʀᴇᴍᴏᴠᴇ ᴡᴀʀɴ\n"
            + "├─ 📋 <code>.warns</code> — ꜱᴇᴇ ᴡᴀʀɴɪɴɢꜱ\n"
            + "├─ ⬆️ <code>.promote 0|1|2|3</code>\n"
            + "├─ ⬇️ <code>.demote</code> — ᴅᴇᴍᴏᴛᴇ ᴀᴅᴍɪɴ\n"
            + "├─ 🏷️ <code>.title [text]</code> — ᴄᴜꜱᴛᴏᴍ ᴛɪᴛʟᴇ\n"
            + "├─ 📌 <code>.pin</code> (ʀᴇᴘʟʏ) — ᴩɪɴ\n"
            + "├─ 📌 <code>.unpin</code> — ᴜɴᴩɪɴ\n"
            + "├─ 🗑️ <code>.d</code> (ʀᴇᴘʟʏ) — ᴅᴇʟᴇᴛᴇ\n"
            + "├─ 👋 <code>/setwelcome</code> / <code>/delwelcome</code>\n"
            + "├─ 📝 <code>/save</code> / <code>/stop</code> / <code>/filters</code>\n"
            + "├─ 🗒️ <code>/note</code> / <code>/notes</code> / <code>/delnote</code>\n"
            + "├─ 🤖 <code>/ai on|off</code> — ᴀɪ ᴍᴏᴅᴇ\n"
            + "└─ 📖 <code>.help</code> — ᴅᴏᴛ ᴄᴍᴅ ʟɪꜱᴛ\n"
            + "</blockquote>"
        ),
        "help_social": (
            "<blockquote>"
            + T("👥 " + H("social and friends"))
            + "├─ ➕ <code>/addf [tag]</code> (ʀᴇᴘʟʏ) — ᴀᴅᴅ ꜰʀɪᴇɴᴅ\n"
            + "├─ 🏷️ <code>/tag [t1] [t2]</code> — ᴍᴇɴᴛɪᴏɴ ꜰʀɪᴇɴᴅꜱ\n"
            + "├─ 🏷️ <code>/t all</code> — ᴛᴀɢ ᴀʟʟ ꜰʀɪᴇɴᴅꜱ\n"
            + "├─ ✏️ <code>/ctag [old] [new]</code> — ᴄʜᴀɴɢᴇ ᴛᴀɢ\n"
            + "├─ 🗑️ <code>/delf [tag]</code> — ᴅᴇʟᴇᴛᴇ ꜰʀɪᴇɴᴅ\n"
            + "├─ 📜 <code>/allf</code> — ᴀʟʟ ꜰʀɪᴇɴᴅꜱ ʟɪꜱᴛ\n"
            + "├─ 👥 <code>/friend</code> — ꜰʀɪᴇɴᴅꜱ ᴄᴏᴜɴᴛ\n"
            + "├─ 📖 <code>/friends</code> — ꜰʀɪᴇɴᴅ ᴄᴍᴅꜱ ʜᴇʟᴩ\n"
            + "├─ 🎟️ <code>/create_coupon [code] [amt] [max]</code>\n"
            + "├─ 🎫 <code>/coupon [code]</code> — ʀᴇᴅᴇᴇᴍ ᴄᴏᴜᴩᴏɴ\n"
            + "├─ 📊 <code>/status [code]</code> — ᴄᴏᴜᴩᴏɴ ɪɴꜰᴏ\n"
            + "├─ 🗑️ <code>/del_coupon</code> — ᴅᴇʟᴇᴛᴇ ᴄᴏᴜᴩᴏɴ\n"
            + "├─ 💍 <code>/marry</code> (ʀᴇᴘʟʏ) — ᴩʀᴏᴩᴏꜱᴇ\n"
            + "├─ 💔 <code>/divorce</code> — ᴇɴᴅ ʀᴇʟᴀᴛɪᴏɴ\n"
            + "├─ 💕 <code>/relation</code> — ꜱᴛᴀᴛᴜꜱ ᴄᴀʀᴅ\n"
            + "├─ 💌 <code>/confession [text]</code> — ᴀɴᴏɴ ᴄᴏɴꜰᴇꜱꜱ\n"
            + "├─ 💬 <code>/confess</code> (ʀᴇᴘʟʏ) — ꜱᴇɴᴅ ᴛᴏ ᴜꜱᴇʀ\n"
            + "├─ 📝 <code>/setintro [text]</code> — ꜱᴇᴛ ɪɴᴛʀᴏ\n"
            + "└─ 👤 <code>/intro</code> me / (ʀᴇᴘʟʏ) — ꜱᴇᴇ ɪɴᴛʀᴏ\n"
            + "</blockquote>"
        ),
        "help_util": (
            "<blockquote>"
            + T("🧰 " + H("utility tools"))
            + "├─ 🎨 <code>/q</code> (ʀᴇᴘʟʏ) — ǫᴜᴏᴛᴇ ꜱᴛɪᴄᴋᴇʀ\n"
            + "├─ 📦 <code>/own</code> — ᴄʀᴇᴀᴛᴇ ꜱᴛɪᴄᴋᴇʀ ᴩᴀᴄᴋ\n"
            + "├─ 📝 <code>/detail</code> (ʀᴇᴘʟʏ) — ɴᴀᴍᴇ ʜɪꜱᴛᴏʀʏ\n"
            + "├─ 🆔 <code>/id</code> — ᴜꜱᴇʀ / ᴄʜᴀᴛ ɪᴅ\n"
            + "├─ 👑 <code>/admins</code> — ᴀᴅᴍɪɴ ʟɪꜱᴛ\n"
            + "├─ 👑 <code>/owner</code> — ᴛᴀɢ ɢʀᴏᴜᴩ ᴏᴡɴᴇʀ\n"
            + "├─ 🚨 <code>/report</code> (ʀᴇᴘʟʏ) — ʀᴇᴘᴏʀᴛ ᴜꜱᴇʀ\n"
            + "├─ 🗑️ <code>/isdeleted [id]</code> — ᴄʜᴇᴄᴋ ᴀᴄᴄᴏᴜɴᴛ\n"
            + "├─ 🌐 <code>/tr [lang] [text]</code> — ᴛʀᴀɴꜱʟᴀᴛᴇ\n"
            + "├─ 🧮 <code>/calc [expr]</code> — ᴄʟᴀʟᴄᴜʟᴀᴛᴏʀ\n"
            + "├─ 🔊 <code>/voice</code> (ʀᴇᴘʟʏ) — ᴛᴇxᴛ ᴛᴏ ꜱᴩᴇᴇᴄʜ\n"
            + "├─ 😂 <code>/meme</code> — ʀᴀɴᴅᴏᴍ ᴍᴇᴍᴇ\n"
            + "├─ 🤣 <code>/joke</code> — ʀᴀɴᴅᴏᴍ ᴊᴏᴋᴇ\n"
            + "├─ 🧠 <code>/fact</code> — ʀᴀɴᴅᴏᴍ ꜰᴀᴄᴛ\n"
            + "├─ 💬 <code>/quote</code> — ɪɴꜱᴩɪʀᴀᴛɪᴏɴ\n"
            + "├─ 🌦️ <code>/weather [city]</code> — ᴡᴇᴀᴛʜᴇʀ\n"
            + "├─ 🪙 <code>/crypto [coin]</code> — ᴄʀʏᴩᴛᴏ ᴩʀɪᴄᴇ\n"
            + "├─ 🎬 <code>/anime [name]</code> — ᴀɴɪᴍᴇ ɪɴꜰᴏ\n"
            + "├─ 🌸 <code>/waifu</code> — ʀᴀɴᴅᴏᴍ ᴡᴀɪꜰᴜ ɪᴍɢ\n"
            + "├─ 🐱 <code>/neko</code> — ɴᴇᴋᴏ ɪᴍᴀɢᴇ\n"
            + "├─ 📖 <code>/word [w]</code> — ᴅɪᴄᴛɪᴏɴᴀʀʏ\n"
            + "├─ ✨ <code>/ascii [text]</code> — ᴀꜱᴄɪɪ ᴀʀᴛ\n"
            + "├─ 🔄 <code>/reverse [text]</code> — ʀᴇᴠᴇʀꜱᴇ\n"
            + "├─ 😂 <code>/mock [text]</code> — ꜱᴩᴏɴɢᴇʙᴏʙ\n"
            + "└─ 😄 <code>/emojify [text]</code> — ᴀᴅᴅ ᴇᴍᴏᴊɪꜱ\n"
            + "</blockquote>"
        ),
        "help_rec": (
            "<blockquote>"
            + T("🔐 " + H("account recovery"))
            + "├─ ⚠️ ᴅᴍ ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅꜱ ʙᴇʟᴏᴡ~\n"
            + "│\n"
            + "├─ 🔑 <code>/setpass [password]</code> — ꜱᴇᴛ ᴩᴀꜱꜱ\n"
            + "├─ ℹ️ <code>/mpass</code> — ꜱᴇᴇ ʏᴏᴜʀ ᴩᴀꜱꜱ ɪɴ ᴅᴍ\n"
            + "├─ 🔄 <code>/cpass [old] [new]</code> — ᴄʜᴀɴɢᴇ ᴩᴀꜱꜱ\n"
            + "├─ ✅ <code>/transfer [old_id] [pass]</code>\n"
            + "│    ᴏʟᴅ ᴀᴄᴄᴏᴜɴᴛ ᴍᴜꜱᴛ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ\n"
            + "│\n"
            + "└─ 🛡️ ᴀʟʟ ᴅᴀᴛᴀ ꜱᴛᴏʀᴇᴅ ꜱᴀꜰᴇʟʏ ɪɴ ᴛᴜʀꜱᴏ ᴅʙ\n"
            + "</blockquote>"
        ),
        "help_rem": (
            "<blockquote>"
            + T("⏰ " + H("remind rep streak"))
            + "├─ ⏰ <code>/remind 30m|2h|1d [text]</code>\n"
            + "├─ 📋 <code>/myreminders</code> — ᴩᴇɴᴅɪɴɢ ʟɪꜱᴛ\n"
            + "├─ 🗑️ <code>/delreminder [id]</code> — ᴅᴇʟᴇᴛᴇ\n"
            + "│\n"
            + "├─ ⭐ <code>/rep</code> (ʀᴇᴘʟʏ) — ɢɪᴠᴇ ʀᴇᴘ 𝟷𝟸ʜ\n"
            + "├─ 🥇 <code>/toprep</code> — ᴛᴏᴘ ʀᴇᴘᴜᴛᴀᴛɪᴏɴ\n"
            + "├─ 🌟 <code>/topxp</code> — ᴛᴏ🇵 xᴩ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n"
            + "│\n"
            + "├─ 🔥 <code>/streak</code> — ᴅᴀɪʟʏ ꜱᴛʀᴇᴀᴋ ᴄᴀʀᴅ\n"
            + "├─ 📊 <code>/level</code> — xᴩ ᴩʀᴏɢʀᴇꜱꜱ ʙᴀʀ\n"
            + "├─ 🏆 <code>/leaderboard</code> — ᴀʟʟ ʀᴀɴᴋꜱ\n"
            + "├─ 📖 <code>/economy</code> — ᴇᴄᴏɴᴏᴍʏ ɪɴꜰᴏ\n"
            + "├─ 🏓 <code>/ping</code> — ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ\n"
            + "└─ 🤖 <code>/botinfo</code> — ʙᴏᴛ ꜱᴛᴀᴛꜱ\n"
            + "</blockquote>"
        ),
    }

# Callback queries
@app.on_callback_query(filters.regex(r"^(start|help|help_(ai|eco|gems|fun|casino|mod|social|util|rec|rem))$"))
async def on_callback(_, cq: CallbackQuery):
    try:
        await cq.answer()
        d = cq.data
        username = BOT_USERNAME or "riruru_bot"
        H = ff
        def T(title):
            return f"✦ ┌─[ {title} ]\n│\n"

        if d == "start":
            await cq.edit_message_text(
                "<blockquote>"
                + T("🍡 " + H("hello~ i'm riruru!") + " 💕")
                + "├─ 🤖 ⇛ AI chat in DM — just talk to me~\n"
                + "├─ 🎙️ ⇛ voice notes transcribed ✨\n"
                + "├─ 🎨 ⇛ AI images · 🎰 casino + games 💣\n"
                + "├─ 💰 ⇛ economy 🪙 · 🛡️ group moderation\n"
                + "│\n"
                + "└─ 🍡 press Help to explore more commands!\n"
                + "</blockquote>",
                reply_markup=start_keyboard(username)
            )
        elif d == "help":
            await cq.edit_message_text(
                "<blockquote>"
                + T("🌸 " + H("riruru help menu") + " 💕")
                + f"├─ 💰 {ff('economy')} — /daily /rob /kill /bal\n"
                + f"├─ 💎 {ff('gems and powers')} — /gems /powers\n"
                + f"├─ 🎰 {ff('casino')} — /slots /bomb /blackjack\n"
                + f"├─ 🎮 {ff('fun')} — /truth /dare /rizz /roast\n"
                + f"├─ 🛡️ {ff('group mod')} — .ban .mute .warn\n"
                + f"├─ 🤖 {ff('ai and voice')} — /img /voice /bio\n"
                + "│\n"
                + f"└─ 🌸 {ff('tap a button below')}~ 👇\n"
                + "</blockquote>",
                reply_markup=help_keyboard()
            )
        else:
            texts = _help_texts()
            if d in texts:
                await cq.edit_message_text(texts[d], reply_markup=BACK_BTN)
    except Exception:
        traceback.print_exc()

# ══════════════════════════════════════════════════════════════════
#  ✨ v1.1.2 PREMIUM FEATURES
# ══════════════════════════════════════════════════════════════════

ACHIEVEMENT_LABELS = {
    "first_win": "🏆 First Win",
    "bomb_survivor": "💣 Bomb Survivor",
    "jackpot_king": "💎 Jackpot King",
    "streak_7": "🔥 7-Day Streak",
}

SHOP_CACHE = {
    "shield": ("🛡️", "Shield", "Blocks one `/rob` attempt.", 450),
    "lucky_charm": ("🍀", "Lucky Charm", "Boosts your next `/daily` by 50%.", 650),
    "vip_badge": ("👑", "VIP Badge", "Adds a permanent VIP badge to your profile.", 1200),
}

async def profile_text(user_id: int) -> str:
    user = await get_user(user_id)
    if not user:
        return ff("profile load nahi hui~")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*)+1 FROM users WHERE coins>?", (user["coins"],)
        ) as cur:
            rank = (await cur.fetchone() or [0])[0]
        async with db.execute(
            "SELECT achievement_id FROM achievements WHERE user_id=? ORDER BY earned_at",
            (user_id,),
        ) as cur:
            achievements = [row[0] for row in await cur.fetchall()]
    badge = " 👑" if await item_quantity(user_id, "vip_badge") else ""
    medals = " ".join(ACHIEVEMENT_LABELS.get(a, a) for a in achievements) or "—"
    return (
        f"🌸 **ʀɪʀᴜʀᴜ ᴘʀᴏꜰɪʟᴇ**{badge}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {mention(type('User', (), {'first_name': user.get('first_name'), 'id': user_id})())}\n\n"
        f"💰 **ᴄᴏɪɴꜱ:** `{user['coins']}`\n"
        f"🪙 **ᴄʀᴇᴅɪᴛꜱ:** `{user['credits']}`\n"
        f"📈 **ʀᴀɴᴋ:** `#{rank}`\n"
        f"🏆 **ᴡɪɴꜱ:** `{user.get('games_won', 0)}`  ·  **ʟᴏꜱꜱᴇꜱ:** `{user.get('games_lost', 0)}`\n"
        f"🔥 **ᴅᴀɪʟʏ ꜱᴛʀᴇᴀᴋ:** `{user.get('daily_streak', 0)}`\n\n"
        f"✨ **ᴀᴄʜɪᴇᴠᴇᴍᴇɴᴛꜱ:**\n{medals}"
    )

@app.on_message(filters.command("profile"), group=1)
async def cmd_profile(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        await msg.reply(await profile_text(msg.from_user.id))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("richest"), group=1)
async def cmd_richest(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id,first_name,username,coins FROM users ORDER BY coins DESC LIMIT 10"
            ) as cur:
                rows = await cur.fetchall()
        if not rows:
            return await msg.reply(ff("abhi leaderboard khaali hai~"))
        lines = []
        for index, (uid, first_name, username, coins) in enumerate(rows, 1):
            name = f"@{username}" if username else (first_name or f"User {uid}")
            lines.append(f"**{index}.** {name} — `{coins}` 🪙")
        await msg.reply(
            "🏆 **ʀɪʀᴜʀᴜ'ꜱ ʀɪᴄʜᴇꜱᴛ** 💎\n\n"
            + "\n".join(lines)
            + "\n\n_ᴡᴇᴇᴋʟʏ ᴄᴏᴍᴘᴇᴛɪᴛɪᴏɴ~ ᴋᴇᴇᴘ ᴇᴀʀɴɪɴɢ!_",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("shop"), group=1)
async def cmd_shop(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        lines = ["🛍️ **ʀɪʀᴜʀᴜ ꜱʜᴏᴘ** 💕", ""]
        for item_id, (emoji, name, description, price) in SHOP_CACHE.items():
            lines.append(f"{emoji} **{name}** — `{price}` 🪙\n_{description}_\n")
        lines.append("_ᴜꜱᴇ `/buy shield`, `/buy lucky_charm`, or `/buy vip_badge`~_")
        await msg.reply("\n".join(lines), parse_mode=enums.ParseMode.HTML)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("buy"), group=1)
async def cmd_buy(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        item_id = msg.command[1].lower().replace("-", "_") if len(msg.command) > 1 else ""
        if item_id not in SHOP_CACHE:
            return await msg.reply(ff("/buy [shield|lucky_charm|vip_badge]"))
        _, name, _, price = SHOP_CACHE[item_id]
        if not await debit_coins(msg.from_user.id, price):
            return await msg.reply(f"🥺 **ᴄᴏɪɴꜱ ᴋᴀᴍ ʜᴀɪɴ~** `{price}` 🪙 ᴄʜᴀʜɪʏᴇ")
        await add_item(msg.from_user.id, item_id)
        await msg.reply(f"✅ **{name} ᴜɴʟᴏᴄᴋᴇᴅ~**\n_{ff('thanks for shopping with Riruru')}_ 💕")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command(["inv", "inventory"]), group=1)
async def cmd_inventory(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT item_id,quantity FROM inventory WHERE user_id=? AND quantity>0",
                (msg.from_user.id,),
            ) as cur:
                rows = await cur.fetchall()
        if not rows:
            return await msg.reply("🎒 **ɪɴᴠᴇɴᴛᴏʀʏ**\n\n_ᴋᴜᴄʜ ɴᴀʜɪ ʜᴀɪ ᴀʙʜɪ~ `/shop` ᴅᴇᴋʜᴏ_")
        lines = []
        for item_id, quantity in rows:
            item = SHOP_CACHE.get(item_id)
            lines.append(f"{item[0] if item else '✨'} **{item[1] if item else item_id}** × `{quantity}`")
        await msg.reply("🎒 **ᴍʏ ɪɴᴠᴇɴᴛᴏʀʏ** 💕\n\n" + "\n".join(lines))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("use"), group=1)
async def cmd_use(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        item_id = msg.command[1].lower().replace("-", "_") if len(msg.command) > 1 else ""
        if item_id == "lucky_charm":
            return await msg.reply("🍀 **ʟᴜᴄᴋʏ ᴄʜᴀʀᴍ** ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅ ᴘᴇʀ ᴀᴜᴛᴏ-ᴇǫᴜɪᴩᴩᴇᴅ~")
        if item_id == "shield":
            return await msg.reply("🛡️ **ꜱʜɪᴇʟᴅ** ɪꜱ ᴀᴜᴛᴏ-ᴜꜱᴇᴅ ᴡʜᴇɴ ꜱᴏᴍᴇᴏɴᴇ ʀᴏʙꜱ ʏᴏᴜ~")
        await msg.reply(ff("use karne ke liye /use [shield|lucky_charm]"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("roulette"), group=1)
async def cmd_roulette(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        if len(msg.command) < 3:
            return await msg.reply("🎡 `/roulette [bet] [red|black|odd|even|0-36]`")
        bet = parse_bet(msg)
        choice = msg.command[2].lower()
        valid = {"red", "black", "odd", "even"} | {str(n) for n in range(37)}
        if not bet or choice not in valid:
            return await msg.reply(ff("valid bet aur choice do~"))
        if not await debit_coins(msg.from_user.id, bet):
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~")
        spin = await msg.reply("🎡 **ʀᴏᴜʟᴇᴛᴛᴇ ꜱᴘɪɴɴɪɴɢ~**\n\n`🔴  ⚫  🟢  ...`")
        await asyncio.sleep(0.8)
        number = random.randint(0, 36)
        red_numbers = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        color = "green" if number == 0 else ("red" if number in red_numbers else "black")
        won = choice == str(number) or choice == color or (
            choice == "odd" and number > 0 and number % 2 == 1
        ) or (choice == "even" and number > 0 and number % 2 == 0)
        multiplier = 35 if choice.isdigit() else 2
        payout = bet * multiplier if won else 0
        if payout:
            await update_coins(msg.from_user.id, payout)
        await record_game(msg.from_user.id, "roulette", won)
        result = (
            f"🎡 **ʀᴏᴜʟᴇᴛᴛᴇ**\n\n"
            f"**{number}** · {'🟢' if color == 'green' else ('🔴' if color == 'red' else '⚫')} `{color}`\n\n"
            f"{'🎉 **ʏᴏᴜ ᴡᴏɴ~** +' + str(payout) if won else '🥺 **ɴᴏ ʟᴜᴄᴋ~** -' + str(bet)} 🪙"
        )
        await spin.edit(result)
        roulette_mood = 'excited' if won else 'sobbing'
        await send_mood(app, msg.chat.id, roulette_mood,
            f"{'🎉 ᴡᴏɴ~ +' + str(payout) if won else '🥺 ɴᴏ ʟᴜᴄᴋ~ -' + str(bet)} 🪙"
        )
    except Exception:
        traceback.print_exc()

MINE_SESSIONS = {}

def mine_keyboard(uid, revealed=None, over=False):
    revealed = revealed or set()
    rows = []
    for index in range(9):
        if index % 3 == 0:
            rows.append([])
        label = "✅" if index in revealed else ("💣" if over else "🟦")
        style = "success" if index in revealed else ("danger" if over else "primary")
        rows[-1].append(InlineKeyboardButton(
            label, callback_data=f"mine_pick_{uid}_{index}", style=style
        ))
    if not over:
        rows.append([InlineKeyboardButton("💰 ᴄᴀꜱʜ ᴏᴜᴛ", callback_data=f"mine_cash_{uid}", style="success")])
    return InlineKeyboardMarkup(rows)

@app.on_message(filters.command(["minerush", "mine"]), group=1)
async def cmd_minerush(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg)
        if not bet:
            return await msg.reply("⚡ `/minerush [bet]` — ᴍɪɴ 𝟷𝟶 ᴄᴏɪɴꜱ~ 𝟷𝟻 ꜱᴇᴄᴏɴᴅ ʀᴜꜱʜ")
        uid = msg.from_user.id
        if uid in MINE_SESSIONS:
            return await msg.reply("⚡ ᴛᴇʀᴀ ᴇᴋ ᴍɪɴᴇ ʀᴜꜱʜ ᴀʟʀᴇᴀᴅʏ ᴄʜᴀʟ ʀᴀʜᴀ~")
        if not await debit_coins(uid, bet):
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~")
        MINE_SESSIONS[uid] = {
            "bet": bet, "bombs": set(random.sample(range(9), 2)),
            "revealed": set(), "deadline": time.time() + 15,
        }
        await msg.reply(
            "⚡ **ᴍɪɴᴇ ʀᴜꜱʜ** 💥\n\n_𝟷𝟻 ꜱᴇᴄᴏɴᴅꜱ~ ꜰᴀꜱᴛᴇʀ ᴄʟɪᴄᴋꜱ, ʙɪɢɢᴇʀ ᴍᴜʟᴛɪᴩʟɪᴇʀ!_",
            reply_markup=mine_keyboard(uid),
        )
    except Exception:
        traceback.print_exc()

@app.on_callback_query(filters.regex(r"^mine_(pick|cash)_(\d+)(?:_(\d+))?$"))
async def mine_callback(_, cq: CallbackQuery):
    try:
        parts = cq.data.split("_")
        action, uid = parts[1], int(parts[2])
        if cq.from_user.id != uid:
            return await cq.answer("ʏᴇ ᴛᴇʀɪ ɢᴀᴍᴇ ɴᴀʜɪ~ 🥺", show_alert=True)
        session = MINE_SESSIONS.get(uid)
        if not session:
            return await cq.answer("ʀᴜꜱʜ ᴇxᴩɪʀᴇᴅ~ /minerush ꜱᴇ ᴩʜɪʀ ꜱᴇ ᴋᴀʀᴏ", show_alert=True)
        await cq.answer()
        if time.time() > session["deadline"]:
            MINE_SESSIONS.pop(uid, None)
            await record_game(uid, "minerush", False)
            return await cq.edit_message_text("⏱️ **ᴛɪᴍᴇ ᴜᴩ~**\n\n-`" + str(session["bet"]) + "` 🪙 ʟᴏꜱᴛ~")
        if action == "cash":
            safe = len(session["revealed"])
            if safe < 1:
                return await cq.answer("ᴩᴇʜʟᴇ ᴛɪʟᴇ ᴛᴏ ᴋʜᴏʟᴏ~", show_alert=True)
            win = int(session["bet"] * (1.3 ** safe))
            MINE_SESSIONS.pop(uid, None)
            await update_coins(uid, win)
            await record_game(uid, "minerush", True)
            await cq.edit_message_text(f"⚡ **ᴄᴀꜱʜᴇᴅ ᴏᴜᴛ~**\n\n+`{win}` 🪙 🎉")
            await send_mood(app, chat_id, 'excited', f"⚡ ᴄᴀꜱʜᴇᴅ ᴏᴜᴛ~ +<code>{win}</code> 🪙 🎉")
            return
        index = int(parts[3])
        if not 0 <= index < 9:
            return await cq.answer("ɪɴᴠᴀʟɪᴅ ᴛɪʟᴇ~", show_alert=True)
        if index in session["revealed"]:
            return await cq.answer("ᴀʟʀᴇᴀᴅʏ ᴋʜᴏʟᴀ ʜᴀɪ~")
        if index in session["bombs"]:
            MINE_SESSIONS.pop(uid, None)
            await record_game(uid, "minerush", False)
            await cq.edit_message_text(
                f"💥 **ʙᴏᴏᴍ!**\n\n-`{session['bet']}` 🪙 ʟᴏꜱᴛ~",
                reply_markup=mine_keyboard(uid, session["revealed"], over=True),
            )
            await send_mood(app, chat_id, 'worried', f"💥 ʙᴏᴏᴍ! -<code>{session['bet']}</code> 🪙 ʟᴏꜱᴛ~")
            return
        session["revealed"].add(index)
        safe = len(session["revealed"])
        multiplier = round(1.3 ** safe, 2)
        await cq.edit_message_text(
            f"⚡ **ᴍɪɴᴇ ʀᴜꜱʜ** · `{15 - int(time.time() - (session['deadline'] - 15))}s`\n"
            f"✅ ꜱᴀꜰᴇ: `{safe}` · 📈 `{multiplier}x`\n"
            f"💰 ᴘᴏᴛᴇɴᴛɪᴀʟ: `{int(session['bet'] * multiplier)}` 🪙",
            reply_markup=mine_keyboard(uid, session["revealed"]),
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("quiz"), group=1)
async def cmd_quiz(_, msg: Message):
    questions = [
        ("Which planet is known as the Red Planet?", ["Earth", "Mars", "Venus", "Jupiter"], 1),
        ("What is 7 × 8?", ["48", "54", "56", "63"], 2),
        ("What do plants absorb?", ["O2", "N2", "CO2", "H2"], 2),
    ]
    question, options, answer = random.choice(questions)
    try:
        if not msg.from_user or await is_banned(msg.from_user.id):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        poll_type = getattr(getattr(enums, "PollType", None), "QUIZ", "quiz")
        await app.send_poll(
            msg.chat.id, question, options, is_anonymous=False, type=poll_type,
            correct_option_id=answer, explanation="ʀɪʀᴜʀᴜ ᴋᴇᴇᴩꜱ ᴀɴ ᴇʏᴇ ᴏɴ ʏᴏᴜ~ 🍡",
        )
    except Exception as exc:
        print(f"  Quiz error: {type(exc).__name__}: {str(exc)[:180]}")
        await msg.reply(ff("quiz poll nahi bhej paayi~ mujhe poll bhejne ki permission do 🥺"))

HEIST_SESSIONS = {}

def heist_keyboard(chat_id):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("💰 ᴊᴏɪɴ ʜᴇɪꜱᴛ", callback_data=f"heist_join_{chat_id}", style="success"),
        InlineKeyboardButton("🚪 ᴏᴘᴇɴ ᴠᴀᴜʟᴛ", callback_data=f"heist_open_{chat_id}", style="primary"),
    ]])

@app.on_message(filters.command("heist") & filters.group)
async def cmd_heist(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        bet = parse_bet(msg, 25)
        if not bet:
            return await msg.reply("💰 `/heist [bet]` — ᴍɪɴ 𝟸𝟻 ᴄᴏɪɴꜱ~ 𝟹+ ᴘʟᴀʏᴇʀꜱ")
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        if msg.chat.id in HEIST_SESSIONS:
            return await msg.reply(ff("ek heist already gathering hai~"))
        if not await debit_coins(msg.from_user.id, bet):
            return await msg.reply("🥺 ᴛᴇʀᴇ ᴩᴀꜱ ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ~")
        HEIST_SESSIONS[msg.chat.id] = {
            "creator": msg.from_user.id, "bet": bet, "members": {msg.from_user.id: bet},
            "expires": time.time() + 120,
        }
        await msg.reply(
            f"🏦 **ᴠᴀᴜʟᴛ ʜᴇɪꜱᴛ ᴏᴘᴇɴ~**\n\n"
            f"💰 ᴇɴᴛʀʏ: `{bet}` 🪙 · 👥 ᴍɪɴ: `3`\n"
            f"_ᴛᴇᴀᴍ ʙᴀɴᴀᴏ, ᴘʜɪʀ ᴏᴡɴᴇʀ ᴏᴘᴇɴ ᴠᴀᴜʟᴛ ᴅᴀʙᴀʏᴇ~_",
            reply_markup=heist_keyboard(msg.chat.id),
        )
    except Exception:
        traceback.print_exc()

@app.on_callback_query(filters.regex(r"^heist_(join|open)_(-?\d+)$"))
async def heist_callback(_, cq: CallbackQuery):
    try:
        action, chat_id = cq.data.split("_")[1], int(cq.data.split("_")[2])
        if not cq.message or cq.message.chat.id != chat_id:
            return await cq.answer("ʏᴇ ʏᴀʜᴀɴ ᴋɪ ʜᴇɪꜱᴛ ɴᴀʜɪ~", show_alert=True)
        session = HEIST_SESSIONS.get(chat_id)
        if not session or time.time() > session["expires"]:
            HEIST_SESSIONS.pop(chat_id, None)
            return await cq.answer("ʜᴇɪꜱᴛ ᴇxᴩɪʀᴇᴅ~", show_alert=True)
        uid = cq.from_user.id
        await cq.answer()
        await ensure_user(uid, cq.from_user.username, cq.from_user.first_name)
        if action == "join":
            if uid in session["members"]:
                return await cq.answer("ᴛᴜ ᴀʟʀᴇᴀᴅʏ ɪɴ ʜᴀɪ~")
            if not await debit_coins(uid, session["bet"]):
                return await cq.answer("ᴄᴏɪɴꜱ ᴋᴀᴍ ʜᴀɪɴ~", show_alert=True)
            session["members"][uid] = session["bet"]
            return await cq.answer("ᴛᴇᴀᴍ ᴍᴇ ᴀᴀ ɢᴀʏᴀ~ 💕")
        if uid != session["creator"]:
            return await cq.answer("ꜱɪʀꜰ ʜᴇɪꜱᴛ ᴏᴡɴᴇʀ ᴏᴘᴇɴ ᴋᴀʀᴇ~", show_alert=True)
        if len(session["members"]) < 3:
            return await cq.answer("ᴛʜʀᴇᴇ ᴘʟᴀʏᴇʀꜱ ᴄʜᴀʜɪʏᴇ~", show_alert=True)
        members = list(session["members"])
        pot = sum(session["members"].values())
        multiplier = random.choice([1.5, 2, 2.5, 3])
        total = int(pot * multiplier)
        split = total // len(members)
        HEIST_SESSIONS.pop(chat_id, None)
        for member in members:
            await update_coins(member, split)
            await record_game(member, "heist", True)
        await cq.edit_message_text(
            f"🏦 **ᴠᴀᴜʟᴛ ᴄʀᴀᴄᴋᴇᴅ~** 🎉\n\n"
            f"👥 ᴛᴇᴀᴍ: `{len(members)}` · 📈 `{multiplier}x`\n"
            f"💰 ᴘᴏᴛ: `{total}` 🪙 · **ᴇᴀᴄʜ:** `{split}` 🪙"
        )
        await send_mood(app, chat_id, 'cool',
            f"🏦 ᴠᴀᴜʟᴛ ᴄʀᴀᴄᴋᴇᴅ~ 🎉\n👥 `{len(members)}` · 📈 `{multiplier}x`\n💰 ᴇᴀᴄʜ: `{split}` 🪙"
        )
    except Exception:
        traceback.print_exc()

def lottery_round_key():
    return datetime.utcnow().date().isoformat()

@app.on_message(filters.command("lottery"), group=1)
async def cmd_lottery(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg, 10)
        if not bet:
            return await msg.reply("🎟️ `/lottery [bet]` — ᴅᴀɪʟʏ ᴘᴏᴏʟ, ᴡɪɴɴᴇʀ ᴅʀᴀᴡɴ ᴇᴠᴇʀʏ 𝟸𝟺ʜ~")
        round_key = lottery_round_key()
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT 1 FROM lottery_entries WHERE chat_id=? AND user_id=? AND round_key=?",
                (msg.chat.id, msg.from_user.id, round_key),
            ) as cur:
                if await cur.fetchone():
                    return await msg.reply(ff("is round me ek hi entry allowed hai~"))
            async with db.execute(
                "UPDATE users SET coins=coins-? WHERE user_id=? AND coins>=? RETURNING coins",
                (bet, msg.from_user.id, bet),
            ) as debit:
                if await debit.fetchone() is None:
                    await db.rollback()
                    return await msg.reply("🥺 ᴄᴏɪɴꜱ ᴋᴀᴍ ʜᴀɪɴ~")
            await db.execute(
                "INSERT INTO lottery_entries(chat_id,user_id,amount,round_key) VALUES (?,?,?,?)",
                (msg.chat.id, msg.from_user.id, bet, round_key),
            )
            await db.commit()
            async with db.execute(
                "SELECT COUNT(*),COALESCE(SUM(amount),0) FROM lottery_entries WHERE chat_id=? AND round_key=?",
                (msg.chat.id, round_key),
            ) as cur:
                count, pot = await cur.fetchone()
        await msg.reply(f"🎟️ **ʟᴏᴛᴛᴇʀʏ ᴇɴᴛʀʏ ᴄᴏɴꜰɪʀᴍᴇᴅ~**\n\n👥 `{count}` ᴇɴᴛʀɪᴇꜱ · 💰 ᴘᴏᴛ `{pot}` 🪙")
    except Exception:
        traceback.print_exc()

async def draw_lotteries():
    old_round = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT DISTINCT chat_id FROM lottery_entries WHERE round_key=?",
            (old_round,),
        ) as cur:
            chats = [row[0] for row in await cur.fetchall()]
    for chat_id in chats:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id,amount FROM lottery_entries WHERE chat_id=? AND round_key=?",
                (chat_id, old_round),
            ) as cur:
                entries = await cur.fetchall()
            if not entries:
                continue
            async with db.execute(
                "SELECT 1 FROM lottery_draws WHERE chat_id=? AND round_key=?",
                (chat_id, old_round),
            ) as cur:
                if await cur.fetchone():
                    continue
            winner = random.choices([row[0] for row in entries], weights=[row[1] for row in entries])[0]
            pot = sum(row[1] for row in entries)
            await db.execute(
                "INSERT INTO lottery_draws(chat_id,round_key,winner_id,pot) VALUES (?,?,?,?)",
                (chat_id, old_round, winner, pot),
            )
            await db.commit()
        await update_coins(winner, pot)
        await unlock_achievement(winner, "jackpot_king")
        try:
            await send_mood(app, chat_id, 'greedy',
                f"🎟️ **ʟᴏᴛᴛᴇʀʏ ᴅʀᴀᴡ~** 🎉\n\n🏆 ᴡɪɴɴᴇʀ: [ᴡɪɴɴᴇʀ](tg://user?id={winner})\n💎 ᴘᴏᴛ: `{pot}` 🪙"
            )
        except Exception:
            traceback.print_exc()

async def lottery_worker():
    while True:
        try:
            await draw_lotteries()
        except Exception:
            traceback.print_exc()
        await asyncio.sleep(3600)

# ─── GROUP PREMIUM CONTROLS ────────────────────────────────────────
@app.on_message(filters.command(["ai", "mochi"]) & filters.group)
async def cmd_group_ai(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("sirf group admins AI mode change kar sakte hain~"))
        args = [part.lower() for part in msg.command[1:]]
        if msg.command and msg.command[0].lower() == "mochi" and args and args[0] == "ai":
            args = args[1:]
        arg = args[0] if args else ""
        if arg in ("on", "mention"):
            enabled, mode = 1, "mention"
        elif arg in ("always", "all"):
            enabled, mode = 1, "always"
        elif arg in ("off", "never", "unalways", "disable"):
            enabled, mode = 0, "mention"
        else:
            return await msg.reply(
                "🌸 `/ai mention` · `/ai always` · `/ai off`\n"
                "ᴏʀ `/mochi ai always` ᴛᴏ ᴛᴜʀɴ ᴏɴ ᴀʟᴡᴀʏꜱ ᴍᴏᴅᴇ~"
            )
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO groups(chat_id,ai_enabled,ai_mode) VALUES (?,?,?) "
                "ON CONFLICT(chat_id) DO UPDATE SET ai_enabled=excluded.ai_enabled, ai_mode=excluded.ai_mode",
                (msg.chat.id, enabled, mode),
            )
            await db.commit()
        description = "ᴍᴇɴᴛɪᴏɴ ᴏʀ ʀᴇᴩʟʏ ᴍᴏᴅᴇ" if mode == "mention" else "ᴀʟᴡᴀʏꜱ ᴍᴏᴅᴇ · ᴛʜʀᴏᴛᴛʟᴇᴅ ᴛᴏ 𝟷 ʀᴇᴩʟʏ/𝟷𝟸s"
        await msg.reply(f"🌸 **ʀɪʀᴜʀᴜ ɢʀᴏᴜᴩ ᴀɪ {'ON' if enabled else 'OFF'}~**\n_{description}_")
    except Exception:
        traceback.print_exc()
    
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("warn") & filters.group)
async def cmd_warn(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("sirf group admins warn kar sakte hain~"))
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karke /warn [reason] use karo~"))
        await ensure_user(target.id, target.username, target.first_name)
        reason = " ".join(msg.command[1:]).strip() or "no reason given"
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO warn_records(chat_id,user_id,reason,issued_by) VALUES (?,?,?,?)",
                (msg.chat.id, target.id, reason, msg.from_user.id),
            )
            await db.execute(
                "UPDATE users SET warnings=warnings+1 WHERE user_id=?", (target.id,)
            )
            await db.commit()
            async with db.execute(
                "SELECT COUNT(*) FROM warn_records WHERE chat_id=? AND user_id=?",
                (msg.chat.id, target.id),
            ) as cur:
                count = (await cur.fetchone() or [0])[0]
        if count >= 3:
            await app.ban_chat_member(msg.chat.id, target.id)
            await app.send_message(target.id, "🚫 ʀɪʀᴜʀᴜ ɴᴇ ᴛᴜᴍʜᴇ ɢʀᴏᴜᴩ ꜱᴇ ʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ~ 🥺 ʙᴇ ɢᴏᴏᴅ ɴᴇxᴛ ᴛɪᴍᴇ~")
            await send_mood(app, msg.chat.id, 'furious',
                f"🚫 {mention(target)} **ʙᴀɴɴᴇᴅ** — `3/3` ᴡᴀʀɴꜱ"
            )
        else:
            await send_mood(app, msg.chat.id, 'serious',
                f"⚠️ {mention(target)} **ᴡᴀʀɴᴇᴅ** — `{count}/3`\n_{reason}_"
            )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("warnings") & filters.group)
async def cmd_warnings(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT reason,issued_at FROM warn_records WHERE chat_id=? AND user_id=? ORDER BY id DESC LIMIT 10",
                (msg.chat.id, target.id),
            ) as cur:
                rows = await cur.fetchall()
        if not rows:
            return await msg.reply(f"✅ {mention(target)} ᴋᴇ ᴋᴏɪ ᴡᴀʀɴꜱ ɴᴀʜɪ~")
        details = "\n".join(f"• {reason}" for reason, _ in rows)
        await msg.reply(f"⚠️ **ᴡᴀʀɴɪɴɢꜱ ᴏꜰ** {mention(target)} · `{len(rows)}/3`\n\n{details}")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("resetwarn") & filters.group)
async def cmd_resetwarn(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        return await msg.reply(ff("sirf group admins reset kar sakte hain~"))
    target = msg.reply_to_message.from_user if msg.reply_to_message else None
    if not target:
        return await msg.reply(ff("reply karke /resetwarn use karo~"))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM warn_records WHERE chat_id=? AND user_id=?", (msg.chat.id, target.id))
        await db.execute("UPDATE users SET warnings=0 WHERE user_id=?", (target.id,))
        await db.commit()
    await send_mood(app, msg.chat.id, 'peaceful',
        f"✅ {mention(target)} ᴋᴇ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ~"
    )

@app.on_message(filters.command("note") & filters.group)
async def cmd_note(_, msg: Message):
    args = msg.command[1:]
    if not args:
        return await msg.reply(ff("/note [name] [text]  ·  /note [name] to read"))
    key = args[0].lower()
    if len(args) == 1:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT note_value FROM group_notes WHERE chat_id=? AND note_key=?",
                (msg.chat.id, key),
            ) as cur:
                row = await cur.fetchone()
        return await msg.reply(
            f"📝 **{key}**\n\n{row[0]}" if row else ff("ye note mila nahi~")
        )
    if not await is_admin(msg.chat.id, msg.from_user.id):
        return await msg.reply(ff("sirf group admins notes save kar sakte hain~"))
    value = " ".join(args[1:])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO group_notes(chat_id,note_key,note_value,created_by) VALUES (?,?,?,?) "
            "ON CONFLICT(chat_id,note_key) DO UPDATE SET note_value=excluded.note_value,updated_at=datetime('now')",
            (msg.chat.id, key, value, msg.from_user.id),
        )
        await db.commit()
    await send_mood(app, msg.chat.id, 'cute_smile', f"📝 <b>ɴᴏᴛᴇ ꜱᴀᴠᴇᴅ~</b> <code>{key}</code> ✅")

@app.on_message(filters.command("notes") & filters.group)
async def cmd_notes(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT note_key FROM group_notes WHERE chat_id=? ORDER BY note_key", (msg.chat.id,)
            ) as cur:
                rows = await cur.fetchall()
        await send_mood(app, msg.chat.id, 'curious',
            "📝 **ɢʀᴏᴜᴘ ɴᴏᴛᴇꜱ**\n\n" + (
            "\n".join(f"• `{row[0]}`" for row in rows) if rows else ff("koi notes nahi~")
        ))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("addnote") & filters.group)
async def cmd_addnote(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        args = msg.command[1:]
        if len(args) < 2:
            return await send_mood(app, msg.chat.id, 'confused',
                ff("/addnote [name] [text]"), parse_mode=enums.ParseMode.HTML)
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await send_mood(app, msg.chat.id, 'worried',
                ff("sirf group admins notes save kar sakte hain~"), parse_mode=enums.ParseMode.HTML)
        key = args[0].lower()
        value = " ".join(args[1:])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO group_notes(chat_id,note_key,note_value,created_by) VALUES (?,?,?,?) "
                "ON CONFLICT(chat_id,note_key) DO UPDATE SET note_value=excluded.note_value,updated_at=datetime('now')",
                (msg.chat.id, key, value, msg.from_user.id),
            )
            await db.commit()
        await send_mood(app, msg.chat.id, 'cute_smile',
            f"📝 <b>ɴᴏᴛᴇ ꜱᴀᴠᴇᴅ~</b> <code>{key}</code> ✅\n\n{value[:200]}")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("delnote") & filters.group)
async def cmd_delnote(_, msg: Message):
    if not await is_admin(msg.chat.id, msg.from_user.id):
        return await msg.reply(ff("sirf group admins notes delete kar sakte hain~"))
    key = msg.command[1].lower() if len(msg.command) > 1 else ""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT note_value FROM group_notes WHERE chat_id=? AND note_key=?", (msg.chat.id, key)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return await msg.reply(ff("ye note mila nahi~"))
        await db.execute("DELETE FROM group_notes WHERE chat_id=? AND note_key=?", (msg.chat.id, key))
        await db.commit()
    await send_mood(app, msg.chat.id, 'annoyed', f"🗑️ <b>ɴᴏᴛᴇ ᴅᴇʟᴇᴛᴇᴅ~</b> <code>{key}</code>")

# ─── AI CHAT (DM) ─────────────────────────────────────────────────
ALL_CMDS = [
    "start","help","img","credits","wallet","admin","daily","work",
    "crime","rob","pay","ship","roll","trivia","kiss","slap","hug",
    "punch","kick","setwelcome","welcome","delwelcome","save","stop",
    "filters","ban","unban","stats","broadcast","addcredits",
    "deductcredits","addcoins","gban","ungban",
    "slots","blackjack","coinflip","diceduel","bomb","roulette","minerush",
    "richest","profile","shop","buy","inv","inventory","use","heist","lottery","quiz","mine",
    "warn","warnings","resetwarn","note","notes","delnote","ai"
]

@app.on_message(filters.private & filters.text & ~filters.command(ALL_CMDS))
async def ai_chat(_, msg: Message):
    try:
        # Admin panel broadcast capture (pending target chosen from panel)
        if msg.from_user and msg.from_user.id in ADMINS and msg.from_user.id in PENDING_BROADCASTS:
            _tgt = PENDING_BROADCASTS.pop(msg.from_user.id)
            await do_broadcast(app, msg, _tgt)
            return
        # Maintenance mode + bot-ban gate (admins bypass)
        if await _maint_block(msg):
            return
        if await is_banned(msg.from_user.id):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        await msg.reply_chat_action(enums.ChatAction.TYPING)
        await increment_messages(msg.from_user.id)
        history = await get_history(msg.from_user.id)
        reply   = await riruru_reply(msg.text, history, await user_mood(msg.from_user.id),
                                     user_id=msg.from_user.id)
        if not reply:
            return
        await save_message(msg.from_user.id, "user", msg.text)
        await save_message(msg.from_user.id, "assistant", reply)
        # AI replies are TEXT ONLY — no face photos (user request)
        await msg.reply(reply)
    except Exception:
        traceback.print_exc()

# ─── VOICE DECODER ────────────────────────────────────────────────
@app.on_message(filters.voice)
async def voice_handler(_, msg: Message):
    path = None
    try:
        if not msg.from_user or await is_banned(msg.from_user.id):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        status = await msg.reply(f"🎙️ ᴛʀᴀɴꜱᴄʀɪʙɪɴɢ~ ✨")
        path = await msg.download()
        transcript = await transcribe_voice(path)
        os.remove(path)
        reply_msg = await riruru_reply(
            f"User sent a voice note saying: '{transcript}'. React cutely to it!",
            mood=await user_mood(msg.from_user.id),
            user_id=msg.from_user.id,
        )
        if not reply_msg:
            reply_msg = "haha acha tha 😄"
        await status.edit(
            f"🎙️ **{ff('Decoded')}** ✨\n_{transcript}_\n\n"
            f"🌸 **ʀɪʀᴜʀᴜ ꜱᴀʏꜱ:** {reply_msg}"
        )
    except Exception:
        traceback.print_exc()
        try:
            await msg.reply("aww~ voice decode nahi hua 🥺 dobara try karo~")
        except Exception:
            pass
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

# ─── /img ─────────────────────────────────────────────────────────
@app.on_message(filters.command("img"), group=1)
async def cmd_img(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        if await is_banned(msg.from_user.id):
            return

        prompt = " ".join(msg.command[1:]).strip()
        if not prompt:
            return await msg.reply(ff("ek prompt de /img beautiful anime girl 🙄"))

        # /img is FREE — the old credit gate is removed (credits were unearnable:
        # /daily and /work pay users.coins, never credits).
        status = await msg.reply(f"🎨 {ff('generating...')} ✨")
        import urllib.parse
        url = (
            f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
            f"?width=1024&height=1024&nologo=true&enhance=true"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=40)) as r:
                if r.status != 200:
                    raise Exception(f"HTTP {r.status}")
                img_data = await r.read()

        await status.delete()
        await msg.reply_photo(
            BytesIO(img_data),
            caption=(
                f"🎨 <b>{ff('AI Image')}</b>\n<i>{prompt}</i>\n\n"
                f"<i>free ✨</i>"
            ),
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        traceback.print_exc()
        try:
            await msg.reply(ff("image generate nahi hui 💀 dobara try kar"))
        except Exception:
            pass

# ─── /credits /wallet ─────────────────────────────────────────────
@app.on_message(filters.command(["credits","wallet"]), group=1)
async def cmd_credits(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        await msg.reply(
            f"💼 **{ff('Wallet')}** — {mention(msg.from_user)}\n\n"
            f"🪙 **{ff('Credits')}:** `{user['credits']}`\n"
            f"💰 **{ff('Coins')}:** `{user['coins']}`\n\n"
            f"_{ff('earn more with /daily /work /crime')}_"
        )
    except Exception:
        traceback.print_exc()

# ─── ECONOMY ──────────────────────────────────────────────────────
WORK_JOBS = [
    ("delivered pizza to 47 houses 🍕", 80, 150),
    ("coded someone's assignment 💻",   100, 200),
    ("sold chai on the street ☕",       60, 120),
    ("walked someone's dog in rain 🐕", 50, 100),
    ("moderated a Discord for 6h 😭",  90, 180),
]
CRIME_JOBS = [
    ("stole a politician's speech 📄",  200, 400, True),
    ("hacked into a WiFi router 🕵️",   150, 350, True),
    ("scammed a scammer 😈",            300, 500, True),
    ("got caught shoplifting 🚓",      -100, -50, False),
    ("slipped mid-heist on banana 🍌",  -80, -20, False),
]

@app.on_message(filters.command("daily"), group=1)
async def cmd_daily(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        cd = cooldown_left(user["daily_last"], 24)
        if cd:
            return await send_mood(app, msg.chat.id, 'annoyed', await cooldown_text("daily", cd))
        today = datetime.utcnow().date()
        yesterday = (today - timedelta(days=1)).isoformat()
        streak = user.get("daily_streak", 0) + 1 if user.get("daily_streak_date") == yesterday else 1
        reward = random.randint(150, 300)
        if streak >= 7:
            reward *= 3
            await unlock_achievement(msg.from_user.id, "streak_7")
        if await consume_item(msg.from_user.id, "lucky_charm"):
            reward = int(reward * 1.5)
        await update_coins(msg.from_user.id, reward)
        await set_cooldown(msg.from_user.id, "daily_last")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET daily_streak=?,daily_streak_date=? WHERE user_id=?",
                (streak, today.isoformat(), msg.from_user.id),
            )
            await db.commit()
        daily_mood = 'party' if streak >= 7 else 'excited'
        bonus = ' · 𝟹× ᴡᴇᴇᴋʟʏ ʙᴏɴᴜꜱ~' if streak >= 7 else ''
        await send_mood(app, msg.chat.id, daily_mood,
            f"🎁 <b>{ff('Daily Reward')}</b>\n\n"
            f"+<code>{reward}</code> {ff('coins')} credited! 💰\n"
            f"🔥 <b>ꜱᴛʀᴇᴀᴋ:</b> <code>{streak}</code> days{bonus}\n"
            f"<i>ᴄᴀʟ ᴅᴏʙᴀʀᴀ ᴀᴀɴᴀ~ 💕</i>"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("work"), group=1)
async def cmd_work(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        cd = cooldown_left(user["work_last"], 1)
        if cd:
            return await msg.reply(await cooldown_text("work", cd))
        desc, lo, hi = random.choice(WORK_JOBS)
        earned = random.randint(lo, hi)
        await update_coins(msg.from_user.id, earned)
        await set_cooldown(msg.from_user.id, "work_last")
        await send_mood(app, msg.chat.id, 'cheerful',
            f"💼 **{ff('Work Done')}**\n\ntu {desc}\n+`{earned}` {ff('coins')}! 💰"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("crime"), group=1)
async def cmd_crime(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        cd = cooldown_left(user["crime_last"], 2)
        if cd:
            return await msg.reply(await cooldown_text("crime", cd))
        desc, lo, hi, success = random.choice(CRIME_JOBS)
        amount = abs(random.randint(lo, hi))
        await set_cooldown(msg.from_user.id, "crime_last")
        if success:
            await update_coins(msg.from_user.id, amount)
            await send_mood(app, msg.chat.id, 'cool', f"😈 <b>{ff('Crime Win')}</b>\ntu {desc}\n+<code>{amount}</code> {ff('coins')}! 💰")
        else:
            await debit_coins(msg.from_user.id, amount)
            await send_mood(app, msg.chat.id, 'worried', f"🚓 <b>{ff('Crime Fail')}</b>\ntu {desc}\n-<code>{amount}</code> {ff('coins')} fine 😭")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("rob"), group=1)
async def cmd_rob(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        cd = cooldown_left(user["rob_last"], 6)
        if cd:
            return await msg.reply(await cooldown_text("rob", cd))
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo jise rob karna hai 🙄"))
        if target.id == msg.from_user.id:
            return await msg.reply(ff("khud ko rob? 💀"))
        t_data = await get_user(target.id)
        if not t_data or t_data["coins"] < 50:
            return await msg.reply(ff("us garib ke paas kuch nahi 💀"))
        await set_cooldown(msg.from_user.id, "rob_last")
        if await consume_item(target.id, "shield"):
            return await send_mood(app, msg.chat.id, 'sweating',
                f"🛡️ **ᴘʟᴏᴛ ᴛᴡɪꜱᴛ~** {mention(target)} ᴋᴇ ᴘᴀꜱꜱ ꜱʜɪᴇʟᴅ ᴛʜᴀ~\n"
                f"_ʀᴏʙʙᴇʀʏ ʙʟᴏᴄᴋᴇᴅ!_ ✨"
            )
        amount = random.randint(30, min(200, t_data["coins"]))
        if random.random() < 0.5:
            if not await transfer_coins(target.id, msg.from_user.id, amount):
                return await msg.reply(ff("robbery ke time coins change ho gaye~ phir try karo"))
            await send_mood(app, msg.chat.id, 'smug',
                f"💸 **{ff('Robbery!')}**\n"
                f"tu {mention(target)} se `{amount}` {ff('coins')} le gaya 😈"
            )
        else:
            fine = random.randint(20, 80)
            await debit_coins(msg.from_user.id, fine)
            await send_mood(app, msg.chat.id, 'sobbing',
                f"🚓 **{ff('Caught!')}**\n"
                f"{mention(target)} ne pakad liya 💀\n-`{fine}` {ff('coins')} fine!"
            )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("pay"), group=1)
async def cmd_pay(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo + /pay [amount] 🙄"))
        try:
            amount = int(msg.command[-1]); assert amount > 0
        except Exception:
            return await msg.reply(ff("valid amount de 🙄"))
        await ensure_user(target.id, target.username, target.first_name)
        if not await transfer_coins(msg.from_user.id, target.id, amount):
            return await msg.reply(ff("itne coins nahi hain tere paas 💀"))
        await send_mood(app, msg.chat.id, 'love',
            f"✅ `{amount}` {ff('coins')} → {mention(target)} ✨"
        )
    except Exception:
        traceback.print_exc()

# ─── FUN ACTIONS ──────────────────────────────────────────────────
ROASTS = {
    "kiss":  ["kyaa~ itna pyaar 🥺💕", "aww so cute hehe~ 🌸"],
    "slap":  ["ara ara~ 😳 gentle raho~", "ouchie~ 🥺 be nice!"],
    "hug":   ["aww wholesome~ 🤗💕", "Riruru ko bhi hug do~ 🍡"],
    "punch": ["ara~ fighting? 😮 be friends~", "ouchie that hurts~ 🥺"],
    "kick":  ["ehhh~ 😳 so violent~", "kyaa~ play nice! 🌸"],
}

def make_action(cmd, action_name, emoji, verb):
    @app.on_message(filters.command(cmd), group=1)
    async def _h(_, msg: Message):
        try:
            if await _maint_block(msg):
                return
            target = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not target:
                return await msg.reply(ff(f"reply karo kisi ko {cmd} karne ke liye 🙄"))
            gif = await get_anime_gif(action_name)
            caption = (
                f"{emoji} {mention(msg.from_user)} **{ff(verb)}** {mention(target)}\n"
                f"_{random.choice(ROASTS[cmd])}_"
            )
            try:
                if gif:
                    await msg.reply_animation(gif, caption=caption)
                else:
                    await msg.reply(caption)
            except Exception:
                await msg.reply(caption)
        except Exception:
            traceback.print_exc()
    return _h

_kiss  = make_action("kiss",  "kiss",  "💋", "kisses")
_slap  = make_action("slap",  "slap",  "👋", "slaps")
_hug   = make_action("hug",   "hug",   "🤗", "hugs")
_punch = make_action("punch", "punch", "👊", "punches")
_kick  = make_action("kick",  "kick",  "🦵", "kicks")

@app.on_message(filters.command("ship"), group=1)
async def cmd_ship(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo kisi ko ship karne ke liye 💕"))
        score = random.randint(0, 100)
        bar = "❤️" * (score // 10) + "🖤" * (10 - score // 10)
        verdict = (
            ff("soulmates ho bhai 💕")   if score > 85 else
            ff("acha match hai 🌟")       if score > 65 else
            ff("thoda effort lagao 😤")   if score > 40 else
            ff("flop ship hai 💀")
        )
        # Try to generate ship card image
        try:
            from src.images import ship_card
            name1 = msg.from_user.first_name or "User"
            name2 = target.first_name or "User"
            img_buf = await ship_card(name1, name2, score)
            if img_buf:
                await msg.reply_photo(img_buf, caption=(
                    f"💕 **{ff('Ship Score')}**\n"
                    f"{mention(msg.from_user)} + {mention(target)}\n"
                    f"**{score}%** {bar}\n_{verdict}_"
                ))
                return
        except Exception:
            pass
        # Fallback: text only
        await msg.reply(
            f"💕 **{ff('Ship Score')}**\n\n"
            f"{mention(msg.from_user)} + {mention(target)}\n\n"
            f"**{score}%** {bar}\n\n_{verdict}_"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("roll"), group=1)
async def cmd_roll(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        val = random.randint(1, 6)
        faces = ["⚀","⚁","⚂","⚃","⚄","⚅"]
        await msg.reply(
            f"🎲 **{ff('Dice Roll')}**\n\n{faces[val-1]} ᴛᴜ ʀᴏʟʟᴇᴅ **{val}**!"
        )
    except Exception:
        traceback.print_exc()

TRIVIA_Q = [
    ("Capital of Japan?",          "Tokyo",      ["Beijing","Seoul","Tokyo","Bangkok"]),
    ("Sides of a hexagon?",        "6",          ["5","6","7","8"]),
    ("Red Planet?",                "Mars",       ["Venus","Mars","Jupiter","Saturn"]),
    ("7 × 8 = ?",                  "56",         ["48","54","56","63"]),
    ("Who wrote Harry Potter?",    "J.K. Rowling",["Tolkien","J.K. Rowling","Rowling","King"]),
    ("Gas plants absorb?",         "CO2",        ["O2","N2","CO2","H2"]),
    ("Number of continents?",      "7",          ["5","6","7","8"]),
    ("Largest ocean?",             "Pacific",    ["Atlantic","Pacific","Indian","Arctic"]),
]

@app.on_message(filters.command("trivia"), group=1)
async def cmd_trivia(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        q, ans, choices = random.choice(TRIVIA_Q)
        random.shuffle(choices)
        opts = "\n".join(f"  **{i+1}.** {c}" for i,c in enumerate(choices))
        await msg.reply(
            f"❓ **{ff('Trivia Time')}**\n\n**{q}**\n\n{opts}\n\n"
            f"_{ff('reply with the number!')}_"
        )
    except Exception:
        traceback.print_exc()

# ─── ADMIN PANEL ──────────────────────────────────────────────────
@app.on_message(filters.command("admin") & filters.private)
async def cmd_admin(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai bhai 💀"))
        stats = await get_stats()
        await msg.reply(
            f"👑 **{ff('Admin Panel')}**\n\n"
            f"👥 {ff('Users')}: `{stats['users']}`\n"
            f"💬 {ff('Groups')}: `{stats['groups']}`\n"
            f"🚫 {ff('Banned')}: `{stats['banned']}`\n"
            f"⏱️ {ff('Uptime')}: `{uptime_str()}`\n\n"
            f"**{ff('Commands')}:**\n"
            f"• `/broadcast [msg]`\n"
            f"• `/addcredits [uid] [amt]`\n"
            f"• `/addcoins [uid] [amt]`\n"
            f"• `/gban [uid] [reason]`\n"
            f"• `/ungban [uid]`\n"
            f"• `/stats`"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("stats") & filters.private)
async def cmd_stats(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        stats = await get_stats()
        await msg.reply(
            f"📊 **{ff('Stats')}**\n\n"
            f"👥 {ff('Users')}: `{stats['users']}`\n"
            f"💬 {ff('Groups')}: `{stats['groups']}`\n"
            f"🚫 {ff('Banned')}: `{stats['banned']}`\n"
            f"⏱️ {ff('Uptime')}: `{uptime_str()}`"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("broadcast") & filters.private)
async def cmd_broadcast(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return
        text = " ".join(msg.command[1:]) if msg.command else ""
        photo_id = msg.photo.file_id if msg.photo else None
        if not text and not photo_id:
            return await msg.reply(ff("kya broadcast karoon? 🙄"))
        caption = f"📢 **{ff('Broadcast')}**\n\n{text[:3500]}" if text else f"📢 **{ff('Broadcast')}**"
        users = await get_all_users()
        status = await msg.reply(ff(f"broadcasting to {len(users)} users..."))
        ok, fail = 0, 0
        for uid in users:
            try:
                if photo_id:
                    await app.send_photo(uid, photo_id, caption=caption)
                else:
                    await app.send_message(uid, caption)
                ok += 1
                await asyncio.sleep(0.05)
            except Exception:
                fail += 1
        await status.edit(ff(f"done! sent: {ok}, failed: {fail}"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("addcredits") & filters.private)
async def cmd_addcredits(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return
        uid, amt = int(msg.command[1]), int(msg.command[2])
        await ensure_user(uid)
        await update_credits(uid, amt)
        await msg.reply(ff(f"added {amt} credits to {uid} ✅"))
    except Exception:
        await msg.reply(ff("/addcredits [uid] [amount]"))

@app.on_message(filters.command("addcoins") & filters.private)
async def cmd_addcoins(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return
        uid, amt = int(msg.command[1]), int(msg.command[2])
        await ensure_user(uid)
        await update_coins(uid, amt)
        await msg.reply(ff(f"added {amt} coins to {uid} ✅"))
    except Exception:
        await msg.reply(ff("/addcoins [uid] [amount]"))

@app.on_message(filters.command("gban") & filters.private)
async def cmd_gban(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return
        uid    = int(msg.command[1])
        reason = " ".join(msg.command[2:]) or "no reason"
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO banned_users (user_id,reason) VALUES (?,?)", (uid, reason)
            )
            await db.commit()
        await msg.reply(ff(f"globally banned {uid} 🚫"))
    except Exception:
        await msg.reply(ff("/gban [uid] [reason]"))

@app.on_message(filters.command("ungban") & filters.private)
async def cmd_ungban(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not is_owner(msg.from_user.id):
            return
        uid = int(msg.command[1])
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM banned_users WHERE user_id=?", (uid,))
            await db.commit()
        await msg.reply(ff(f"unbanned {uid} ✅"))
    except Exception:
        await msg.reply(ff("/ungban [uid]"))

# ─── GROUP MODERATION ─────────────────────────────────────────────
async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        m = await app.get_chat_member(chat_id, user_id)
        s = getattr(m.status, 'value', str(m.status)) if m.status else ''
        return s in ('administrator', 'creator', 'owner')
    except Exception:
        return False

@app.on_message(filters.new_chat_members)
async def on_new_member(_, msg: Message):
    try:
        chat_id = msg.chat.id
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
            await db.commit()
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM groups WHERE chat_id=?", (chat_id,)) as cur:
                grp = await cur.fetchone()
        if not grp or not grp["welcome_enabled"]:
            return
        for member in msg.new_chat_members:
            if member.is_bot:
                continue
            wtext = grp["welcome_text"]
            wtext = wtext.replace("{first}", member.first_name or "friend")
            wtext = wtext.replace(
                "{username}", f"@{member.username}" if member.username else member.first_name
            )
            wtext = wtext.replace("{first}", member.first_name or "friend")
            wtext = wtext.replace("{chatname}", msg.chat.title or "this group")
            try:
                import urllib.parse
                welcome_prompt = urllib.parse.quote(
                    f"cute pink anime welcome card, text says Welcome {member.first_name or 'friend'}"
                )
                welcome_url = (
                    f"https://image.pollinations.ai/prompt/{welcome_prompt}"
                    "?width=1024&height=512&nologo=true&enhance=true"
                )
                await msg.reply_photo(welcome_url, caption=wtext)
            except Exception:
                await msg.reply(wtext)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("setwelcome") & filters.group)
async def cmd_setwelcome(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        text = " ".join(msg.command[1:]).strip()
        if not text:
            return await msg.reply(ff("welcome text de\nVars: {first} {username} {chatname}"))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO groups (chat_id,welcome_text) VALUES (?,?) "
                "ON CONFLICT(chat_id) DO UPDATE SET welcome_text=excluded.welcome_text",
                (msg.chat.id, text)
            )
            await db.commit()
        await msg.reply(ff("welcome message set ✅"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("welcome") & filters.group)
async def cmd_welcome(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        arg = msg.command[1].lower() if len(msg.command) > 1 else ""
        if arg not in ("on","off"):
            return await msg.reply(ff("/welcome on or /welcome off"))
        enabled = 1 if arg == "on" else 0
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO groups (chat_id,welcome_enabled) VALUES (?,?) "
                "ON CONFLICT(chat_id) DO UPDATE SET welcome_enabled=excluded.welcome_enabled",
                (msg.chat.id, enabled)
            )
            await db.commit()
        await msg.reply(ff(f"welcome turned {arg} ✅"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("delwelcome") & filters.group)
async def cmd_delwelcome(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE groups SET welcome_text=?, welcome_enabled=0 WHERE chat_id=?",
                ("ʜᴇʏ {first}, ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {chatname}! 🎉", msg.chat.id)
            )
            await db.commit()
        await msg.reply(ff("welcome reset ✅"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("save") & filters.group)
async def cmd_save(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        args = msg.command[1:]
        if not args:
            return await msg.reply(ff("/save [keyword] [response]"))
        kw   = args[0].lower()
        resp = " ".join(args[1:]) if len(args) > 1 else (
            msg.reply_to_message.text if msg.reply_to_message else ""
        )
        if not resp:
            return await msg.reply(ff("response bhi de bhai 🙄"))
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO group_filters (chat_id,keyword,response) VALUES (?,?,?)",
                (msg.chat.id, kw, resp)
            )
            await db.commit()
        await msg.reply(ff(f"filter saved: '{kw}' ✅"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("stop") & filters.group)
async def cmd_stop(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        if len(msg.command) < 2:
            return await msg.reply(ff("/stop [keyword]"))
        kw = msg.command[1].lower()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM group_filters WHERE chat_id=? AND keyword=?", (msg.chat.id, kw)
            )
            await db.commit()
        await msg.reply(ff(f"filter removed: '{kw}' ✅"))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("filters") & filters.group)
async def cmd_filters(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT keyword FROM group_filters WHERE chat_id=?", (msg.chat.id,)
            ) as cur:
                rows = await cur.fetchall()
        if not rows:
            return await msg.reply(ff("koi filter nahi set hai 🙄"))
        kws = "\n".join(f"• `{r[0]}`" for r in rows)
        await msg.reply(f"🔍 **{ff('Active Filters')}**\n\n{kws}")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("ban") & filters.group)
async def cmd_ban(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo jise ban karna hai"))
        await app.ban_chat_member(msg.chat.id, target.id)
        await send_mood(app, msg.chat.id, 'furious',
            f"🚫 {mention(target)} **{ff('banned')}** ✅")
    except Exception:
        await msg.reply(ff("ban nahi hua 💀 mujhe admin rights do"))

@app.on_message(filters.command("unban") & filters.group)
async def cmd_unban(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo jise unban karna hai"))
        await app.unban_chat_member(msg.chat.id, target.id)
        await send_mood(app, msg.chat.id, 'peaceful',
            f"✅ {mention(target)} **{ff('unbanned')}**")
    except Exception:
        traceback.print_exc()

# ══════════════════════════════════════════════════════════════════
#  🛡️  ADMIN PANEL  — additive section. Existing admin commands above
#  (/admin /broadcast /addcredits /addcoins /gban /ungban) untouched.
# ══════════════════════════════════════════════════════════════════
def admin_main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 ꜱᴛᴀᴛꜱ", callback_data="adm_stats"),
         InlineKeyboardButton("👤 ᴜꜱᴇʀꜱ", callback_data="adm_users")],
        [InlineKeyboardButton("💰 ᴇᴄᴏɴᴏᴍʏ", callback_data="adm_economy"),
         InlineKeyboardButton("🎮 ɢᴀᴍᴇꜱ", callback_data="adm_games")],
        [InlineKeyboardButton("📢 ʙʀᴏᴀᴅᴄᴀꜱᴛ", callback_data="adm_broadcast"),
         InlineKeyboardButton("💎 ᴩʀᴇᴍɪᴜᴍ", callback_data="adm_premium")],
        [InlineKeyboardButton("🎟️ ᴄᴏᴜᴩᴏɴꜱ", callback_data="adm_coupons"),
         InlineKeyboardButton("📋 ʟᴏɢꜱ", callback_data="adm_logs")],
        [InlineKeyboardButton("🔧 ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", callback_data="adm_maintenance"),
         InlineKeyboardButton("⚙️ ꜱᴇᴛᴛɪɴɢꜱ", callback_data="adm_settings")],
        [InlineKeyboardButton("🔑 ᴀᴩɪ ᴋᴇʏꜱ", callback_data="adm_keys"),
         InlineKeyboardButton("🚫 ʙᴀɴ ʟɪꜱᴛ", callback_data="adm_banlist")],
    ])

def admin_back_kb(target="adm_main"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data=target)]])

def admin_users_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 ꜱᴇᴀʀᴄʜ ᴜꜱᴇʀ", callback_data="adm_user_search"),
         InlineKeyboardButton("📋 ᴀʟʟ ᴜꜱᴇʀꜱ", callback_data="adm_user_list_0")],
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴄᴏɪɴꜱ", callback_data="adm_addcoins"),
         InlineKeyboardButton("➖ ʀᴇᴍᴏᴠᴇ ᴄᴏɪɴꜱ", callback_data="adm_removecoins")],
        [InlineKeyboardButton("💎 ᴀᴅᴅ ɢᴇᴍꜱ", callback_data="adm_addgems"),
         InlineKeyboardButton("🔄 ʀᴇꜱᴇᴛ ꜱᴛᴀᴛꜱ", callback_data="adm_resetstats")],
        [InlineKeyboardButton("🚫 ʙᴀɴ ᴜꜱᴇʀ", callback_data="adm_banuser"),
         InlineKeyboardButton("✅ ᴜɴʙᴀɴ ᴜꜱᴇʀ", callback_data="adm_unbanuser")],
        [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")],
    ])

def admin_economy_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 ꜱᴇᴛ ᴅᴀɪʟʏ", callback_data="adm_set_daily"),
         InlineKeyboardButton("💰 ꜱᴇᴛ ʀᴏʙ ʟɪᴍɪᴛ", callback_data="adm_set_rob")],
        [InlineKeyboardButton("⚔️ ꜱᴇᴛ ᴋɪʟʟ ʀᴇᴡᴀʀᴅ", callback_data="adm_set_kill"),
         InlineKeyboardButton("🏦 ᴛᴏᴩ ʀɪᴄʜ", callback_data="adm_toprich")],
        [InlineKeyboardButton("✅ ᴇᴄᴏɴᴏᴍʏ ᴏɴ", callback_data="adm_eco_on"),
         InlineKeyboardButton("❌ ᴇᴄᴏɴᴏᴍʏ ᴏꜰꜰ", callback_data="adm_eco_off")],
        [InlineKeyboardButton("🔄 ʀᴇꜱᴇᴛ ᴀʟʟ ᴇᴄᴏ", callback_data="adm_reset_eco")],
        [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")],
    ])

def admin_broadcast_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 ᴀʟʟ ᴜꜱᴇʀꜱ", callback_data="adm_bc_users"),
         InlineKeyboardButton("💬 ᴀʟʟ ɢʀᴏᴜᴩꜱ", callback_data="adm_bc_groups")],
        [InlineKeyboardButton("💎 ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ", callback_data="adm_bc_premium"),
         InlineKeyboardButton("🌍 ᴇᴠᴇʀʏᴏɴᴇ", callback_data="adm_bc_all")],
        [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")],
    ])

def admin_games_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ɢᴀᴍᴇꜱ ᴏɴ", callback_data="adm_games_on"),
         InlineKeyboardButton("❌ ɢᴀᴍᴇꜱ ᴏꜰꜰ", callback_data="adm_games_off")],
        [InlineKeyboardButton("📊 ɢᴀᴍᴇ ꜱᴛᴀᴛꜱ", callback_data="adm_game_stats"),
         InlineKeyboardButton("🔄 ᴄᴀɴᴄᴇʟ ᴀʟʟ", callback_data="adm_cancel_games")],
        [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")],
    ])

def admin_maintenance_kb(is_on: bool):
    toggle_text = "✅ ᴛᴜʀɴ ᴏꜰꜰ" if is_on else "❌ ᴛᴜʀɴ ᴏɴ"
    toggle_cb = "adm_maint_off" if is_on else "adm_maint_on"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data=toggle_cb)],
        [InlineKeyboardButton("✏️ ꜱᴇᴛ ᴍᴇꜱꜱᴀɢᴇ", callback_data="adm_maint_msg")],
        [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")],
    ])

def admin_settings_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔢 ʙᴏᴛ ᴠᴇʀꜱɪᴏɴ", callback_data="adm_set_version"),
         InlineKeyboardButton("📊 ꜱʜᴏᴡ ꜱᴇᴛᴛɪɴɢꜱ", callback_data="adm_show_settings")],
        [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")],
    ])

async def _adm_counts():
    """(total_users, premium_count) — never raises."""
    try:
        t = await adb_one("SELECT COUNT(*) FROM users")
        total = t[0] if t else 0
    except Exception:
        total = 0
    try:
        p = await adb_one("SELECT COUNT(*) FROM protection WHERE is_premium=1")
        prem = p[0] if p else 0
    except Exception:
        prem = 0
    return total, prem

async def _adm_main_text():
    total_users, premium_count = await _adm_counts()
    maint = await is_maintenance()
    eco_on = await get_setting("economy_enabled", "1")
    games_on = await get_setting("games_enabled", "1")
    status_eco = "✅" if eco_on == "1" else "❌"
    status_game = "✅" if games_on == "1" else "❌"
    status_maint = "🔴 ᴏɴ" if maint else "🟢 ᴏꜰꜰ"
    return (
        "<blockquote>"
        f"✦ ┌─[ 🛡️ {ff('riruru admin panel')} ]\n"
        "│\n"
        f"├─ 👥 {ff('total users')}: <b>{total_users}</b>\n"
        f"├─ 💎 {ff('premium users')}: <b>{premium_count}</b>\n"
        f"├─ 💰 {ff('economy')}: <b>{status_eco}</b>\n"
        f"├─ 🎮 {ff('games')}: <b>{status_game}</b>\n"
        f"├─ 🔧 {ff('maintenance')}: <b>{status_maint}</b>\n"
        "│\n"
        f"└─ 🌸 {ff('select an option below')}~ 👇\n"
        "</blockquote>"
    )

@app.on_message(filters.command(["adminpanel", "ap"]) & filters.user(ADMINS), group=1)
async def cmd_adminpanel(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await send_mood(app, msg.chat.id, "cool", await _adm_main_text(),
                        reply_markup=admin_main_kb(), reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_callback_query(filters.regex(r"^adm_") & filters.user(ADMINS))
async def admin_callback(_, cb: CallbackQuery):
    data = cb.data
    uid = cb.from_user.id
    try:
        # ── MAIN ──
        if data == "adm_main":
            await _adm_edit(cb, await _adm_main_text(), admin_main_kb())

        # ── STATS ──
        elif data == "adm_stats":
            t = await adb_one("SELECT COUNT(*) FROM users")
            total_users = t[0] if t else 0
            today = datetime.utcnow().date().isoformat()
            nt = await adb_one("SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (f"{today}%",))
            new_today = nt[0] if nt else 0
            tc = await adb_one("SELECT COALESCE(SUM(balance),0) FROM wallet")
            total_coins = tc[0] if tc else 0
            tg = await adb_one("SELECT COALESCE(SUM(gems),0) FROM wallet")
            total_gems = tg[0] if tg else 0
            _, premium_count = await _adm_counts()
            bn = await adb_one("SELECT COUNT(*) FROM user_bans")
            banned_count = bn[0] if bn else 0
            gw = await adb_one("SELECT COALESCE(SUM(wins),0) FROM game_stats")
            gl = await adb_one("SELECT COALESCE(SUM(losses),0) FROM game_stats")
            games_played = (gw[0] if gw else 0) + (gl[0] if gl else 0)
            up = int(time.time() - START_TIME)
            h, rem = divmod(up, 3600)
            m, _s = divmod(rem, 60)
            text = (
                "<blockquote>"
                f"✦ ┌─[ 📊 {ff('bot statistics')} ]\n│\n"
                f"├─ 👥 {ff('total users')}: <b>{total_users}</b>\n"
                f"├─ 🆕 {ff('new today')}: <b>{new_today}</b>\n"
                f"├─ 💎 {ff('premium')}: <b>{premium_count}</b>\n"
                f"├─ 🚫 {ff('banned')}: <b>{banned_count}</b>\n"
                "│\n"
                f"├─ 💰 {ff('total coins')}: <b>{total_coins:,}</b>\n"
                f"├─ 💎 {ff('total gems')}: <b>{total_gems}</b>\n"
                f"├─ 🎮 {ff('games played')}: <b>{games_played}</b>\n"
                "│\n"
                f"└─ ⏱️ {ff('uptime')}: <b>{h}h {m}m</b>\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_back_kb("adm_main"))

        # ── USERS ──
        elif data == "adm_users":
            text = (
                "<blockquote>"
                f"✦ ┌─[ 👤 {ff('user management')} ]\n│\n"
                f"├─ 🔍 /auser [id] — {ff('search user')}\n"
                f"├─ ➕ /addcoins [id] [amt] — {ff('add coins')}\n"
                f"├─ ➖ /rmcoins [id] [amt] — {ff('remove coins')}\n"
                f"├─ 💎 /addgems [id] [amt] — {ff('add gems')}\n"
                f"├─ 🔄 /resetuser [id] — {ff('reset stats')}\n"
                f"├─ 🚫 /botban [id] [reason]\n"
                f"└─ ✅ /botunban [id]\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_users_kb())

        elif data == "adm_user_search":
            try:
                await cb.answer(f"{ff('use')} /auser [id] 🔍", show_alert=True)
            except Exception:
                pass

        elif data.startswith("adm_user_list_"):
            try:
                page = max(0, int(data.rsplit("_", 1)[-1]))
            except Exception:
                page = 0
            rows = await adb_all(
                "SELECT user_id, COALESCE(first_name,'?') FROM users ORDER BY user_id DESC LIMIT 11 OFFSET ?",
                (page * 10,),
            )
            has_next = len(rows) > 10
            rows = rows[:10]
            if not rows and page == 0:
                lines = f"└─ {ff('no users yet')}~\n"
            else:
                lines = "".join(f"├─ <code>{r[0]}</code> — {r[1]}\n" for r in rows)
                lines += f"└─ {ff('page')} {page + 1}\n"
            text = ("<blockquote>" f"✦ ┌─[ 👤 {ff('all users')} ]\n│\n" + lines + "</blockquote>")
            nav = []
            if page > 0:
                nav.append(InlineKeyboardButton("◀️", callback_data=f"adm_user_list_{page - 1}"))
            if has_next:
                nav.append(InlineKeyboardButton("▶️", callback_data=f"adm_user_list_{page + 1}"))
            kb_rows = [nav] if nav else []
            kb_rows.append([InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_users")])
            await _adm_edit(cb, text, InlineKeyboardMarkup(kb_rows))

        elif data in ("adm_addcoins", "adm_removecoins", "adm_addgems",
                      "adm_resetstats", "adm_banuser", "adm_unbanuser"):
            hint = {
                "adm_addcoins": "/addcoins [id] [amt]",
                "adm_removecoins": "/rmcoins [id] [amt]",
                "adm_addgems": "/addgems [id] [amt]",
                "adm_resetstats": "/resetuser [id]",
                "adm_banuser": "/botban [id] [reason]",
                "adm_unbanuser": "/botunban [id]",
            }[data]
            try:
                await cb.answer(f"{ff('use')} {hint}", show_alert=True)
            except Exception:
                pass

        # ── ECONOMY ──
        elif data == "adm_economy":
            daily_n = await get_setting("daily_normal", "2000")
            daily_p = await get_setting("daily_premium", "5000")
            rob_n = await get_setting("rob_max_normal", "10000")
            rob_p = await get_setting("rob_max_premium", "50000")
            eco = await get_setting("economy_enabled", "1")
            text = (
                "<blockquote>"
                f"✦ ┌─[ 💰 {ff('economy control')} ]\n│\n"
                f"├─ 🎁 {ff('daily normal')}: <b>${daily_n}</b>\n"
                f"├─ 🎁 {ff('daily premium')}: <b>${daily_p}</b>\n"
                f"├─ 🔫 {ff('rob max normal')}: <b>${rob_n}</b>\n"
                f"├─ 🔫 {ff('rob max premium')}: <b>${rob_p}</b>\n"
                f"├─ ✅ {ff('economy status')}: <b>{'ON' if eco == '1' else 'OFF'}</b>\n"
                "│\n"
                f"├─ /setdaily [n] [prem] · /setrob [n] [prem]\n"
                f"└─ /setkill [min] [max]\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_economy_kb())

        elif data == "adm_eco_on":
            await set_setting("economy_enabled", "1", uid)
            await log_admin_action(uid, "economy_on")
            try:
                await cb.answer(f"✅ {ff('economy enabled')}!", show_alert=True)
            except Exception:
                pass
            await _adm_edit(cb, (await _adm_economy_text()), admin_economy_kb())

        elif data == "adm_eco_off":
            await set_setting("economy_enabled", "0", uid)
            await log_admin_action(uid, "economy_off")
            try:
                await cb.answer(f"❌ {ff('economy disabled')}!", show_alert=True)
            except Exception:
                pass
            await _adm_edit(cb, (await _adm_economy_text()), admin_economy_kb())

        elif data in ("adm_set_daily", "adm_set_rob", "adm_set_kill"):
            hint = {"adm_set_daily": "/setdaily [normal] [premium]",
                    "adm_set_rob": "/setrob [normal] [premium]",
                    "adm_set_kill": "/setkill [min] [max]"}[data]
            try:
                await cb.answer(f"{ff('use')} {hint}", show_alert=True)
            except Exception:
                pass

        elif data == "adm_toprich":
            rows = await adb_all(
                "SELECT user_id, balance+bank AS tot FROM wallet ORDER BY tot DESC LIMIT 5")
            lines = "".join(f"├─ <code>{r[0]}</code> — <b>{r[1]:,}</b>\n" for r in (rows or []))
            text = ("<blockquote>" f"✦ ┌─[ 🏦 {ff('top rich')} ]\n│\n"
                    + (lines or f"└─ {ff('no data')}~\n") + "</blockquote>")
            await _adm_edit(cb, text, admin_back_kb("adm_economy"))

        elif data == "adm_reset_eco":
            text = (f"<blockquote>⚠️ <b>{ff('reset all economy')}?</b>\n"
                    f"└─ {ff('this zeroes every wallet. tap again to confirm.')}</blockquote>")
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚠️ ʏᴇꜱ, ʀᴇꜱᴇᴛ ᴀʟʟ", callback_data="adm_reset_eco_yes")],
                [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_economy")],
            ])
            await _adm_edit(cb, text, kb)

        elif data == "adm_reset_eco_yes":
            await adb_run("UPDATE wallet SET balance=0, bank=0, gems=0")
            await log_admin_action(uid, "reset_all_eco")
            try:
                await cb.answer(f"🔄 {ff('all wallets reset')}!", show_alert=True)
            except Exception:
                pass
            await _adm_edit(cb, await _adm_main_text(), admin_main_kb())

        # ── GAMES ──
        elif data == "adm_games":
            games_on = await get_setting("games_enabled", "1")
            active = 0
            for _g in ("BOMB_SESSIONS", "BOMB_PENDING", "HEIST_SESSIONS"):
                try:
                    _d = globals().get(_g)
                    if isinstance(_d, dict):
                        active += len(_d)
                except Exception:
                    pass
            text = (
                "<blockquote>"
                f"✦ ┌─[ 🎮 {ff('game control')} ]\n│\n"
                f"├─ ✅ {ff('games status')}: <b>{'ON' if games_on == '1' else 'OFF'}</b>\n"
                f"├─ 🎲 {ff('active games')}: <b>{active}</b>\n"
                "│\n"
                f"└─ 🌸 {ff('use buttons below')}~\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_games_kb())

        elif data == "adm_games_on":
            await set_setting("games_enabled", "1", uid)
            await log_admin_action(uid, "games_on")
            try:
                await cb.answer(f"✅ {ff('games enabled')}!", show_alert=True)
            except Exception:
                pass

        elif data == "adm_games_off":
            await set_setting("games_enabled", "0", uid)
            await log_admin_action(uid, "games_off")
            try:
                await cb.answer(f"❌ {ff('games disabled')}!", show_alert=True)
            except Exception:
                pass

        elif data == "adm_game_stats":
            rows = await adb_all("SELECT game, wins, losses FROM game_stats ORDER BY wins DESC LIMIT 10")
            lines = "".join(f"├─ {r[0]}: <b>{r[1]}W</b> / {r[2]}L\n" for r in (rows or []))
            text = ("<blockquote>" f"✦ ┌─[ 📊 {ff('game stats')} ]\n│\n"
                    + (lines or f"└─ {ff('no data')}~\n") + "</blockquote>")
            await _adm_edit(cb, text, admin_back_kb("adm_games"))

        elif data == "adm_cancel_games":
            for _g in ("BOMB_SESSIONS", "BOMB_PENDING", "HEIST_SESSIONS"):
                try:
                    _d = globals().get(_g)
                    if isinstance(_d, dict):
                        _d.clear()
                except Exception:
                    pass
            await log_admin_action(uid, "cancel_all_games")
            try:
                await cb.answer(f"🔄 {ff('all active games cancelled')}!", show_alert=True)
            except Exception:
                pass

        # ── MAINTENANCE ──
        elif data == "adm_maintenance":
            maint = await is_maintenance()
            maint_msg = await get_setting("maintenance_msg", "🔧 Under maintenance~")
            text = (
                "<blockquote>"
                f"✦ ┌─[ 🔧 {ff('maintenance mode')} ]\n│\n"
                f"├─ ꜱᴛᴀᴛᴜꜱ: <b>{'🔴 ON' if maint else '🟢 OFF'}</b>\n"
                f"├─ ᴍᴇꜱꜱᴀɢᴇ:\n"
                f"│  <i>{maint_msg}</i>\n"
                "│\n"
                f"└─ /setmaintmsg [text]\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_maintenance_kb(maint))

        elif data == "adm_maint_on":
            await set_setting("maintenance", "1", uid)
            await log_admin_action(uid, "maintenance_on")
            try:
                await cb.answer(f"🔴 {ff('maintenance on')}!", show_alert=True)
            except Exception:
                pass

        elif data == "adm_maint_off":
            await set_setting("maintenance", "0", uid)
            await log_admin_action(uid, "maintenance_off")
            try:
                await cb.answer(f"🟢 {ff('maintenance off')}!", show_alert=True)
            except Exception:
                pass

        elif data == "adm_maint_msg":
            try:
                await cb.answer(f"{ff('use')} /setmaintmsg [text]", show_alert=True)
            except Exception:
                pass

        # ── LOGS ──
        elif data == "adm_logs":
            logs = await adb_all(
                "SELECT admin_id, action, details, timestamp FROM admin_logs ORDER BY id DESC LIMIT 10")
            if not logs:
                text = ("<blockquote>" f"✦ ┌─[ 📋 {ff('admin logs')} ]\n│\n"
                        f"└─ {ff('no logs yet')}~\n" "</blockquote>")
            else:
                lines = ""
                for _log in logs:
                    aid, action, details, ts = _log
                    ts_short = ts[:16] if ts else "?"
                    lines += f"├─ <code>{ts_short}</code>\n│  👤 <b>{aid}</b> → {action}\n"
                text = ("<blockquote expandable>" f"✦ ┌─[ 📋 {ff('recent admin logs')} ]\n│\n"
                        + lines + f"└─ {ff('last 10 actions')}\n" + "</blockquote>")
            await _adm_edit(cb, text, admin_back_kb("adm_main"))

        # ── PREMIUM ──
        elif data == "adm_premium":
            _, total_prem = await _adm_counts()
            text = (
                "<blockquote>"
                f"✦ ┌─[ 💎 {ff('premium management')} ]\n│\n"
                f"├─ 💎 {ff('total premium')}: <b>{total_prem}</b>\n"
                "│\n"
                f"├─ ➕ /addprem [id] — {ff('add premium')}\n"
                f"├─ ➖ /rmprem [id] — {ff('remove premium')}\n"
                f"└─ 📋 /listprem — {ff('list all premium')}\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_back_kb("adm_main"))

        # ── COUPONS ──
        elif data == "adm_coupons":
            text = (
                "<blockquote>"
                f"✦ ┌─[ 🎟️ {ff('coupons')} ]\n│\n"
                f"├─ /create_coupon [code] [amt] [max]\n"
                f"├─ /coupon [code]\n"
                f"├─ /status [code]\n"
                f"└─ /del_coupon [code]\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_back_kb("adm_main"))

        # ── BROADCAST ──
        elif data == "adm_broadcast":
            text = (
                "<blockquote>"
                f"✦ ┌─[ 📢 {ff('broadcast')} ]\n│\n"
                f"├─ {ff('select target below')}~\n"
                "│\n"
                f"├─ 👥 {ff('all users')}\n"
                f"├─ 💬 {ff('all groups')}\n"
                f"├─ 💎 {ff('premium only')}\n"
                f"└─ 🌍 {ff('everyone')}\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_broadcast_kb())

        elif data in ("adm_bc_users", "adm_bc_groups", "adm_bc_premium", "adm_bc_all"):
            target = {"adm_bc_users": "users", "adm_bc_groups": "groups",
                      "adm_bc_premium": "premium", "adm_bc_all": "all"}[data]
            PENDING_BROADCASTS[uid] = target
            try:
                await cb.answer(f"{ff('now send the message to broadcast')} ({target})!", show_alert=True)
            except Exception:
                pass

        # ── API KEYS ──
        elif data == "adm_keys":
            rows = await adb_all(
                "SELECT id, key_value, label, is_active, last_status, added_at"
                " FROM api_keys WHERE service='groq' ORDER BY id")
            rows = rows or []
            if not rows:
                lines = f"└─ {ff('no keys yet')} — {ff('use')} /addkey\n"
            else:
                lines = ""
                for r in rows:
                    kid, kval, klabel, kactive, kstatus, kats = r
                    st = "🟢" if kactive else "⚪"
                    ats = (kats or "?")[:10]
                    lines += (f"├─ {st} <b>#{kid}</b> <code>{mask_key(kval)}</code>\n"
                              f"│  🏷️ {klabel or '-'} · {kstatus or 'untested'} · {ats}\n")
            text = ("<blockquote expandable>"
                    f"✦ ┌─[ 🔑 {ff('groq api keys')} ({len(rows)}) ]\n│\n"
                    + lines +
                    f"│\n├─ ➕ /addkey [label] [key]\n"
                    f"├─ 🗑️ /rmkey [id]\n"
                    f"└─ 🧪 /testkeys\n"
                    "</blockquote>")
            kb_rows = []
            for r in rows[:8]:
                kid, _kv, _kl, kactive, _ks, _ka = r
                toggle = "⏸️" if kactive else "▶️"
                kb_rows.append([
                    InlineKeyboardButton(f"🧪 #{kid}", callback_data=f"adm_key_test_{kid}"),
                    InlineKeyboardButton(f"{toggle} #{kid}", callback_data=f"adm_key_toggle_{kid}"),
                    InlineKeyboardButton(f"🗑️ #{kid}", callback_data=f"adm_key_del_{kid}"),
                ])
            kb_rows.append([InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_main")])
            await _adm_edit(cb, text, InlineKeyboardMarkup(kb_rows))

        elif data.startswith("adm_key_test_"):
            try:
                kid = int(data.rsplit("_", 1)[-1])
            except Exception:
                kid = 0
            row = await adb_one("SELECT key_value FROM api_keys WHERE id=?", (kid,))
            if not row:
                try:
                    await cb.answer("Key not found", show_alert=True)
                except Exception:
                    pass
            else:
                try:
                    await cb.answer("🧪 Testing key…", show_alert=False)
                except Exception:
                    pass
                ok, detail = await test_groq_key(row[0])
                await adb_run("UPDATE api_keys SET last_status=? WHERE id=?",
                              (detail, kid))
                await log_admin_action(uid, "test_key", kid, detail)
                try:
                    await cb.answer(detail, show_alert=True)
                except Exception:
                    pass
                # refresh the list view
                cb.data = "adm_keys"
                await admin_callback(_, cb)
                return

        elif data.startswith("adm_key_toggle_"):
            try:
                kid = int(data.rsplit("_", 1)[-1])
            except Exception:
                kid = 0
            row = await adb_one("SELECT is_active FROM api_keys WHERE id=?", (kid,))
            if row is not None:
                new_state = 0 if row[0] else 1
                await adb_run("UPDATE api_keys SET is_active=? WHERE id=?", (new_state, kid))
                n = await rebuild_groq_pool()
                await log_admin_action(uid, "toggle_key", kid, f"active={new_state} pool={n}")
                try:
                    await cb.answer(f"{'▶️ Activated' if new_state else '⏸️ Paused'} — pool: {n} keys",
                                    show_alert=True)
                except Exception:
                    pass
            cb.data = "adm_keys"
            await admin_callback(_, cb)
            return

        elif data.startswith("adm_key_del_yes_"):
            try:
                kid = int(data.rsplit("_", 1)[-1])
            except Exception:
                kid = 0
            await adb_run("DELETE FROM api_keys WHERE id=?", (kid,))
            n = await rebuild_groq_pool()
            await log_admin_action(uid, "del_key", kid, f"pool={n}")
            try:
                await cb.answer(f"🗑️ Key #{kid} deleted — pool: {n}", show_alert=True)
            except Exception:
                pass
            cb.data = "adm_keys"
            await admin_callback(_, cb)
            return

        elif data.startswith("adm_key_del_"):
            try:
                kid = int(data.rsplit("_", 1)[-1])
            except Exception:
                kid = 0
            text = (f"<blockquote>⚠️ <b>{ff('delete key')} #{kid}?</b>\n"
                    f"└─ {ff('tap again to confirm.')}</blockquote>")
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"⚠️ {ff('yes, delete')}", callback_data=f"adm_key_del_yes_{kid}")],
                [InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="adm_keys")],
            ])
            await _adm_edit(cb, text, kb)

        # ── BAN LIST ──
        elif data == "adm_banlist":
            bans = await adb_all(
                "SELECT user_id, reason, banned_at FROM user_bans ORDER BY banned_at DESC LIMIT 10")
            if not bans:
                lines = f"└─ {ff('no banned users')}~\n"
            else:
                lines = ""
                for _b in bans:
                    uid_b, reason, ts = _b
                    ts_s = ts[:10] if ts else "?"
                    lines += (f"├─ 🚫 <code>{uid_b}</code>\n"
                              f"│  📝 {reason or 'no reason'}\n"
                              f"│  📅 {ts_s}\n")
            text = ("<blockquote expandable>" f"✦ ┌─[ 🚫 {ff('ban list')} ]\n│\n"
                    + lines + "</blockquote>")
            await _adm_edit(cb, text, admin_back_kb("adm_main"))

        # ── SETTINGS ──
        elif data == "adm_settings":
            ver = await get_setting("bot_version", "2.0")
            text = (
                "<blockquote>"
                f"✦ ┌─[ ⚙️ {ff('bot settings')} ]\n│\n"
                f"├─ 🔢 {ff('version')}: <b>v{ver}</b>\n"
                "│\n"
                f"├─ /setver [ver] — {ff('set version')}\n"
                f"└─ /showsettings — {ff('all settings')}\n"
                "</blockquote>"
            )
            await _adm_edit(cb, text, admin_settings_kb())

        elif data == "adm_set_version":
            try:
                await cb.answer(f"{ff('use')} /setver [version]", show_alert=True)
            except Exception:
                pass

        elif data == "adm_show_settings":
            rows = await adb_all("SELECT key, value FROM bot_settings ORDER BY key")
            lines = "".join(f"├─ <code>{r[0]}</code> = <b>{r[1]}</b>\n" for r in (rows or []))
            text = ("<blockquote expandable>" f"✦ ┌─[ ⚙️ {ff('all settings')} ]\n│\n"
                    + (lines or f"└─ {ff('no data')}~\n") + "</blockquote>")
            await _adm_edit(cb, text, admin_back_kb("adm_settings"))
    except Exception:
        traceback.print_exc()
    try:
        await cb.answer()
    except Exception:
        pass

async def _adm_economy_text():
    daily_n = await get_setting("daily_normal", "2000")
    daily_p = await get_setting("daily_premium", "5000")
    rob_n = await get_setting("rob_max_normal", "10000")
    rob_p = await get_setting("rob_max_premium", "50000")
    eco = await get_setting("economy_enabled", "1")
    return (
        "<blockquote>"
        f"✦ ┌─[ 💰 {ff('economy control')} ]\n│\n"
        f"├─ 🎁 {ff('daily normal')}: <b>${daily_n}</b>\n"
        f"├─ 🎁 {ff('daily premium')}: <b>${daily_p}</b>\n"
        f"├─ 🔫 {ff('rob max normal')}: <b>${rob_n}</b>\n"
        f"├─ 🔫 {ff('rob max premium')}: <b>${rob_p}</b>\n"
        f"├─ ✅ {ff('economy status')}: <b>{'ON' if eco == '1' else 'OFF'}</b>\n"
        "</blockquote>"
    )

# ─── ADMIN SLASH COMMANDS (additive — old /admin /broadcast /addcredits /addcoins(private) /gban kept) ──
def _adm_target(msg):
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user.id
    return None

@app.on_message(filters.command("auser") & filters.user(ADMINS), group=1)
async def cmd_auser(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target_id = _adm_target(msg)
        if not target_id and len(msg.command) > 1:
            try:
                target_id = int(msg.command[1])
            except Exception:
                pass
        if not target_id:
            return await msg.reply(f"{ff('usage')}: /auser [id] {ff('or reply')}")
        user = await adb_one("SELECT user_id, username, first_name FROM users WHERE user_id=?", (target_id,))
        if not user:
            return await msg.reply(f"❌ {ff('user not found in db')}")
        w = await adb_one("SELECT balance, bank, gems FROM wallet WHERE user_id=?", (target_id,)) or (0, 0, 0)
        x = await adb_one("SELECT xp, level, total_kills FROM user_xp WHERE user_id=?", (target_id,)) or (0, 1, 0)
        prem = await is_premium_admin_view(target_id)
        banned = await is_bot_banned(target_id)
        text = (
            "<blockquote>"
            f"✦ ┌─[ 👤 {ff('user info')} ]\n│\n"
            f"├─ 🆔 {ff('id')}: <code>{target_id}</code>\n"
            f"├─ 💰 {ff('wallet')}: <b>${(w[0] or 0):,}</b>\n"
            f"├─ 🏦 {ff('bank')}: <b>${(w[1] or 0):,}</b>\n"
            f"├─ 💎 {ff('gems')}: <b>{w[2] or 0}</b>\n"
            f"├─ ⭐ {ff('xp')}: <b>{x[0] or 0}</b>\n"
            f"├─ 📊 {ff('level')}: <b>{x[1] or 1}</b>\n"
            f"├─ ⚔️ {ff('kills')}: <b>{x[2] or 0}</b>\n"
            f"├─ 💎 {ff('premium')}: <b>{'✅' if prem else '❌'}</b>\n"
            f"├─ 🚫 {ff('bot banned')}: <b>{'✅' if banned else '❌'}</b>\n"
            f"└─ 🌸 {ff('admin view')}\n"
            "</blockquote>"
        )
        await send_mood(app, msg.chat.id, "curious", text, reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("addcoins") & filters.group & filters.user(ADMINS), group=1)
async def cmd_admin_addcoins(_, msg: Message):
    """Group-scoped admin coin grant. Old private /addcoins (owner) untouched."""
    try:
        parts = msg.command
        t = _adm_target(msg)
        if t is not None:
            target_id, amount = t, int(parts[1])
        else:
            target_id, amount = int(parts[1]), int(parts[2])
        await adb_run("INSERT INTO wallet (user_id, balance) VALUES (?, ?) "
                      "ON CONFLICT(user_id) DO UPDATE SET balance=balance+?",
                      (target_id, amount, amount))
        bal = await adb_one("SELECT balance FROM wallet WHERE user_id=?", (target_id,))
        await log_admin_action(msg.from_user.id, "addcoins", target_id, f"+{amount}")
        await log_transaction(target_id, "admin_add", amount, (bal[0] if bal else 0),
                              f"Admin {msg.from_user.id} added")
        await send_mood(app, msg.chat.id, "greedy",
                        f"<blockquote>✅ {ff('added')} <b>${amount:,}</b> {ff('to')} <code>{target_id}</code></blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {ff('error')}: {e}\n{ff('usage')}: /addcoins [id] [amt]")

@app.on_message(filters.command("rmcoins") & filters.user(ADMINS), group=1)
async def cmd_rmcoins(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        parts = msg.command
        t = _adm_target(msg)
        if t is not None:
            target_id, amount = t, int(parts[1])
        else:
            target_id, amount = int(parts[1]), int(parts[2])
        await adb_run("INSERT INTO wallet (user_id, balance) VALUES (?, 0) "
                      "ON CONFLICT(user_id) DO UPDATE SET balance=MAX(0, balance-?)",
                      (target_id, amount))
        bal = await adb_one("SELECT balance FROM wallet WHERE user_id=?", (target_id,))
        await log_admin_action(msg.from_user.id, "rmcoins", target_id, f"-{amount}")
        await log_transaction(target_id, "admin_remove", -amount, (bal[0] if bal else 0),
                              f"Admin {msg.from_user.id} removed")
        await send_mood(app, msg.chat.id, "annoyed",
                        f"<blockquote>➖ {ff('removed')} <b>${amount:,}</b> {ff('from')} <code>{target_id}</code></blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {ff('error')}: {e}\n{ff('usage')}: /rmcoins [id] [amt]")

@app.on_message(filters.command("addgems") & filters.user(ADMINS), group=1)
async def cmd_addgems(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        parts = msg.command
        t = _adm_target(msg)
        if t is not None:
            target_id, amount = t, int(parts[1])
        else:
            target_id, amount = int(parts[1]), int(parts[2])
        await adb_run("INSERT INTO wallet (user_id, gems) VALUES (?, ?) "
                      "ON CONFLICT(user_id) DO UPDATE SET gems=gems+?",
                      (target_id, amount, amount))
        await log_admin_action(msg.from_user.id, "addgems", target_id, f"+{amount}")
        await log_transaction(target_id, "admin_add_gems", amount, 0,
                              f"Admin {msg.from_user.id} added gems")
        await send_mood(app, msg.chat.id, "greedy",
                        f"<blockquote>💎 {ff('added')} <b>{amount}</b> {ff('gems to')} <code>{target_id}</code></blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {ff('error')}: {e}\n{ff('usage')}: /addgems [id] [amt]")

@app.on_message(filters.command("addprem") & filters.user(ADMINS), group=1)
async def cmd_addprem(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target_id = _adm_target(msg)
        if target_id is None:
            target_id = int(msg.command[1])
        await adb_run("INSERT INTO protection (user_id, is_premium) VALUES (?, 1) "
                      "ON CONFLICT(user_id) DO UPDATE SET is_premium=1", (target_id,))
        await log_admin_action(msg.from_user.id, "add_premium", target_id)
        await send_mood(app, msg.chat.id, "excited",
                        f"<blockquote>💎 {ff('premium added to')} <code>{target_id}</code>!</blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {e}\n{ff('usage')}: /addprem [id]")

@app.on_message(filters.command("rmprem") & filters.user(ADMINS), group=1)
async def cmd_rmprem(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target_id = _adm_target(msg)
        if target_id is None:
            target_id = int(msg.command[1])
        await adb_run("UPDATE protection SET is_premium=0 WHERE user_id=?", (target_id,))
        await log_admin_action(msg.from_user.id, "remove_premium", target_id)
        await send_mood(app, msg.chat.id, "annoyed",
                        f"<blockquote>💎 {ff('premium removed from')} <code>{target_id}</code></blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {e}\n{ff('usage')}: /rmprem [id]")

@app.on_message(filters.command("listprem") & filters.user(ADMINS), group=1)
async def cmd_listprem(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        rows = await adb_all("SELECT user_id FROM protection WHERE is_premium=1 LIMIT 20")
        if not rows:
            return await msg.reply(ff("no premium users found."))
        lines = ""
        for i, r in enumerate(rows, 1):
            nm = await adb_one("SELECT first_name FROM users WHERE user_id=?", (r[0],))
            lines += f"├─ {i}. <code>{r[0]}</code> — {(nm[0] if nm and nm[0] else '?')}\n"
        await send_mood(app, msg.chat.id, "excited",
                        "<blockquote>" f"✦ ┌─[ 💎 {ff('premium users')} ]\n│\n" + lines +
                        f"└─ {ff('total')}: {len(rows)}\n" "</blockquote>", reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("botban") & filters.user(ADMINS), group=1)
async def cmd_botban(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        t = _adm_target(msg)
        if t is not None:
            target_id = t
            reason = " ".join(msg.command[1:]) or "No reason"
        else:
            target_id = int(msg.command[1])
            reason = " ".join(msg.command[2:]) or "No reason"
        if target_id in ADMINS:
            return await msg.reply(f"❌ {ff('cannot ban an admin')}!")
        await adb_run("INSERT OR REPLACE INTO user_bans (user_id, reason, banned_by, banned_at)"
                      " VALUES (?, ?, ?, ?)",
                      (target_id, reason, msg.from_user.id, datetime.utcnow().isoformat()))
        await log_admin_action(msg.from_user.id, "botban", target_id, reason)
        await send_mood(app, msg.chat.id, "furious",
                        f"<blockquote>🚫 <code>{target_id}</code> {ff('banned from bot')}!\n📝 {reason}</blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {e}\n{ff('usage')}: /botban [id] [reason]")

@app.on_message(filters.command("botunban") & filters.user(ADMINS), group=1)
async def cmd_botunban(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target_id = _adm_target(msg)
        if target_id is None:
            target_id = int(msg.command[1])
        await adb_run("DELETE FROM user_bans WHERE user_id=?", (target_id,))
        await log_admin_action(msg.from_user.id, "botunban", target_id)
        await send_mood(app, msg.chat.id, "peaceful",
                        f"<blockquote>✅ <code>{target_id}</code> {ff('unbanned')}!</blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {e}\n{ff('usage')}: /botunban [id]")

@app.on_message(filters.command("resetuser") & filters.user(ADMINS), group=1)
async def cmd_resetuser(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        target_id = _adm_target(msg)
        if target_id is None:
            target_id = int(msg.command[1])
        await adb_run("INSERT INTO wallet (user_id, balance, bank, gems) VALUES (?, 0, 0, 0) "
                      "ON CONFLICT(user_id) DO UPDATE SET balance=0, bank=0, gems=0", (target_id,))
        await adb_run("INSERT INTO user_xp (user_id, xp, level, total_kills, total_robs) "
                      "VALUES (?, 0, 1, 0, 0) ON CONFLICT(user_id) DO UPDATE SET "
                      "xp=0, level=1, total_kills=0, total_robs=0", (target_id,))
        await log_admin_action(msg.from_user.id, "reset_user", target_id)
        await send_mood(app, msg.chat.id, "dead",
                        f"<blockquote>🔄 <code>{target_id}</code> {ff('stats reset')}!</blockquote>",
                        reply_to_id=msg.id)
    except Exception as e:
        await msg.reply(f"❌ {e}\n{ff('usage')}: /resetuser [id]")

@app.on_message(filters.command("setdaily") & filters.user(ADMINS), group=1)
async def cmd_setdaily(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        normal = msg.command[1]
        premium = msg.command[2] if len(msg.command) > 2 else None
        await set_setting("daily_normal", normal, msg.from_user.id)
        if premium is not None:
            await set_setting("daily_premium", premium, msg.from_user.id)
        await log_admin_action(msg.from_user.id, "set_daily", 0, f"{normal}/{premium}")
        await msg.reply(f"✅ {ff('daily set')}: {ff('normal')}=<b>{normal}</b>"
                        + (f", {ff('premium')}=<b>{premium}</b>" if premium else ""),
                        parse_mode=enums.ParseMode.HTML)
    except Exception:
        await msg.reply(f"{ff('usage')}: /setdaily [normal] [premium]")

@app.on_message(filters.command("setrob") & filters.user(ADMINS), group=1)
async def cmd_setrob(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        normal = msg.command[1]
        premium = msg.command[2] if len(msg.command) > 2 else None
        await set_setting("rob_max_normal", normal, msg.from_user.id)
        if premium is not None:
            await set_setting("rob_max_premium", premium, msg.from_user.id)
        await log_admin_action(msg.from_user.id, "set_rob", 0, f"{normal}/{premium}")
        await msg.reply(f"✅ {ff('rob max set')}: {ff('normal')}=<b>{normal}</b>"
                        + (f", {ff('premium')}=<b>{premium}</b>" if premium else ""),
                        parse_mode=enums.ParseMode.HTML)
    except Exception:
        await msg.reply(f"{ff('usage')}: /setrob [normal] [premium]")

@app.on_message(filters.command("setkill") & filters.user(ADMINS), group=1)
async def cmd_setkill(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await set_setting("kill_min_normal", msg.command[1], msg.from_user.id)
        await set_setting("kill_max_normal", msg.command[2], msg.from_user.id)
        if len(msg.command) > 4:
            await set_setting("kill_min_premium", msg.command[3], msg.from_user.id)
            await set_setting("kill_max_premium", msg.command[4], msg.from_user.id)
        await log_admin_action(msg.from_user.id, "set_kill", 0, " ".join(msg.command[1:]))
        await msg.reply(f"✅ {ff('kill rewards updated')}.", parse_mode=enums.ParseMode.HTML)
    except Exception:
        await msg.reply(f"{ff('usage')}: /setkill [min] [max] ([prem_min] [prem_max])")

@app.on_message(filters.command("setver") & filters.user(ADMINS), group=1)
async def cmd_setver(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await set_setting("bot_version", msg.command[1], msg.from_user.id)
        await log_admin_action(msg.from_user.id, "set_version", 0, msg.command[1])
        await msg.reply(f"✅ {ff('version set to')} <b>v{msg.command[1]}</b>", parse_mode=enums.ParseMode.HTML)
    except Exception:
        await msg.reply(f"{ff('usage')}: /setver [version]")

@app.on_message(filters.command("setmaintmsg") & filters.user(ADMINS), group=1)
async def cmd_setmaintmsg(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        txt = msg.text.split(None, 1)[1]
        await set_setting("maintenance_msg", txt, msg.from_user.id)
        await log_admin_action(msg.from_user.id, "set_maint_msg", 0, txt[:100])
        await msg.reply(f"✅ {ff('maintenance message updated')}.", parse_mode=enums.ParseMode.HTML)
    except Exception:
        await msg.reply(f"{ff('usage')}: /setmaintmsg [text]")

@app.on_message(filters.command("showsettings") & filters.user(ADMINS), group=1)
async def cmd_showsettings(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        rows = await adb_all("SELECT key, value FROM bot_settings ORDER BY key")
        lines = "".join(f"├─ <code>{r[0]}</code> = <b>{r[1]}</b>\n" for r in (rows or []))
        await send_mood(app, msg.chat.id, "curious",
                        "<blockquote>" f"✦ ┌─[ ⚙️ {ff('all settings')} ]\n│\n"
                        + (lines or f"└─ {ff('no data')}~\n") + "</blockquote>",
                        reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command(["keys", "keylist"]) & filters.user(ADMINS), group=1)
async def cmd_keylist(_, msg: Message):
    try:
        rows = await adb_all(
            "SELECT id, key_value, label, is_active, last_status FROM api_keys"
            " WHERE service='groq' ORDER BY id")
        rows = rows or []
        n_active = sum(1 for r in rows if r[3])
        lines = ""
        for r in rows:
            kid, kval, klabel, kactive, kstatus = r
            st = "🟢" if kactive else "⚪"
            lines += f"├─ {st} <b>#{kid}</b> <code>{mask_key(kval)}</code> — {klabel or '-'} ({kstatus or 'untested'})\n"
        await send_mood(app, msg.chat.id, "curious",
                        "<blockquote expandable>"
                        f"✦ ┌─[ 🔑 {ff('groq keys')}: {n_active}/{len(rows)} {ff('active')} ]\n│\n"
                        + (lines or f"└─ {ff('no keys yet')}~\n") + "</blockquote>",
                        reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("addkey") & filters.user(ADMINS), group=1)
async def cmd_addkey(_, msg: Message):
    try:
        parts = msg.command[1:]
        if not parts:
            return await msg.reply(f"{ff('usage')}: /addkey [label] [key]")
        if len(parts) == 1:
            label, key = f"key-{datetime.utcnow().strftime('%m%d-%H%M')}", parts[0]
        else:
            label, key = parts[0][:30], parts[-1]
        key = key.strip()
        if not key.startswith("gsk_") or len(key) < 12:
            return await msg.reply(f"❌ {ff('that does not look like a groq key (gsk_…)')}")
        ex = await adb_one("SELECT id FROM api_keys WHERE key_value=?", (key,))
        if ex:
            return await msg.reply(f"⚠️ {ff('key already exists as')} #{ex[0]}")
        ok_ins = await adb_run(
            "INSERT INTO api_keys (service, key_value, label, added_by, added_at, is_active)"
            " VALUES ('groq', ?, ?, ?, ?, 1)",
            (key, label, msg.from_user.id, datetime.utcnow().isoformat()))
        if not ok_ins:
            return await msg.reply(f"❌ {ff('db error, try again')}")
        n = await rebuild_groq_pool()
        await log_admin_action(msg.from_user.id, "add_key", 0, f"{label} pool={n}")
        try:
            await msg.delete()
        except Exception:
            pass
        await send_mood(app, msg.chat.id, "excited",
                        f"<blockquote>🔑 {ff('key added')}: <b>{label}</b> <code>{mask_key(key)}</code>\n"
                        f"└─ {ff('pool')}: <b>{n}</b> {ff('active keys')} ✅</blockquote>",
                        reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("rmkey") & filters.user(ADMINS), group=1)
async def cmd_rmkey(_, msg: Message):
    try:
        if len(msg.command) < 2:
            return await msg.reply(f"{ff('usage')}: /rmkey [id] — {ff('see ids in')} /keys")
        kid = int(msg.command[1])
        row = await adb_one("SELECT label FROM api_keys WHERE id=?", (kid,))
        if not row:
            return await msg.reply(f"❌ {ff('no key with id')} #{kid}")
        left = await adb_one("SELECT COUNT(*) FROM api_keys WHERE service='groq' AND is_active=1")
        if left and left[0] <= 1:
            # deleting the last active key would kill AI — confirm explicitly
            if len(msg.command) < 3 or msg.command[2].lower() != "force":
                return await msg.reply(
                    f"⚠️ #{kid} {ff('is the last active key!')} {ff('repeat with')} "
                    f"<code>/rmkey {kid} force</code> {ff('to confirm')}.",
                    parse_mode=enums.ParseMode.HTML)
        await adb_run("DELETE FROM api_keys WHERE id=?", (kid,))
        n = await rebuild_groq_pool()
        await log_admin_action(msg.from_user.id, "del_key", kid, f"pool={n}")
        await send_mood(app, msg.chat.id, "annoyed",
                        f"<blockquote>🗑️ {ff('key')} #{kid} ({row[0]}) {ff('deleted')} — "
                        f"{ff('pool')}: <b>{n}</b></blockquote>", reply_to_id=msg.id)
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("testkeys") & filters.user(ADMINS), group=1)
async def cmd_testkeys(_, msg: Message):
    try:
        rows = await adb_all("SELECT id, key_value, label FROM api_keys WHERE service='groq' ORDER BY id")
        rows = rows or []
        if not rows:
            return await msg.reply(ff("no keys to test."))
        status = await msg.reply(f"🧪 {ff('testing')} {len(rows)} {ff('keys')}…")
        results = []
        for kid, kval, klabel in rows:
            ok, detail = await test_groq_key(kval)
            await adb_run("UPDATE api_keys SET last_status=? WHERE id=?", (detail, kid))
            results.append(f"{'✅' if ok else '❌'} #{kid} ({klabel}): {detail}")
        await log_admin_action(msg.from_user.id, "test_all_keys", 0,
                               f"{sum('✅' in r for r in results)}/{len(results)} ok")
        try:
            await status.edit(f"<blockquote>🧪 <b>{ff('key test results')}</b>\n│\n" +
                              "".join(f"├─ {r}\n" for r in results) + "</blockquote>",
                              parse_mode=enums.ParseMode.HTML)
        except Exception:
            await msg.reply("\n".join(results))
    except Exception:
        traceback.print_exc()

async def do_broadcast(client, msg, target):
    """Panel-driven broadcast. Records history, never raises."""
    sent = fail = 0
    media_type = media_id = None
    btext = msg.text or msg.caption or ""
    try:
        await msg.reply(f"📢 {ff('starting broadcast to')}: <b>{target}</b>...",
                        parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass
    try:
        targets = []
        if target in ("users", "all", "premium"):
            if target == "premium":
                rows = await adb_all("SELECT user_id FROM protection WHERE is_premium=1")
            else:
                rows = await adb_all("SELECT user_id FROM users")
            targets += [r[0] for r in (rows or [])]
        if target in ("groups", "all"):
            grows = await adb_all("SELECT chat_id FROM groups")
            if not grows:
                grows = await adb_all("SELECT chat_id FROM group_economy")
            targets += [r[0] for r in (grows or [])]
        for tid in targets:
            try:
                if msg.photo:
                    media_type, media_id = "photo", msg.photo.file_id
                    await client.send_photo(tid, photo=msg.photo.file_id,
                                            caption=msg.caption or "",
                                            parse_mode=enums.ParseMode.HTML)
                elif msg.video:
                    media_type, media_id = "video", msg.video.file_id
                    await client.send_video(tid, video=msg.video.file_id,
                                            caption=msg.caption or "",
                                            parse_mode=enums.ParseMode.HTML)
                elif getattr(msg, "document", None):
                    media_type, media_id = "document", msg.document.file_id
                    await client.send_document(tid, document=msg.document.file_id,
                                               caption=msg.caption or "",
                                               parse_mode=enums.ParseMode.HTML)
                elif btext:
                    await client.send_message(tid, btext, parse_mode=enums.ParseMode.HTML)
                else:
                    fail += 1
                    continue
                sent += 1
                await asyncio.sleep(0.05)
            except Exception:
                fail += 1
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO broadcast_history (admin_id, message, media_type, media_file_id,"
                    " target, sent_count, fail_count, sent_at, status)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'done')",
                    (msg.from_user.id if msg.from_user else 0, btext[:1000],
                     media_type, media_id, target, sent, fail,
                     datetime.utcnow().isoformat()),
                )
                await db.commit()
        except Exception:
            pass
        await log_admin_action(msg.from_user.id if msg.from_user else 0,
                               "broadcast", 0, f"target={target} sent={sent} fail={fail}")
    except Exception:
        traceback.print_exc()
    try:
        await msg.reply(f"<blockquote>📢 {ff('broadcast done')}!\n✅ {ff('sent')}: {sent}\n❌ {ff('failed')}: {fail}</blockquote>",
                        parse_mode=enums.ParseMode.HTML)
    except Exception:
        pass

# ─── ANTI-ABUSE + FILTERS (group messages) ────────────────────────
GAALI = [
    "fuck","shit","bitch","bastard","asshole","chutiya","madarchod",
    "bhenchod","gaandu","randi","haramzada","kamina","saala","kutte",
    "harami","madar",
]
SPAM_TRACKER = defaultdict(deque)

def is_reply_to_bot(msg: Message) -> bool:
    reply = getattr(msg, "reply_to_message", None)
    replied_user = getattr(reply, "from_user", None) if reply else None
    return bool(
        replied_user
        and (
            (BOT_ID and replied_user.id == BOT_ID)
            or (BOT_USERNAME and (replied_user.username or "").lower() == BOT_USERNAME.lower())
        )
    )

# Names/variations that trigger Riruru in groups
RIRURU_NAMES = [
    "riruru", "ririru", "riru", "riri",
    "riruuu", "ririruuu", "riruru!", "riruru?",
]

def should_ai_reply(msg: Message) -> bool:
    """Check if Riruru should reply in group: reply-to-bot, @tag, or name mention."""
    try:
        # CASE 1: Reply to bot's own message
        try:
            if is_reply_to_bot(msg):
                return True
        except Exception:
            pass
        try:
            if (msg.reply_to_message and msg.reply_to_message.from_user
                    and getattr(msg.reply_to_message.from_user, "is_self", False)):
                return True
        except Exception:
            pass
        # CASE 2: Bot tagged via @username
        try:
            if msg.text and BOT_USERNAME:
                if f"@{BOT_USERNAME.lower()}" in msg.text.lower():
                    return True
        except Exception:
            pass
        # CASE 3: Name mentioned in text
        try:
            if msg.text:
                text_lower = msg.text.lower().strip()
                for name in RIRURU_NAMES:
                    if name in text_lower:
                        return True
        except Exception:
            pass
        # CASE 4: Caption mention (photo/video msgs)
        try:
            cap = getattr(msg, "caption", None)
            if cap:
                cap_lower = cap.lower().strip()
                for name in RIRURU_NAMES:
                    if name in cap_lower:
                        return True
        except Exception:
            pass
        return False
    except Exception:
        return False

async def group_ai_response(msg: Message, prompt: str):
    chat_id = msg.chat.id
    if chat_id in GROUP_AI_BUSY:
        return
    GROUP_AI_BUSY.add(chat_id)
    try:
        await msg.reply_chat_action(enums.ChatAction.TYPING)
        reply = await riruru_reply(
            prompt, await get_history(msg.from_user.id), await user_mood(msg.from_user.id),
            user_id=msg.from_user.id,
        )
        if not reply:
            return
        await save_message(msg.from_user.id, "user", prompt)
        await save_message(msg.from_user.id, "assistant", reply)
        # AI replies are TEXT ONLY — no face photos (user request)
        await app.send_message(chat_id, reply)
    except Exception as exc:
        print(f"  Group AI error: {type(exc).__name__}: {str(exc)[:180]}")
    finally:
        GROUP_AI_BUSY.discard(chat_id)

@app.on_message(filters.group & filters.text, group=10)
async def group_msg(_, msg: Message):
    try:
        if not msg.from_user:
            return
        # Admin panel broadcast capture (pending target chosen from panel)
        if msg.from_user.id in ADMINS and msg.from_user.id in PENDING_BROADCASTS:
            if not (msg.text and msg.text.startswith("/")):
                _tgt = PENDING_BROADCASTS.pop(msg.from_user.id)
                await do_broadcast(app, msg, _tgt)
                return
        if msg.text and msg.text.startswith("/"):
            try:
                user_last_command[msg.from_user.id] = msg.text.split()[0][:32]
            except Exception:
                pass
            return
        # Maintenance mode + bot-ban gate (admins bypass)
        if await _maint_block(msg):
            return
        # Handle dot commands (.ban, .mute, etc.)
        try:
            from src.handlers_dotmod import handle_dot
            if await handle_dot(app, msg):
                return
        except Exception:
            traceback.print_exc()
        chat_id = msg.chat.id
        text_lo = msg.text.lower() if msg.text else ""
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        await increment_messages(msg.from_user.id)

        # Register group
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
            await db.commit()

        # Keyword filters
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT keyword,response FROM group_filters WHERE chat_id=?", (chat_id,)
            ) as cur:
                for kw, resp in await cur.fetchall():
                    if kw in text_lo:
                        await msg.reply(resp)
                        break

        # Group AI answers ONLY when mentioned/replied/tagged (never every message).
        # Group must have AI enabled; DM handler always replies (no trigger check there).
        settings = await group_settings(chat_id)
        if settings.get("ai_enabled") and should_ai_reply(msg) and not text_lo.startswith("/"):
            raw_text = msg.text or getattr(msg, "caption", None) or ""
            clean_text = raw_text
            for name in RIRURU_NAMES:
                clean_text = clean_text.replace(name, "")
            if BOT_USERNAME:
                clean_text = re.sub(rf"@{re.escape(BOT_USERNAME)}", "", clean_text,
                                    flags=re.IGNORECASE)
            clean_text = clean_text.strip()
            if not clean_text:
                clean_text = "haan?"
            if len(clean_text) >= 2:
                now = time.time()
                last_reply = GROUP_AI_LAST_REPLY.get(chat_id, 0)
                if now - last_reply >= GROUP_AI_REPLY_COOLDOWN:
                    GROUP_AI_LAST_REPLY[chat_id] = now
                    asyncio.create_task(group_ai_response(msg, clean_text))
                    return

        # Anti-spam: five messages in eight seconds gets a short mute.
        if settings.get("anti_spam_enabled", 1) and not await is_admin(chat_id, msg.from_user.id):
            key = (chat_id, msg.from_user.id)
            now = time.time()
            recent = SPAM_TRACKER[key]
            while recent and now - recent[0] > 8:
                recent.popleft()
            recent.append(now)
            if len(recent) >= 6:
                recent.clear()
                try:
                    from kittygram.types import ChatPermissions as _CP
                    await app.restrict_chat_member(
                        chat_id, msg.from_user.id,
                        permissions=_CP(can_send_messages=False),
                        until_date=datetime.utcnow() + timedelta(seconds=60),
                    )
                    await msg.reply(f"🔇 {mention(msg.from_user)} ᴋᴏ 𝟷 ᴍɪɴᴜᴛᴇ ᴍᴜᴛᴇ~ ꜱʟᴏᴡ ᴅᴏᴡɴ 🥺")
                except Exception:
                    traceback.print_exc()

        # Anti-abuse
        if any(g in text_lo for g in GAALI):
            if await is_admin(chat_id, msg.from_user.id):
                return
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO users (user_id,warnings) VALUES (?,1) "
                    "ON CONFLICT(user_id) DO UPDATE SET warnings=warnings+1",
                    (msg.from_user.id,)
                )
                await db.commit()
                async with db.execute(
                    "SELECT warnings FROM users WHERE user_id=?", (msg.from_user.id,)
                ) as cur:
                    row = await cur.fetchone()
                    warns = row[0] if row else 1

            if warns >= 3:
                try:
                    await app.ban_chat_member(chat_id, msg.from_user.id)
                    async with aiosqlite.connect(DB_PATH) as db:
                        await db.execute(
                            "UPDATE users SET warnings=0 WHERE user_id=?", (msg.from_user.id,)
                        )
                        await db.commit()
                    await send_mood(app, chat_id, 'furious',
                        f"🚫 {mention(msg.from_user)} **{ff('banned')}**!\n_{ff('3 strikes = out bhai 💀')}_")
                except Exception:
                    await msg.reply(ff("ban karna chahti thi, admin rights do mujhe 💀"))
            else:
                roasts = [
                    "arre~ aise mat bolo 🥺 be nice please~",
                    "kyaa~ gaali? Riruru ko dukh hua 😢 sorry bolo~",
                    "ehh~ such language! 🌸 seedha baat karo~",
                ]
                await msg.reply(
                    f"⚠️ {mention(msg.from_user)}, {random.choice(roasts)}\n"
                    f"_**{ff('Warning')} {warns}/3** — {3-warns} {ff('more and youre out')} 🚫_"
                )
    except Exception:
        traceback.print_exc()

# ══════════════════════════════════════════════════════════════════
#  🎰 CASINO & BOMB GAMES
# ══════════════════════════════════════════════════════════════════

def parse_bet(msg, min_bet=10):
    try:
        bet = int(msg.command[1])
        assert bet >= min_bet
        return bet
    except Exception:
        return None

# ─── /slots ───────────────────────────────────────────────────────
SLOT_SYMBOLS = ["🍒","🍋","🍇","⭐","💎","🎰","🍡"]

@app.on_message(filters.command("slots"), group=1)
async def cmd_slots(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg)
        if not bet:
            return await msg.reply("🎰 `/slots [bet]` — ᴍɪɴ 𝟷𝟶 ᴄᴏɪɴꜱ~ 💕")
        if not await debit_coins(msg.from_user.id, bet):
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~ ᴇᴀʀɴ ᴡɪᴛʜ `/daily`")
        s = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        spin_msg = await msg.reply(f"🎰 **ꜱᴩɪɴɴɪɴɢ~** ✨\n\n`[ ❓ | ❓ | ❓ ]`")
        await asyncio.sleep(1)
        if s[0] == s[1] == s[2] == "💎":
            mult, label = 10, "💎 **ᴊᴀᴄᴋᴩᴏᴛ!!** 💎"
        elif s[0] == s[1] == s[2]:
            mult, label = 5, "🌟 **ᴛʀɪᴩʟᴇ~** 🌟"
        elif s[0] == s[1] or s[1] == s[2] or s[0] == s[2]:
            mult, label = 2, "✨ **ᴍᴀᴛᴄʜ~** ✨"
        else:
            mult, label = 0, "😢 **ɴᴏ ʟᴜᴄᴋ~**"
        win = bet * mult
        if win: await update_coins(msg.from_user.id, win)
        await record_game(msg.from_user.id, "slots", bool(win))
        if s[0] == s[1] == s[2] == "💎":
            await unlock_achievement(msg.from_user.id, "jackpot_king")
        result = f"🎰 **ꜱʟᴏᴛꜱ** 💕\n\n`[ {s[0]} | {s[1]} | {s[2]} ]`\n\n{label}\n"
        result += f"+'`{win}`' 🪙" if win else f"-'`{bet}`' 🪙"
        await spin_msg.edit(result)
        if s[0] == s[1] == s[2] == "💎":
            slots_mood = 'excited'
        elif win:
            slots_mood = 'laughing'
        else:
            slots_mood = 'pout'
        await send_mood(app, msg.chat.id, slots_mood,
            f"[ {s[0]} | {s[1]} | {s[2]} ] — {label}"
        )
    except Exception:
        traceback.print_exc()

# ─── /coinflip ────────────────────────────────────────────────────
@app.on_message(filters.command("coinflip"), group=1)
async def cmd_coinflip(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg)
        if not bet:
            return await msg.reply("🪙 `/coinflip [bet]` — ᴍɪɴ 𝟷𝟶 ᴄᴏɪɴꜱ~ 💕")
        if not await debit_coins(msg.from_user.id, bet):
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~")
        flip_msg = await msg.reply("🪙 **ꜰʟɪᴩᴩɪɴɢ~** ✨")
        await asyncio.sleep(1)
        won = random.random() < 0.5
        if won: await update_coins(msg.from_user.id, bet * 2)
        await record_game(msg.from_user.id, "coinflip", won)
        result = (
            f"🪙 **ᴄᴏɪɴꜰʟɪᴩ** 💕\n\n"
            f"{'🟡 **ʜᴇᴀᴅꜱ~** ʏᴏᴜ ᴡɪɴ! 🎉' if won else '⚫ **ᴛᴀɪʟꜱ~** ʙᴇᴛᴛᴇʀ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ 🥺'}\n\n"
            f"{'+' if won else '-'}'`{bet}`' 🪙"
        )
        await flip_msg.edit(result)
        flip_mood = 'laughing' if won else 'pout'
        await send_mood(app, msg.chat.id, flip_mood,
            f"{'🟡 ʜᴇᴀᴅꜱ~ ᴡɪɴ!' if won else '⚫ ᴛᴀɪʟꜱ~ ʟᴜᴄᴋ ɴᴇxᴛ ᴛɪᴍᴇ'} {'+' if won else '-'}`{bet}` 🪙"
        )
    except Exception:
        traceback.print_exc()

# ─── /diceduel ────────────────────────────────────────────────────
@app.on_message(filters.command("diceduel"), group=1)
async def cmd_diceduel(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg)
        if not bet:
            return await msg.reply("🎲 `/diceduel [bet]` — ᴍɪɴ 𝟷𝟶 ᴄᴏɪɴꜱ~ 💕")
        if not await debit_coins(msg.from_user.id, bet):
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~")
        roll_msg = await msg.reply("🎲 **ʀᴏʟʟɪɴɢ~** ✨")
        await asyncio.sleep(1)
        faces = ["⚀","⚁","⚂","⚃","⚄","⚅"]
        p = random.randint(1, 6)
        m = random.randint(1, 6)
        if p > m:
            await update_coins(msg.from_user.id, bet * 2)
            outcome = f"🎉 **ʏᴏᴜ ᴡɪɴ~** +`{bet}` 🪙"
        elif p < m:
            outcome = f"😢 **ʀɪʀᴜʀᴜ ᴡɪɴꜱ~** -`{bet}` 🪙"
        else:
            await update_coins(msg.from_user.id, bet)
            outcome = f"🤝 **ᴅʀᴀᴡ~** ʙᴇᴛ ʀᴇᴛᴜʀɴᴇᴅ 🔄"
        await record_game(msg.from_user.id, "diceduel", p > m)
        await roll_msg.edit(
            f"🎲 **ᴅɪᴄᴇ ᴅᴜᴇʟ** 💕\n\n"
            f"ʏᴏᴜ: {faces[p-1]} `({p})`  ᴠꜱ  ʀɪʀᴜʀᴜ: {faces[m-1]} `({m})`\n\n{outcome}"
        )
        if p > m:
            duel_mood = 'wink_tongue'
        elif p < m:
            duel_mood = 'crying_hard'
        else:
            duel_mood = 'pout'
        await send_mood(app, msg.chat.id, duel_mood,
            f"ʏᴏᴜ: {faces[p-1]} `({p})`  ᴠꜱ  ʀɪʀᴜʀᴜ: {faces[m-1]} `({m})` — {outcome}"
        )
    except Exception:
        traceback.print_exc()

# ─── /blackjack ───────────────────────────────────────────────────
BJ_SESSIONS: dict = {}  # user_id → {deck, player, dealer, bet}

def bj_card_value(card):
    r = card[:-1]
    if r in ("J","Q","K"): return 10
    if r == "A": return 11
    return int(r)

def bj_hand_value(hand):
    val = sum(bj_card_value(c) for c in hand)
    aces = sum(1 for c in hand if c[:-1] == "A")
    while val > 21 and aces:
        val -= 10; aces -= 1
    return val

def bj_new_deck():
    suits = ["♠","♥","♦","♣"]
    ranks = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
    deck = [f"{r}{s}" for s in suits for r in ranks]
    random.shuffle(deck)
    return deck

def bj_hand_str(hand):
    return "  ".join(f"`{c}`" for c in hand)

def bj_keyboard(uid):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🃏 ʜɪᴛ",   callback_data=f"bj_hit_{uid}",   style="success"),
        InlineKeyboardButton("✋ ꜱᴛᴀɴᴅ", callback_data=f"bj_stand_{uid}", style="danger"),
    ]])

@app.on_message(filters.command("blackjack"), group=1)
async def cmd_blackjack(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg)
        if not bet:
            return await msg.reply("🃏 `/blackjack [bet]` — ᴍɪɴ 𝟷𝟶 ᴄᴏɪɴꜱ~ 💕")
        if not await debit_coins(msg.from_user.id, bet):
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~")
        uid = msg.from_user.id
        deck = bj_new_deck()
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        BJ_SESSIONS[uid] = {"deck": deck, "player": player, "dealer": dealer, "bet": bet}
        pv = bj_hand_value(player)
        text = (
            f"🃏 **ʙʟᴀᴄᴋᴊᴀᴄᴋ** 💕\n\n"
            f"🌸 **ʏᴏᴜʀ ʜᴀɴᴅ** `({pv})`:\n{bj_hand_str(player)}\n\n"
            f"🌸 **ʀɪʀᴜʀᴜ'ꜱ ʜᴀɴᴅ**:\n`{dealer[0]}`  `??`\n\n"
            f"💰 **ʙᴇᴛ:** `{bet}` 🪙"
        )
        if pv == 21:
            win = int(bet * 1.5)
            await update_coins(uid, bet + win)
            await record_game(uid, "blackjack", True)
            await unlock_achievement(uid, "jackpot_king")
            BJ_SESSIONS.pop(uid, None)
            await send_mood(app, msg.chat.id, 'cheerful',
                text + f"\n\n🎉 **ʙʟᴀᴄᴋᴊᴀᴄᴋ~** +`{win}` 🪙"
            )
            return
        await msg.reply(text, reply_markup=bj_keyboard(uid))
    except Exception:
        traceback.print_exc()

@app.on_callback_query(filters.regex(r"^bj_(hit|stand)_(\d+)$"))
async def bj_callback(_, cq: CallbackQuery):
    try:
        action = cq.data.split("_")[1]
        uid = int(cq.data.split("_")[2])
        if cq.from_user.id != uid:
            return await cq.answer("ʏᴇ ᴛᴇʀɪ ɢᴀᴍᴇ ɴᴀʜɪ ʜᴀɪ~ 🥺", show_alert=True)
        sess = BJ_SESSIONS.get(uid)
        if not sess:
            return await cq.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ɢᴀᴍᴇ~ ᴜꜱᴇ /blackjack", show_alert=True)
        await cq.answer()
        deck, player, dealer, bet = sess["deck"], sess["player"], sess["dealer"], sess["bet"]

        if action == "hit":
            player.append(deck.pop())
            pv = bj_hand_value(player)
            if pv > 21:
                BJ_SESSIONS.pop(uid, None)
                await record_game(uid, "blackjack", False)
                text = (
                    f"🃏 **ʙʟᴀᴄᴋᴊᴀᴄᴋ** 💕\n\n"
                    f"🌸 **ʏᴏᴜʀ ʜᴀɴᴅ** `({pv})`:\n{bj_hand_str(player)}\n\n"
                    f"💥 **ʙᴜꜱᴛ!** -`{bet}` 🪙 🥺"
                )
                await cq.edit_message_text(text)
                await send_mood(app, cq.message.chat.id, 'sad',
                    f"💥 ʙᴜꜱᴛ! -`{bet}` 🪙 🥺"
                )
                return
            dv = bj_hand_value(dealer)
            text = (
                f"🃏 **ʙʟᴀᴄᴋᴊᴀᴄᴋ** 💕\n\n"
                f"🌸 **ʏᴏᴜʀ ʜᴀɴᴅ** `({pv})`:\n{bj_hand_str(player)}\n\n"
                    f"🌸 **ʀɪʀᴜʀᴜ'ꜱ ʜᴀɴᴅ**:\n`{dealer[0]}`  `??`\n\n"
                f"💰 **ʙᴇᴛ:** `{bet}` 🪙"
            )
            await cq.edit_message_text(text, reply_markup=bj_keyboard(uid))

        elif action == "stand":
            while bj_hand_value(dealer) < 17:
                dealer.append(deck.pop())
            pv = bj_hand_value(player)
            dv = bj_hand_value(dealer)
            BJ_SESSIONS.pop(uid, None)
            if dv > 21 or pv > dv:
                await update_coins(uid, bet * 2)
                outcome = f"🎉 **ʏᴏᴜ ᴡɪɴ~** +`{bet}` 🪙"
                won = True
            elif pv == dv:
                await update_coins(uid, bet)
                outcome = f"🤝 **ᴘᴜꜱʜ~** ʙᴇᴛ ʀᴇᴛᴜʀɴᴇᴅ 🔄"
                won = False
            else:
                outcome = f"😢 **ʀɪʀᴜʀᴜ ᴡɪɴꜱ~** -`{bet}` 🪙"
                won = False
            await record_game(uid, "blackjack", won)
            text = (
                f"🃏 **ʙʟᴀᴄᴋᴊᴀᴄᴋ** 💕\n\n"
                f"🌸 **ʏᴏᴜʀ ʜᴀɴᴅ** `({pv})`:\n{bj_hand_str(player)}\n\n"
                f"🌸 **ʀɪʀᴜʀᴜ'ꜱ ʜᴀɴᴅ** `({dv})`:\n{bj_hand_str(dealer)}\n\n{outcome}"
            )
            await cq.edit_message_text(text)
            bj_mood = 'cheerful' if won else 'sad'
            await send_mood(app, cq.message.chat.id, bj_mood, outcome)
    except Exception:
        traceback.print_exc()

# ─── /bomb ────────────────────────────────────────────────────────
# 5×5 grid, user picks bomb count (1-20), dynamic multiplier
BOMB_SESSIONS: dict = {}  # uid → {bombs: set, bet, revealed: set, bomb_count}
BOMB_PENDING: dict = {}   # uid → {bet, chat_id, message_id, expires}
GRID_SIZE = 25  # 5×5

def bomb_multiplier(safe_count: int, bomb_count: int) -> float:
    """Higher bomb count = higher reward per safe tile."""
    total_safe = GRID_SIZE - bomb_count
    if safe_count == 0 or total_safe == 0:
        return 1.0
    # Base multiplier scales with danger (more bombs = steeper curve)
    base = 1.0 + (bomb_count / GRID_SIZE) * 1.5
    return round(base ** safe_count, 2)

def bomb_keyboard(uid, revealed: set, bomb_positions: set, game_over=False, cash_out=False):
    rows = []
    for r in range(5):
        row = []
        for c in range(5):
            idx = r * 5 + c
            if idx in revealed:
                # Already revealed safe — green
                row.append(InlineKeyboardButton(
                    "✅", callback_data=f"bomb_done_{uid}_{idx}", style="success"
                ))
            elif game_over and idx in bomb_positions:
                # Reveal all bombs on game over — red
                row.append(InlineKeyboardButton(
                    "💣", callback_data=f"bomb_done_{uid}_{idx}", style="danger"
                ))
            elif game_over:
                # Unrevealed safe tiles on loss
                row.append(InlineKeyboardButton(
                    "🟦", callback_data=f"bomb_done_{uid}_{idx}", style="primary"
                ))
            else:
                # Still pickable
                row.append(InlineKeyboardButton(
                    "🟦", callback_data=f"bomb_pick_{uid}_{idx}", style="primary"
                ))
        rows.append(row)
    if not game_over and cash_out:
        rows.append([InlineKeyboardButton(
            "💰 ᴄᴀꜱʜ ᴏᴜᴛ~", callback_data=f"bomb_cash_{uid}", style="success"
        )])
    return InlineKeyboardMarkup(rows)

def bomb_count_keyboard(uid, bet):
    """Let user pick how many bombs they want."""
    options = [1, 3, 5, 10, 15, 20]
    rows = []
    styles = ["success", "success", "primary", "primary", "danger", "danger"]
    row = []
    for i, n in enumerate(options):
        row.append(InlineKeyboardButton(
            f"💣 {n}", callback_data=f"bomb_start_{uid}_{bet}_{n}", style=styles[i]
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data=f"bomb_cancel_{uid}", style="danger")])
    return InlineKeyboardMarkup(rows)

@app.on_message(filters.command("bomb"), group=1)
async def cmd_bomb(_, msg: Message):
    try:
        if await _maint_block(msg):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        bet = parse_bet(msg)
        if not bet:
            return await msg.reply(
                "💣 **ʙᴏᴍʙ ɢᴀᴍᴇ** 💕\n\n"
                "Usage: `/bomb [bet]`\n"
                "_ᴍɪɴ 𝟷𝟶 ᴄᴏɪɴꜱ~ ᴛʜᴇɴ ᴄʜᴏᴏꜱᴇ ʙᴏᴍʙ ᴄᴏᴜɴᴛ!_"
            )
        user = await get_user(msg.from_user.id)
        if not user or user["coins"] < bet:
            return await msg.reply("🥺 ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ~")
        uid = msg.from_user.id
        prompt = await msg.reply(
            f"💣 **ʙᴏᴍʙ ɢᴀᴍᴇ** — 𝟻×𝟻 ɢʀɪᴅ 💕\n\n"
            f"💰 **ʙᴇᴛ:** `{bet}` 🪙\n\n"
            f"🎯 ᴄʜᴏᴏꜱᴇ ʜᴏᴡ ᴍᴀɴʏ 💣 ʙᴏᴍʙꜱ~\n"
            f"_ᴍᴏʀᴇ ʙᴏᴍʙꜱ = ʜɪɢʜᴇʀ ʀᴇᴡᴀʀᴅꜱ ✨_",
            reply_markup=bomb_count_keyboard(uid, bet)
        )
        BOMB_PENDING[uid] = {
            "bet": bet,
            "chat_id": msg.chat.id,
            "message_id": prompt.id,
            "expires": time.time() + 120,
        }
    except Exception:
        traceback.print_exc()

@app.on_callback_query(filters.regex(r"^bomb_start_(\d+)_(\d+)_(\d+)$"))
async def bomb_start_callback(_, cq: CallbackQuery):
    try:
        parts = cq.data.split("_")
        uid = int(parts[2])
        bet = int(parts[3])
        bomb_count = int(parts[4])
        if cq.from_user.id != uid:
            return await cq.answer("ʏᴇ ᴛᴇʀɪ ɢᴀᴍᴇ ɴᴀʜɪ~ 🥺", show_alert=True)
        pending = BOMB_PENDING.get(uid)
        if (
            not pending
            or time.time() > pending["expires"]
            or pending["bet"] != bet
            or pending["chat_id"] != cq.message.chat.id
            or pending["message_id"] != cq.message.id
        ):
            BOMB_PENDING.pop(uid, None)
            return await cq.answer("ʏᴇ ᴘᴜʀᴀɴᴀ ʙᴏᴍʙ ᴘʀᴏᴍᴩᴛ ʜᴀɪ~ /bomb ꜱᴇ ɴʏᴀ ᴋᴀʀᴏ", show_alert=True)
        if bomb_count not in (1, 3, 5, 10, 15, 20) or bomb_count >= GRID_SIZE:
            return await cq.answer("ɪɴᴠᴀʟɪᴅ ʙᴏᴍʙ ᴄᴏᴜɴᴛ~", show_alert=True)
        if uid in BOMB_SESSIONS:
            return await cq.answer("ᴛᴇʀᴀ ᴇᴋ ʙᴏᴍʙ ɢᴀᴍᴇ ᴀʟʀᴇᴀᴅʏ ᴄʜᴀʟ ʀᴀʜᴀ~", show_alert=True)
        if not await debit_coins(uid, bet):
            return await cq.answer("ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ~ 🥺", show_alert=True)
        BOMB_PENDING.pop(uid, None)
        await cq.answer()
        # Place bombs randomly
        bombs = set(random.sample(range(GRID_SIZE), bomb_count))
        BOMB_SESSIONS[uid] = {
            "bombs": bombs,
            "bet": bet,
            "bomb_count": bomb_count,
            "revealed": set()
        }
        total_safe = GRID_SIZE - bomb_count
        mult_preview = bomb_multiplier(1, bomb_count)
        await cq.edit_message_text(
            f"💣 **ʙᴏᴍʙ ɢᴀᴍᴇ** — 𝟻×𝟻 💕\n\n"
            f"💣 **ʙᴏᴍʙꜱ:** `{bomb_count}` | 🟦 **ꜱᴀꜰᴇ ᴛɪʟᴇꜱ:** `{total_safe}`\n"
            f"💰 **ʙᴇᴛ:** `{bet}` 🪙\n"
            f"📈 **𝟷ꜱᴛ ᴛɪʟᴇ ᴍᴜʟᴛ:** `{mult_preview}x`\n\n"
            f"_ᴛᴀᴩ ᴀ ᴛɪʟᴇ ᴛᴏ ꜱᴛᴀʀᴛ~ ʜɪᴛ 💣 = ʟᴏꜱᴇ ᴀʟʟ!_",
            reply_markup=bomb_keyboard(uid, set(), bombs)
        )
    except Exception:
        traceback.print_exc()
        try:
            await cq.answer("ʙᴏᴍʙ ɢᴀᴍᴇ ᴍᴇ ᴛʜᴏᴅᴀ ɪꜱꜱᴜᴇ ʜᴜᴀ~", show_alert=True)
        except Exception:
            pass

@app.on_callback_query(filters.regex(r"^bomb_cancel_(\d+)$"))
async def bomb_cancel_callback(_, cq: CallbackQuery):
    try:
        uid = int(cq.data.split("_")[2])
        if cq.from_user.id != uid:
            return await cq.answer("ʏᴇ ᴛᴇʀɪ ɴᴀʜɪ~ 🥺", show_alert=True)
        BOMB_PENDING.pop(uid, None)
        await cq.answer()
        await cq.edit_message_text("❌ ɢᴀᴍᴇ ᴄᴀɴᴄᴇʟʟᴇᴅ~ 🌸")
    except Exception:
        traceback.print_exc()

@app.on_callback_query(filters.regex(r"^bomb_(pick|cash|done)_(\d+)(?:_(\d+))?$"))
async def bomb_callback(_, cq: CallbackQuery):
    try:
        parts = cq.data.split("_")
        action = parts[1]
        uid = int(parts[2])

        if action == "done":
            return await cq.answer("ɢᴀᴍᴇ ᴏᴠᴇʀ~ 🥺", show_alert=False)

        if cq.from_user.id != uid:
            return await cq.answer("ʏᴇ ᴛᴇʀɪ ɢᴀᴍᴇ ɴᴀʜɪ~ 🥺", show_alert=True)
        sess = BOMB_SESSIONS.get(uid)
        if not sess:
            return await cq.answer("ɴᴏ ᴀᴄᴛɪᴠᴇ ɢᴀᴍᴇ~ /bomb ꜱᴇ ꜱʜᴜʀᴜ ᴋᴀʀᴏ", show_alert=True)
        await cq.answer()

        bet        = sess["bet"]
        bombs      = sess["bombs"]
        bomb_count = sess["bomb_count"]
        revealed   = sess["revealed"]
        total_safe = GRID_SIZE - bomb_count

        if action == "pick":
            idx = int(parts[3])
            if not 0 <= idx < GRID_SIZE:
                return await cq.answer("ɪɴᴠᴀʟɪᴅ ᴛɪʟᴇ~", show_alert=True)
            if idx in revealed:
                return await cq.answer("ᴀʟʀᴇᴀᴅʏ ᴘɪᴄᴋᴇᴅ~ 🌸")

            if idx in bombs:
                # BOOM — lose all
                BOMB_SESSIONS.pop(uid, None)
                mult = bomb_multiplier(len(revealed), bomb_count)
                await record_game(uid, "bomb", False)
                await cq.edit_message_text(
                    f"💥 **ʙᴏᴏᴍ!** 💣\n\n"
                    f"ᴀʀᴀ~ ᴛᴜᴍɴᴇ ʙᴏᴍʙ ʜɪᴛ ᴋɪʏᴀ 🥺\n"
                    f"✅ ꜱᴀꜰᴇ ᴛɪʟᴇꜱ: `{len(revealed)}`\n"
                    f"-`{bet}` 🪙 ʟᴏꜱᴛ~",
                    reply_markup=bomb_keyboard(uid, revealed, bombs, game_over=True)
                )
                await send_mood(app, cq.message.chat.id, 'dead',
                    f"💥 ʙᴏᴏᴍ! 💣 -`{bet}` 🪙 ʟᴏꜱᴛ~"
                )
            else:
                revealed.add(idx)
                safe_count = len(revealed)
                mult = bomb_multiplier(safe_count, bomb_count)
                win_preview = int(bet * mult)
                remaining_safe = total_safe - safe_count

                if remaining_safe == 0:
                    # Auto cash out — all safe tiles found!
                    BOMB_SESSIONS.pop(uid, None)
                    await update_coins(uid, win_preview)
                    await record_game(uid, "bomb", True)
                    await unlock_achievement(uid, "bomb_survivor")
                    await cq.edit_message_text(
                        f"🏆 **ᴩᴇʀꜰᴇᴄᴛ!** ᴀʟʟ ꜱᴀꜰᴇ ᴛɪʟᴇꜱ~ 💕\n\n"
                        f"✅ `{safe_count}/{total_safe}` ᴛɪʟᴇꜱ | `{mult}x`\n"
                        f"+`{win_preview}` 🪙 🎉",
                        reply_markup=bomb_keyboard(uid, revealed, bombs, game_over=True)
                    )
                    await send_mood(app, cq.message.chat.id, 'party',
                        f"🏆 ᴘᴇʀꜰᴇᴄᴛ! ᴀʟʟ ꜱᴀꜰᴇ ᴛɪʟᴇꜱ~ +`{win_preview}` 🪙 🎉"
                    )
                else:
                    await cq.edit_message_text(
                        f"💣 **ʙᴏᴍʙ ɢᴀᴍᴇ** — 𝟻×𝟻 💕\n\n"
                        f"💣 ʙᴏᴍʙꜱ: `{bomb_count}` | ✅ ꜱᴀꜰᴇ: `{safe_count}/{total_safe}`\n"
                        f"📈 **ᴍᴜʟᴛɪᴩʟɪᴇʀ:** `{mult}x`\n"
                        f"💰 **ᴄᴀꜱʜ ᴏᴜᴛ ɴᴏᴡ:** `{win_preview}` 🪙\n"
                        f"_🟦 {remaining_safe} ꜱᴀꜰᴇ ᴛɪʟᴇꜱ ʀᴇᴍᴀɪɴɪɴɢ~_",
                        reply_markup=bomb_keyboard(uid, revealed, bombs, cash_out=True)
                    )

        elif action == "cash":
            safe_count = len(revealed)
            if safe_count == 0:
                return await cq.answer("ᴩᴇʜʟᴇ ᴋᴏɪ ᴛɪʟᴇ ᴛᴏ ᴩɪᴄᴋ ᴋᴀʀᴏ~ 🥺", show_alert=True)
            mult = bomb_multiplier(safe_count, bomb_count)
            win = int(bet * mult)
            BOMB_SESSIONS.pop(uid, None)
            await update_coins(uid, win)
            await record_game(uid, "bomb", True)
            await unlock_achievement(uid, "bomb_survivor")
            await cq.edit_message_text(
                f"💰 **ᴄᴀꜱʜᴇᴅ ᴏᴜᴛ~** 🎉\n\n"
                f"✅ `{safe_count}/{total_safe}` ꜱᴀꜰᴇ ᴛɪʟᴇꜱ | `{mult}x`\n"
                f"+`{win}` 🪙 ᴡᴏɴ~ 💕",
                reply_markup=bomb_keyboard(uid, revealed, bombs, game_over=True)
            )
            await send_mood(app, cq.message.chat.id, 'party',
                f"💰 ᴄᴀꜱʜᴇᴅ ᴏᴜᴛ~ +`{win}` 🪙 🎉"
            )

    except Exception:
        traceback.print_exc()
        try:
            await cq.answer("ʙᴏᴍʙ ᴍᴇ ᴛʜᴏᴅᴀ ɪꜱꜱᴜᴇ ʜᴜᴀ~", show_alert=True)
        except Exception:
            pass

# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
async def main():
    global BOT_USERNAME, BOT_ID
    await init_db()
    await setup_faces()
    try:
        _nkeys = await rebuild_groq_pool()
        print(f"  AI keys : ✅ { _nkeys} active Groq keys in pool")
    except Exception as _e:
        print(f"  AI keys : ⚠️ pool rebuild failed: {_e}")
    print("=" * 55)
    print("  🌸 ʀɪʀᴜʀᴜ ʙᴏᴛ — Starting up~ 💕")
    print(f"  DB      : {DB_PATH}")
    print(f"  Owner   : {OWNER_ID if OWNER_ID else 'NOT SET (admin panel disabled)'}")
    print("=" * 55)

    # Delete any existing webhook so long-polling works
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=false"
            ) as r:
                data = await r.json()
                print(f"  Webhook : deleted → {data.get('result', data)}")
            # Also log webhook info for debug
            async with session.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
            ) as r:
                wh = await r.json()
                print(f"  WebhookInfo: {wh.get('result', {})}")
    except Exception as e:
        print(f"  Webhook cleanup error: {e}")


    # FIX 1A: register multi-file handlers here (loop is running, before polling)
    try:
        from src import handlers_economy, handlers_powers, handlers_social, handlers_utility, handlers_games
        handlers_economy.register(app)
        handlers_powers.register(app)
        handlers_social.register(app)
        handlers_utility.register(app)
        handlers_games.register(app)
        from src import handlers_ttt
        handlers_ttt.register(app)
        print("  Modules : ✅ src handlers loaded (economy/powers/social/utility/games/ttt)")
    except Exception as _e:
        print(f"  Modules : ⚠️ src load issue: {_e}")
        traceback.print_exc()

    await app.start()
    me = await app.get_me()
    BOT_USERNAME = (me.username or "").lower()
    BOT_ID = me.id
    print(f"  Bot     : @{me.username} (ID: {me.id})")
    print(f"  Database: {'Turso libSQL' if USE_TURSO else 'local SQLite'}")
    print("  Status  : ✅ Bot is LIVE! Send /start in Telegram.")
    print("=" * 55)
    start_webserver()  # keeps Render alive — UptimeRobot pings /ping
    lottery_task = asyncio.create_task(lottery_worker())
    try:
        await idle()
    finally:
        lottery_task.cancel()
        await app.stop()

if __name__ == "__main__":
    # Pyrogram registers decorator handlers on its current event loop.
    # app.run(main()) keeps that same loop; asyncio.run(main()) creates a
    # different loop and leaves those handlers unregistered.
    app.run(main())
