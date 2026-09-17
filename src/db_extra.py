#!/usr/bin/env python3
"""Extra DB tables + helpers. Turso-safe, restart-safe. # NEW
All state in Turso so restart/hosting/token change never loses data.
Binary never stored — only file_id/URL/metadata.
"""
import os
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DB_PATH", "mochi.db")

NEW_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS wallet (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    bank INTEGER DEFAULT 0,
    gems INTEGER DEFAULT 0,
    last_interest TEXT,
    gem_usage_today INTEGER DEFAULT 0,
    gem_usage_reset TEXT,
    is_dead INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS protection (
    user_id INTEGER PRIMARY KEY,
    protected_until TEXT,
    is_premium INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS kills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    killer_id INTEGER,
    victim_id INTEGER,
    coins INTEGER,
    xp INTEGER,
    timestamp TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS robs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    robber_id INTEGER,
    victim_id INTEGER,
    amount INTEGER,
    timestamp TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS friends (
    user_id INTEGER,
    friend_id INTEGER,
    tag_name TEXT,
    added_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, friend_id)
);
CREATE TABLE IF NOT EXISTS intros (
    user_id INTEGER PRIMARY KEY,
    intro_text TEXT,
    set_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS coupons (
    code TEXT PRIMARY KEY,
    creator_id INTEGER,
    chat_id INTEGER,
    amount INTEGER,
    max_claims INTEGER DEFAULT 0,
    claims INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT
);
CREATE TABLE IF NOT EXISTS coupon_claims (
    code TEXT,
    user_id INTEGER,
    claimed_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (code, user_id)
);
CREATE TABLE IF NOT EXISTS account_recovery (
    user_id INTEGER PRIMARY KEY,
    password_hash TEXT,
    set_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS recovery_transfers (
    old_id INTEGER PRIMARY KEY,
    new_id INTEGER,
    transferred_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS powers (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    gem_cost INTEGER,
    duration_days INTEGER
);
CREATE TABLE IF NOT EXISTS user_powers (
    user_id INTEGER,
    power_id TEXT,
    activated_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    PRIMARY KEY (user_id, power_id)
);
CREATE TABLE IF NOT EXISTS user_sticker_packs (
    user_id INTEGER PRIMARY KEY,
    pack_name TEXT,
    pack_title TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS user_xp (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    total_kills INTEGER DEFAULT 0,
    total_robs INTEGER DEFAULT 0,
    daily_kills INTEGER DEFAULT 0,
    daily_robs INTEGER DEFAULT 0,
    last_reset TEXT
);
CREATE TABLE IF NOT EXISTS user_emoji (
    user_id INTEGER PRIMARY KEY,
    emoji TEXT,
    set_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS group_economy (
    chat_id INTEGER PRIMARY KEY,
    economy_enabled INTEGER DEFAULT 1,
    games_enabled INTEGER DEFAULT 1,
    welcome_media TEXT,
    welcome_text TEXT
);
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    chat_id INTEGER,
    reminder_text TEXT,
    remind_at TEXT,
    done INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS relationships (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER,
    relation_type TEXT,
    since TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS confessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER,
    to_id INTEGER,
    chat_id INTEGER,
    message TEXT,
    sent_at TEXT DEFAULT (datetime('now')),
    is_anonymous INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS streaks (
    user_id INTEGER PRIMARY KEY,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_daily TEXT
);
CREATE TABLE IF NOT EXISTS reputation (
    user_id INTEGER PRIMARY KEY,
    rep_points INTEGER DEFAULT 0,
    last_given TEXT,
    last_received TEXT
);
CREATE TABLE IF NOT EXISTS name_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    first_name TEXT,
    recorded_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS media_cache (
    hkey TEXT PRIMARY KEY,
    file_id TEXT,
    url TEXT,
    mtype TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_kills_killer ON kills(killer_id);
CREATE INDEX IF NOT EXISTS idx_robs_robber ON robs(robber_id);
CREATE INDEX IF NOT EXISTS idx_xp_level ON user_xp(xp DESC);
CREATE INDEX IF NOT EXISTS idx_rep_points ON reputation(rep_points DESC);
"""

SEED_POWERS = [
    ("shield", "ᴡᴀʀ ꜱʜɪᴇʟᴅ", "Doubles your kill/rob rewards", 5, 7),
    ("ghost", "ɢʜᴏꜱᴛ ᴍᴏᴅᴇ", "Makes you unrobbable even without protection", 8, 3),
    ("banker", "ɢᴏʟᴅ ʙᴀɴᴋᴇʀ", "Doubles bank interest rate to 4% daily", 3, 7),
]

async def init_extra_tables():
    """Create new tables + additive migrations. Never touches existing tables' data."""
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(NEW_TABLES_SQL)
        # users.is_premium did not exist in legacy schema — spec says it does. Add safely.
        for tbl, col, ddl in (
            ("users", "is_premium", "INTEGER DEFAULT 0"),
            ("wallet", "gem_usage_today", "INTEGER DEFAULT 0"),
            ("wallet", "gem_usage_reset", "TEXT"),
            ("wallet", "is_dead", "INTEGER DEFAULT 0"),
            ("group_economy", "claimed", "INTEGER DEFAULT 0"),
        ):
            try:
                async with db.execute(f"PRAGMA table_info({tbl})") as cur:
                    cols = {r[1] for r in await cur.fetchall()}
                if col not in cols:
                    await db.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {ddl}")
            except Exception:
                pass  # table may not exist yet on first run ordering
        await db.executemany(
            "INSERT OR IGNORE INTO powers (id,name,description,gem_cost,duration_days) VALUES (?,?,?,?,?)",
            SEED_POWERS,
        )
        # Migrate legacy users.coins -> wallet.balance once (keep users.coins as-is for compat)
        try:
            async with db.execute(
                "SELECT user_id, coins FROM users WHERE coins > 0"
            ) as cur:
                rows = await cur.fetchall()
            for uid, coins in rows:
                await db.execute(
                    "INSERT OR IGNORE INTO wallet (user_id,balance) VALUES (?,0)", (uid,)
                )
                async with db.execute(
                    "SELECT balance FROM wallet WHERE user_id=?", (uid,)
                ) as c2:
                    bal = (await c2.fetchone() or [0])[0]
                if (bal or 0) == 0 and coins:
                    await db.execute(
                        "UPDATE wallet SET balance=? WHERE user_id=?", (coins, uid)
                    )
        except Exception:
            pass
        await db.commit()

# ── Generic helpers (all Turso-safe via patched aiosqlite.connect) ──
async def _one(sql, args=()):
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, args) as cur:
            r = await cur.fetchone()
            return dict(r) if r else None

async def _all(sql, args=()):
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(sql, args) as cur:
            return await cur.fetchall()

async def _run(sql, args=()):
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, args)
        await db.commit()

async def ensure_wallet(uid: int):
    await _run("INSERT OR IGNORE INTO wallet (user_id) VALUES (?)", (uid,))

async def ensure_xp(uid: int):
    await _run("INSERT OR IGNORE INTO user_xp (user_id) VALUES (?)", (uid,))
    await _run("INSERT OR IGNORE INTO streaks (user_id) VALUES (?)", (uid,))
    await _run("INSERT OR IGNORE INTO reputation (user_id) VALUES (?)", (uid,))

async def get_wallet(uid: int):
    await ensure_wallet(uid)
    return await _one("SELECT * FROM wallet WHERE user_id=?", (uid,)) or {}

async def get_xp(uid: int):
    await ensure_xp(uid)
    return await _one("SELECT * FROM user_xp WHERE user_id=?", (uid,)) or {}

async def is_premium(uid: int) -> bool:
    try:
        r = await _one("SELECT is_premium FROM users WHERE user_id=?", (uid,))
        if r and r.get("is_premium"):
            return True
    except Exception:
        pass
    try:
        p = await _one("SELECT is_premium FROM protection WHERE user_id=?", (uid,))
        return bool(p and p.get("is_premium"))
    except Exception:
        return False

async def add_xp(uid: int, amount: int):
    await ensure_xp(uid)
    w = await get_xp(uid)
    xp = (w.get("xp") or 0) + max(0, int(amount))
    lvl = (w.get("level") or 1)
    # level curve: 100 * lvl^1.5
    import math
    while xp >= int(100 * (lvl ** 1.5)) + 100:
        lvl += 1
    await _run("UPDATE user_xp SET xp=?, level=? WHERE user_id=?", (xp, lvl, uid))
    return xp, lvl

async def is_protected(uid: int) -> bool:
    r = await _one("SELECT protected_until FROM protection WHERE user_id=?", (uid,))
    if not r or not r.get("protected_until"):
        return False
    try:
        return datetime.fromisoformat(r["protected_until"]) > datetime.utcnow()
    except Exception:
        return False

async def has_power(uid: int, pid: str) -> bool:
    r = await _one(
        "SELECT expires_at FROM user_powers WHERE user_id=? AND power_id=?", (uid, pid)
    )
    if not r:
        return False
    try:
        return datetime.fromisoformat(r["expires_at"]) > datetime.utcnow()
    except Exception:
        return False

async def economy_enabled(chat_id: int) -> bool:
    if not chat_id or chat_id > 0:
        return True  # DM always allowed
    r = await _one("SELECT economy_enabled FROM group_economy WHERE chat_id=?", (chat_id,))
    return bool(r.get("economy_enabled", 1)) if r else True

async def games_enabled(chat_id: int) -> bool:
    if not chat_id or chat_id > 0:
        return True
    r = await _one("SELECT games_enabled FROM group_economy WHERE chat_id=?", (chat_id,))
    return bool(r.get("games_enabled", 1)) if r else True

async def apply_bank_interest(uid: int):
    """2% daily (4% with banker power). Auto on each wallet access. Returns interest added."""
    w = await get_wallet(uid)
    bank = w.get("bank") or 0
    if bank <= 0:
        return 0
    last = w.get("last_interest")
    try:
        last_dt = datetime.fromisoformat(last) if last else None
    except Exception:
        last_dt = None
    if last_dt and (datetime.utcnow() - last_dt) < timedelta(hours=24):
        return 0
    rate = 0.04 if await has_power(uid, "banker") else 0.02
    gain = int(bank * rate)
    if gain > 0:
        await _run(
            "UPDATE wallet SET bank=bank+?, last_interest=? WHERE user_id=?",
            (gain, datetime.utcnow().isoformat(), uid),
        )
    else:
        await _run("UPDATE wallet SET last_interest=? WHERE user_id=?",
                   (datetime.utcnow().isoformat(), uid))
    return gain
