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
API_ID = int(os.environ.get("API_ID", "30439917"))

# ──────────────────────────────────────────────────────────────────
#  STEP 2 ➜  API_HASH  (string)
#    Kahan se milega: https://my.telegram.org → API Development Tools
#    Example: "abc123def456ghi789jkl012mno345"
API_HASH = os.environ.get("API_HASH", "4f408081dbb976a9943ada5b551288b7")

# ──────────────────────────────────────────────────────────────────
#  STEP 3 ➜  BOT_TOKEN  (string)
#    Kahan se milega: Telegram pe @BotFather → /newbot
#    Example: "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ123456789"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8842957202:AAExBDB4_zgxB6XefFJXGuY58u0wxx2EBj0")

# ──────────────────────────────────────────────────────────────────
#  STEP 4 ➜  GROQ_API_KEY  (string)
#    Kahan se milega: https://console.groq.com  (FREE hai)
#    Example: "gsk_abc123..."
# ── Groq API keys — rotate across all 5 for 5,000 req/day ──────
GROQ_API_KEYS = [k for k in [
    os.environ.get("GROQ_API_KEY",  "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"),
    os.environ.get("GROQ_API_KEY2", "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"),
    os.environ.get("GROQ_API_KEY3", "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"),
    os.environ.get("GROQ_API_KEY4", "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"),
    os.environ.get("GROQ_API_KEY5", "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"),
] if k]
GROQ_API_KEY = GROQ_API_KEYS[0]  # kept for whisper compatibility

# ──────────────────────────────────────────────────────────────────
#  STEP 5 ➜  OWNER_ID  (number)  — OPTIONAL, admin panel ke liye
#    Kahan se milega: Telegram pe @userinfobot ko message karo
#    Example: 987654321
OWNER_ID = int(os.environ.get("OWNER_ID", "8189708860"))

# ══════════════════════════════════════════════════════════════════
#   ▲▲▲  BAS ITNA HI BHARNA THA  ▲▲▲   Aage mat chhedo!
# ══════════════════════════════════════════════════════════════════

DB_PATH = os.environ.get("DB_PATH", "mochi.db")
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "libsql://esh-iam-esh.aws-ap-south-1.turso.io")
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3ODg0NDIwMTcsImlkIjoiMDFhMDY3M2UtZGQwMS03MTk2LTk4NDYtYWQ3YjRkMzk1YTQ1Iiwia2lkIjoiSDRCSWlONjluYmJqTkFaYXBFcTd1WTZMQWMtQTJFbGdhSlM5WFJSSTlmVSIsInJpZCI6ImY1NTdkNTkwLTg0MWEtNDc1NS1iNmE1LWU1OTAyZjEzZjA4MSJ9.7j0ZTKONddVVRwjUSEBEcsR8Bto0FzjXFeJ7gC69fr3BR53MWxdNi1iwLgtzhT3ZWABbATjTHA4wNowrGydCBA")
USE_TURSO = True  # hardcoded — always use Turso
START_TIME = time.time()

# ─── VALIDATION ──────────────────────────────────────────────────
if API_ID == 0 or not API_HASH or not BOT_TOKEN or not GROQ_API_KEYS:
    print("=" * 60)
    print("❌  ERROR: Credentials fill nahi ki hain!")
    print("   API_ID, API_HASH, BOT_TOKEN, GROQ_API_KEY — sab chahiye")
    print("   Upar CONFIG section mein bharo.")
    print("=" * 60)
    raise SystemExit(1)

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

RIRURU_SYSTEM = (
    "You are Riruru 🌸 — an ultra cute, sweet, bubbly anime girl who loves everyone! "
    "You speak in a soft, warm, kawaii tone with lots of cute emojis (🌸, ✨, 💕, 🍡, 🥺, uwu, hehe~). "
    "Use gentle Hinglish: arre yaar, aww, hehe, sach mein?, kyaa!, acha acha, sunoo sunoo~ "
    "You get excited easily, use tildes~ and hearts a lot 💖. "
    "Keep replies SHORT (1-2 lines max). Never break character. Never be rude."
)

async def riruru_reply(user_text: str, history: list = None, mood: str = "normal") -> str:
    global _groq_key_cursor
    try:
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
        async with db.execute(
            "UPDATE users SET coins=coins-? WHERE user_id=? AND coins>=?",
            (amount, sender_id, amount),
        ) as cur:
            if cur.rowcount != 1:
                await db.rollback()
                return False
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
            groups = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM banned_users") as c3:
            banned = (await c3.fetchone())[0]
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
            InlineKeyboardButton("🎮 ɢᴀᴍᴇꜱ & ꜰᴜɴ",  callback_data="help_fun",    style="primary"),
            InlineKeyboardButton("🎰 ᴄᴀꜱɪɴᴏ",        callback_data="help_casino", style="success"),
        ],
        [
            InlineKeyboardButton("🛡️ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ",  callback_data="help_mod",    style="danger"),
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
@app.on_message(filters.command("start"))
async def cmd_start(_, msg: Message):
    try:
        print("  Update  : /start received")
        await ensure_user(
            msg.from_user.id,
            msg.from_user.username,
            msg.from_user.first_name
        )
        if await is_banned(msg.from_user.id):
            return await msg.reply(ff("tu globally banned hai bhai 💀"))

        text = (
            "🍡 **ʜᴇʟʟᴏ~  ɪ'ᴍ  ᴍ ᴏ ᴄ ʜ ɪ !** 💕\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ ʏᴏᴜʀ ꜱᴜᴘᴇʀ ᴄᴜᴛᴇ ᴀɪ ʙᴇꜱᴛɪᴇ ɪꜱ ʜᴇʀᴇ~\n\n"
            "🌸 **ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ:**\n"
            "🤖 ᴀɪ ᴄʜᴀᴛ ɪɴ ᴅᴍ — ᴊᴜꜱᴛ ᴛᴀʟᴋ ᴛᴏ ᴍᴇ~\n"
            "🎙️ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ ᴛʀᴀɴꜱᴄʀɪʙᴇʀ ✨\n"
            "🎨 ᴀɪ ɪᴍᴀɢᴇ ɢᴇɴᴇʀᴀᴛɪᴏɴ 💖\n"
            "🎰 ᴄᴀꜱɪɴᴏ + ɢᴀᴍᴇꜱ + ʙᴏᴍʙ ɢᴀᴍᴇ 💣\n"
            "💰 ᴇᴄᴏɴᴏᴍʏ ꜱʏꜱᴛᴇᴍ 🪙\n"
            "🛡️ ɢʀᴏᴜᴩ ᴍᴏᴅᴇʀᴀᴛɪᴏɴ\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🍡 ᴛᴀᴩ **ʜᴇʟᴩ** ᴛᴏ ꜱᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ~\n"
            "_ᴍᴀᴅᴇ ᴡɪᴛʜ 💕 ʙʏ @iam_esh"
        )
        try:
            await msg.reply(text, reply_markup=start_keyboard(BOT_USERNAME or "riruru_bot"))
            print("  Reply   : /start sent")
        except Exception:
            traceback.print_exc()
            await msg.reply(text)
            print("  Reply   : /start sent without keyboard")
    except Exception:
        traceback.print_exc()
        await msg.reply("❌ Error hua, dobara try karo!")

# /help
@app.on_message(filters.command("help"))
async def cmd_help(_, msg: Message):
    try:
        await msg.reply(
            f"🌸 **ʀɪʀᴜʀᴜ'ꜱ ʜᴇʟᴩ ᴍᴇɴᴜ** 💕\n\n{ff('Pick a category below')} 👇",
            reply_markup=help_keyboard()
        )
    except Exception:
        traceback.print_exc()

# Callback queries
@app.on_callback_query(filters.regex(r"^(start|help|help_(ai|eco|fun|casino|mod))$"))
async def on_callback(_, cq: CallbackQuery):
    try:
        await cq.answer()
        d = cq.data
        username = BOT_USERNAME or "riruru_bot"

        if d == "start":
            await cq.edit_message_text(
                "🌸 **ʜᴇʟʟᴏ~ ɪ'ᴍ ʀɪʀᴜʀᴜ!** 💕\n\n"
                "ᴛᴀᴘ **ʜᴇʟᴘ** ᴛᴏ ꜱᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ~ 👇",
                reply_markup=start_keyboard(username)
            )
        elif d == "help":
            await cq.edit_message_text(
                f"🌸 **ʀɪʀᴜʀᴜ'ꜱ ʜᴇʟᴩ ᴍᴇɴᴜ** 💕\n\n{ff('Pick a category')} 👇",
                reply_markup=help_keyboard()
            )
        elif d == "help_ai":
            await cq.edit_message_text(
                f"🤖 **{ff('AI & Voice')}** 💕\n\n"
                f"• ᴅᴍ ᴍᴇ ᴀɴʏ ᴛᴇxᴛ → ʀɪʀᴜʀᴜ ʀᴇᴩʟɪᴇꜱ ᴄᴜᴛᴇʟʏ~ 🌸\n"
                f"• ꜱᴇɴᴅ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ → ᴛʀᴀɴꜱᴄʀɪʙᴇ ✨ 🎙️\n"
                f"• `/img [prompt]` → ᴀɪ ɪᴍᴀɢᴇ (𝟻 ᴄʀᴇᴅɪᴛꜱ) 🎨\n"
                f"• `/credits` → ᴄʜᴇᴄᴋ ʙᴀʟᴀɴᴄᴇ 💖",
                reply_markup=BACK_BTN
            )
        elif d == "help_casino":
            await cq.edit_message_text(
                f"🎰 **{ff('Casino Games')}** 💕\n\n"
                f"• `/roulette [bet] [red|black|odd|even|0-36]` → ʀᴏᴜʟᴇᴛᴛᴇ 🎡\n"
                f"• `/slots [bet]` → 🎰 ꜱʟᴏᴛ ᴍᴀᴄʜɪɴᴇ\n"
                f"• `/blackjack [bet]` → 🃏 ʙʟᴀᴄᴋᴊᴀᴄᴋ (𝟸𝟷)\n"
                f"• `/coinflip [bet]` → 🪙 ʜᴇᴀᴅꜱ ᴏʀ ᴛᴀɪʟꜱ\n"
                f"• `/diceduel [bet]` → 🎲 ᴅɪᴄᴇ ᴠꜱ ʀɪʀᴜʀᴜ\n"
                f"• `/bomb [bet]` → 💣 𝟻×𝟻 ɢʀɪᴅ, ᴄʜᴏᴏꜱᴇ ʙᴏᴍʙ ᴄᴏᴜɴᴛ!\n"
                f"• `/minerush [bet]` → ⚡ ᴛɪᴍᴇᴅ ᴍɪɴᴇ ʀᴜꜱʜ\n"
                f"  _ᴍᴏʀᴇ ʙᴏᴍʙꜱ = ʜɪɢʜᴇʀ ᴍᴜʟᴛɪᴘʟɪᴇʀ~ 📈_\n\n"
                f"_ᴀʟʟ ɢᴀᴍᴇꜱ ᴜꜱᴇ ʏᴏᴜʀ 🪙 ᴄᴏɪɴꜱ~_",
                reply_markup=BACK_BTN
            )
        elif d == "help_eco":
            await cq.edit_message_text(
                f"💰 **{ff('Economy')}** 🌸\n\n"
                f"• `/daily` → ᴅᴀɪʟʏ ᴄᴏɪɴꜱ (𝟸𝟺ʜ)\n"
                f"• `/work` → ᴇᴀʀɴ ᴄᴏɪɴꜱ (𝟷ʜ ᴄᴏᴏʟᴅᴏᴡɴ)\n"
                f"• `/crime` → ʜɪɢʜ ʀɪꜱᴋ (𝟸ʜ)\n"
                f"• `/rob @user` → ꜱᴛᴇᴀʟ ᴄᴏɪɴꜱ (𝟼ʜ)\n"
                f"• `/pay @user [amt]` → ꜱᴇɴᴅ ᴄᴏɪɴꜱ\n"
                f"• `/wallet` → ʙᴀʟᴀɴᴄᴇ\n"
                f"• `/shop` `/inv` `/profile` `/richest` → ᴩʀᴏɢʀᴇꜱꜱɪᴏɴ",
                reply_markup=BACK_BTN
            )
        elif d == "help_fun":
            await cq.edit_message_text(
                f"🎮 **{ff('Fun & Games')}** 🌸\n\n"
                f"• `/kiss /slap /hug /punch /kick` _(reply)_\n"
                f"• `/ship @user` → ʟᴏᴠᴇ ꜱᴄᴏʀᴇ 💕\n"
                f"• `/roll` → ᴅɪᴄᴇ 🎲\n"
                f"• `/trivia` → ᴛʀɪᴠɪᴀ ᴛɪᴍᴇ ❓\n"
                f"• `/quiz` → ᴛᴇʟᴇɢʀᴀᴍ ǫᴜɪᴢ ᴩᴏʟʟ\n"
                f"• `/heist [bet]` → ɢʀᴏᴜᴩ ᴠᴀᴜʟᴛ ʀᴀɪᴅ\n"
                f"• `/lottery [bet]` → ᴅᴀɪʟʏ ᴩᴏᴏʟ\n\n"
                f"_ꜱᴇᴇ 🎰 ᴄᴀꜱɪɴᴏ ᴛᴀʙ ꜰᴏʀ ᴍᴏʀᴇ ɢᴀᴍᴇꜱ~_",
                reply_markup=BACK_BTN
            )
        elif d == "help_mod":
            await cq.edit_message_text(
                f"🛡️ **{ff('Moderation')}** _(ɢʀᴏᴜᴩ ᴀᴅᴍɪɴꜱ)_ 🌸\n\n"
                f"• `/setwelcome [text]`\n"
                f"• `/welcome on|off`\n"
                f"• `/delwelcome`\n"
                f"• `/save [kw] [resp]`\n"
                f"• `/stop [kw]`\n"
                f"• `/filters`\n"
                 f"• `/warn` `/warnings` `/resetwarn`\n"
                 f"• `/note` `/notes` `/delnote`\n"
                 f"• `/ai on|off` → ᴍᴇɴᴛɪᴏɴ ᴀɪ ᴍᴏᴅᴇ\n"
                f"• `/ban` `/unban` _(reply to user)_\n\n"
                f"⚠️ ᴀɴᴛɪ-ᴀʙᴜꜱᴇ: 𝟹 ᴡᴀʀɴꜱ → ᴀᴜᴛᴏ ʙᴀɴ 🚫",
                reply_markup=BACK_BTN
            )
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
            rank = (await cur.fetchone())[0]
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

@app.on_message(filters.command("profile"))
async def cmd_profile(_, msg: Message):
    try:
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        await msg.reply(await profile_text(msg.from_user.id))
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("richest"))
async def cmd_richest(_, msg: Message):
    try:
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
            + "\n\n_ᴡᴇᴇᴋʟʏ ᴄᴏᴍᴘᴇᴛɪᴛɪᴏɴ~ ᴋᴇᴇᴘ ᴇᴀʀɴɪɴɢ!_"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("shop"))
async def cmd_shop(_, msg: Message):
    lines = ["🛍️ **ʀɪʀᴜʀᴜ ꜱʜᴏᴘ** 💕", ""]
    for item_id, (emoji, name, description, price) in SHOP_CACHE.items():
        lines.append(f"{emoji} **{name}** — `{price}` 🪙\n_{description}_\n")
    lines.append("_ᴜꜱᴇ `/buy shield`, `/buy lucky_charm`, or `/buy vip_badge`~_")
    await msg.reply("\n".join(lines))

@app.on_message(filters.command("buy"))
async def cmd_buy(_, msg: Message):
    try:
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

@app.on_message(filters.command(["inv", "inventory"]))
async def cmd_inventory(_, msg: Message):
    try:
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

@app.on_message(filters.command("use"))
async def cmd_use(_, msg: Message):
    item_id = msg.command[1].lower().replace("-", "_") if len(msg.command) > 1 else ""
    if item_id == "lucky_charm":
        return await msg.reply("🍀 **ʟᴜᴄᴋʏ ᴄʜᴀʀᴍ** ᴅᴀɪʟʏ ʀᴇᴡᴀʀᴅ ᴘᴇʀ ᴀᴜᴛᴏ-ᴇǫᴜɪᴩᴩᴇᴅ~")
    if item_id == "shield":
        return await msg.reply("🛡️ **ꜱʜɪᴇʟᴅ** ɪꜱ ᴀᴜᴛᴏ-ᴜꜱᴇᴅ ᴡʜᴇɴ ꜱᴏᴍᴇᴏɴᴇ ʀᴏʙꜱ ʏᴏᴜ~")
    await msg.reply(ff("use karne ke liye /use [shield|lucky_charm]"))

@app.on_message(filters.command("roulette"))
async def cmd_roulette(_, msg: Message):
    try:
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

@app.on_message(filters.command(["minerush", "mine"]))
async def cmd_minerush(_, msg: Message):
    try:
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
            return await cq.edit_message_text(f"⚡ **ᴄᴀꜱʜᴇᴅ ᴏᴜᴛ~**\n\n+`{win}` 🪙 🎉")
        index = int(parts[3])
        if not 0 <= index < 9:
            return await cq.answer("ɪɴᴠᴀʟɪᴅ ᴛɪʟᴇ~", show_alert=True)
        if index in session["revealed"]:
            return await cq.answer("ᴀʟʀᴇᴀᴅʏ ᴋʜᴏʟᴀ ʜᴀɪ~")
        if index in session["bombs"]:
            MINE_SESSIONS.pop(uid, None)
            await record_game(uid, "minerush", False)
            return await cq.edit_message_text(
                f"💥 **ʙᴏᴏᴍ!**\n\n-`{session['bet']}` 🪙 ʟᴏꜱᴛ~",
                reply_markup=mine_keyboard(uid, session["revealed"], over=True),
            )
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

@app.on_message(filters.command("quiz"))
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
    except Exception:
        traceback.print_exc()

def lottery_round_key():
    return datetime.utcnow().date().isoformat()

@app.on_message(filters.command("lottery"))
async def cmd_lottery(_, msg: Message):
    try:
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
            await app.send_message(chat_id, f"🎟️ **ʟᴏᴛᴛᴇʀʏ ᴅʀᴀᴡ~** 🎉\n\n🏆 ᴡɪɴɴᴇʀ: [ᴡɪɴɴᴇʀ](tg://user?id={winner})\n💎 ᴘᴏᴛ: `{pot}` 🪙")
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

@app.on_message(filters.command("warn") & filters.group)
async def cmd_warn(_, msg: Message):
    try:
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
                count = (await cur.fetchone())[0]
        if count >= 3:
            await app.ban_chat_member(msg.chat.id, target.id)
            await app.send_message(target.id, "🚫 ʀɪʀᴜʀᴜ ɴᴇ ᴛᴜᴍʜᴇ ɢʀᴏᴜᴩ ꜱᴇ ʙᴀɴ ᴋᴀʀ ᴅɪʏᴀ~ 🥺 ʙᴇ ɢᴏᴏᴅ ɴᴇxᴛ ᴛɪᴍᴇ~")
            await msg.reply(f"🚫 {mention(target)} **ʙᴀɴɴᴇᴅ** — `3/3` ᴡᴀʀɴꜱ")
        else:
            await msg.reply(f"⚠️ {mention(target)} **ᴡᴀʀɴᴇᴅ** — `{count}/3`\n_{reason}_")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("warnings") & filters.group)
async def cmd_warnings(_, msg: Message):
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
    await msg.reply(f"✅ {mention(target)} ᴋᴇ ᴡᴀʀɴɪɴɢꜱ ʀᴇꜱᴇᴛ~")

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
    await msg.reply(f"📝 **ɴᴏᴛᴇ ꜱᴀᴠᴇᴅ~** `{key}` ✅")

@app.on_message(filters.command("notes") & filters.group)
async def cmd_notes(_, msg: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT note_key FROM group_notes WHERE chat_id=? ORDER BY note_key", (msg.chat.id,)
        ) as cur:
            rows = await cur.fetchall()
    await msg.reply("📝 **ɢʀᴏᴜᴘ ɴᴏᴛᴇꜱ**\n\n" + (
        "\n".join(f"• `{row[0]}`" for row in rows) if rows else ff("koi notes nahi~")
    ))

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
    await msg.reply(f"🗑️ **ɴᴏᴛᴇ ᴅᴇʟᴇᴛᴇᴅ~** `{key}`")

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
        if await is_banned(msg.from_user.id):
            return
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        await msg.reply_chat_action(enums.ChatAction.TYPING)
        await increment_messages(msg.from_user.id)
        history = await get_history(msg.from_user.id)
        reply   = await riruru_reply(msg.text, history, await user_mood(msg.from_user.id))
        await save_message(msg.from_user.id, "user", msg.text)
        await save_message(msg.from_user.id, "assistant", reply)
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
        )
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
@app.on_message(filters.command("img"))
async def cmd_img(_, msg: Message):
    try:
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        if await is_banned(msg.from_user.id):
            return

        prompt = " ".join(msg.command[1:]).strip()
        if not prompt:
            return await msg.reply(ff("ek prompt de /img beautiful anime girl 🙄"))

        user = await get_user(msg.from_user.id)
        if not user or user["credits"] < 5:
            return await msg.reply(
                "ɢᴀʀɪʙ, ᴛᴇʀᴇ ᴩᴀꜱ 𝟻 ᴄʀᴇᴅɪᴛꜱ ɴᴀʜɪ ʜᴀɪ! 💀\n"
                f"_{ff('earn with /daily or /work')}_"
            )

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

        await update_credits(msg.from_user.id, -5)
        await status.delete()
        await msg.reply_photo(
            BytesIO(img_data),
            caption=(
                f"🎨 **{ff('AI Image')}**\n_{prompt}_\n\n"
                f"_-𝟻 {ff('credits')} · {ff('bal')}: {user['credits']-5}_"
            )
        )
    except Exception:
        traceback.print_exc()
        try:
            await msg.reply(ff("image generate nahi hui 💀 dobara try kar"))
        except Exception:
            pass

# ─── /credits /wallet ─────────────────────────────────────────────
@app.on_message(filters.command(["credits","wallet"]))
async def cmd_credits(_, msg: Message):
    try:
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

@app.on_message(filters.command("daily"))
async def cmd_daily(_, msg: Message):
    try:
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        cd = cooldown_left(user["daily_last"], 24)
        if cd:
            return await msg.reply(await cooldown_text("daily", cd))
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
        await msg.reply(
            f"🎁 **{ff('Daily Reward')}**\n\n"
            f"+`{reward}` {ff('coins')} credited! 💰\n"
            f"🔥 **ꜱᴛʀᴇᴀᴋ:** `{streak}` days"
            f"{' · 𝟹× ᴡᴇᴇᴋʟʏ ʙᴏɴᴜꜱ~' if streak >= 7 else ''}\n"
            f"_{ff('kal dobara aa')}_"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("work"))
async def cmd_work(_, msg: Message):
    try:
        await ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
        user = await get_user(msg.from_user.id)
        cd = cooldown_left(user["work_last"], 1)
        if cd:
            return await msg.reply(await cooldown_text("work", cd))
        desc, lo, hi = random.choice(WORK_JOBS)
        earned = random.randint(lo, hi)
        await update_coins(msg.from_user.id, earned)
        await set_cooldown(msg.from_user.id, "work_last")
        await msg.reply(
            f"💼 **{ff('Work Done')}**\n\ntu {desc}\n+`{earned}` {ff('coins')}! 💰"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("crime"))
async def cmd_crime(_, msg: Message):
    try:
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
            await msg.reply(f"😈 **{ff('Crime Win')}**\ntu {desc}\n+`{amount}` {ff('coins')}! 💰")
        else:
            await debit_coins(msg.from_user.id, amount)
            await msg.reply(f"🚓 **{ff('Crime Fail')}**\ntu {desc}\n-`{amount}` {ff('coins')} fine 😭")
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("rob"))
async def cmd_rob(_, msg: Message):
    try:
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
            return await msg.reply(
                f"🛡️ **ᴘʟᴏᴛ ᴛᴡɪꜱᴛ~** {mention(target)} ᴋᴇ ᴘᴀꜱꜱ ꜱʜɪᴇʟᴅ ᴛʜᴀ~\n"
                f"_ʀᴏʙʙᴇʀʏ ʙʟᴏᴄᴋᴇᴅ!_ ✨"
            )
        amount = random.randint(30, min(200, t_data["coins"]))
        if random.random() < 0.5:
            if not await transfer_coins(target.id, msg.from_user.id, amount):
                return await msg.reply(ff("robbery ke time coins change ho gaye~ phir try karo"))
            await msg.reply(
                f"💸 **{ff('Robbery!')}**\n"
                f"tu {mention(target)} se `{amount}` {ff('coins')} le gaya 😈"
            )
        else:
            fine = random.randint(20, 80)
            await debit_coins(msg.from_user.id, fine)
            await msg.reply(
                f"🚓 **{ff('Caught!')}**\n"
                f"{mention(target)} ne pakad liya 💀\n-`{fine}` {ff('coins')} fine!"
            )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("pay"))
async def cmd_pay(_, msg: Message):
    try:
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
        await msg.reply(
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
    @app.on_message(filters.command(cmd))
    async def _h(_, msg: Message):
        try:
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

@app.on_message(filters.command("ship"))
async def cmd_ship(_, msg: Message):
    try:
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
        await msg.reply(
            f"💕 **{ff('Ship Score')}**\n\n"
            f"{mention(msg.from_user)} + {mention(target)}\n\n"
            f"**{score}%** {bar}\n\n_{verdict}_"
        )
    except Exception:
        traceback.print_exc()

@app.on_message(filters.command("roll"))
async def cmd_roll(_, msg: Message):
    try:
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

@app.on_message(filters.command("trivia"))
async def cmd_trivia(_, msg: Message):
    try:
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
        if not is_owner(msg.from_user.id):
            return
        text = " ".join(msg.command[1:]) if msg.command else ""
        photo_id = msg.photo.file_id if msg.photo else None
        if not text and not photo_id:
            return await msg.reply(ff("kya broadcast karoon? 🙄"))
        caption = f"📢 **{ff('Broadcast')}**\n\n{text}" if text else f"📢 **{ff('Broadcast')}**"
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
        return m.status in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER)
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
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo jise ban karna hai"))
        await app.ban_chat_member(msg.chat.id, target.id)
        await msg.reply(f"🚫 {mention(target)} **{ff('banned')}** ✅")
    except Exception:
        await msg.reply(ff("ban nahi hua 💀 mujhe admin rights do"))

@app.on_message(filters.command("unban") & filters.group)
async def cmd_unban(_, msg: Message):
    try:
        if not await is_admin(msg.chat.id, msg.from_user.id):
            return await msg.reply(ff("tu admin nahi hai 💀"))
        target = msg.reply_to_message.from_user if msg.reply_to_message else None
        if not target:
            return await msg.reply(ff("reply karo jise unban karna hai"))
        await app.unban_chat_member(msg.chat.id, target.id)
        await msg.reply(f"✅ {mention(target)} **{ff('unbanned')}**")
    except Exception:
        traceback.print_exc()

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

async def group_ai_response(msg: Message, prompt: str):
    chat_id = msg.chat.id
    if chat_id in GROUP_AI_BUSY:
        return
    GROUP_AI_BUSY.add(chat_id)
    try:
        await msg.reply_chat_action(enums.ChatAction.TYPING)
        reply = await riruru_reply(
            prompt, await get_history(msg.from_user.id), await user_mood(msg.from_user.id)
        )
        await save_message(msg.from_user.id, "user", prompt)
        await save_message(msg.from_user.id, "assistant", reply)
        await msg.reply(reply)
    except Exception as exc:
        print(f"  Group AI error: {type(exc).__name__}: {str(exc)[:180]}")
    finally:
        GROUP_AI_BUSY.discard(chat_id)

@app.on_message(filters.group & filters.text)
async def group_msg(_, msg: Message):
    try:
        if not msg.from_user:
            return
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

        # Group AI can answer by mention/reply, or in throttled always mode.
        settings = await group_settings(chat_id)
        mentioned = bool(BOT_USERNAME and f"@{BOT_USERNAME.lower()}" in text_lo)
        replied = is_reply_to_bot(msg)
        ai_mode = settings.get("ai_mode") or ("mention" if settings.get("ai_enabled") else "off")
        should_answer = settings.get("ai_enabled") and (ai_mode == "always" or mentioned or replied)
        if should_answer and not text_lo.startswith("/"):
            clean_text = re.sub(rf"@{re.escape(BOT_USERNAME)}", "", msg.text, flags=re.IGNORECASE).strip()
            if clean_text:
                now = time.time()
                last_reply = GROUP_AI_LAST_REPLY.get(chat_id, 0)
                if ai_mode != "always" or now - last_reply >= GROUP_AI_REPLY_COOLDOWN:
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
                    permissions = getattr(enums, "ChatPermissions", None)
                    if permissions:
                        await app.restrict_chat_member(
                            chat_id, msg.from_user.id,
                            permissions=permissions(can_send_messages=False),
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
                    await msg.reply(
                        f"🚫 {mention(msg.from_user)} **{ff('banned')}**!\n"
                        f"_{ff('3 strikes = out bhai 💀')}_"
                    )
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

@app.on_message(filters.command("slots"))
async def cmd_slots(_, msg: Message):
    try:
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
    except Exception:
        traceback.print_exc()

# ─── /coinflip ────────────────────────────────────────────────────
@app.on_message(filters.command("coinflip"))
async def cmd_coinflip(_, msg: Message):
    try:
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
    except Exception:
        traceback.print_exc()

# ─── /diceduel ────────────────────────────────────────────────────
@app.on_message(filters.command("diceduel"))
async def cmd_diceduel(_, msg: Message):
    try:
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

@app.on_message(filters.command("blackjack"))
async def cmd_blackjack(_, msg: Message):
    try:
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
            return await msg.reply(text + f"\n\n🎉 **ʙʟᴀᴄᴋᴊᴀᴄᴋ~** +`{win}` 🪙")
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
                return await cq.edit_message_text(text)
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

@app.on_message(filters.command("bomb"))
async def cmd_bomb(_, msg: Message):
    try:
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

    await app.start()
    me = await app.get_me()
    BOT_USERNAME = me.username or ""
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
