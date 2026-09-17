#!/usr/bin/env python3
"""Media layer for heavy image/video use. # NEW
Benchmark: shared session, multi-provider fallback, file_id cache in Turso.
Never store binary in DB — only file_id/URL + hash.
"""
import hashlib
import aiohttp

_http_session: aiohttp.ClientSession | None = None

async def get_http_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        conn = aiohttp.TCPConnector(limit=50, ttl_dns_cache=300)
        _http_session = aiohttp.ClientSession(connector=conn)
    return _http_session

# Action → tried endpoints in order (nekos.best slugs + waifu.pics slugs).
# Every interactive command resolves to a REAL gif — no dead actions.
ACTION_GIF_MAP = {
    "kiss": ["kiss", "peck"],
    "hug": ["hug", "cuddle"],
    "slap": ["slap", "smug"],
    "punch": ["kick", "slap", "yeet"],
    "bite": ["bite", "nom"],
    "murder": ["kill", "kick", "yeet"],
    "love": ["love", "hug", "kiss"],
    "look": ["stare", "poke", "wink"],
    "happy": ["happy", "smile", "dance"],
    "sad": ["cry", "pout", "sleep"],
}

# /start hero video: exact clip style the owner picked (mp4, ~20s), by file_id.
# Falls back to a dancing GIF, then to plain text. Never crashes.
START_VIDEO_FILE_ID = "BAACAgUAAxkDAAMSaqvSzExaJlInnLLHvPhrNB1x6XQAAtseAAL5oVlVOf_vQFYr_nw9BA"

_STATIC_FALLBACK = "https://c.tenor.com/7r7g8s0Q_wMAAAAd/anime-happy.gif"
_endpoint_cache: dict = {}
_url_cache: dict = {}  # action -> (url, timestamp); 10-min TTL skips API call per command
_URL_TTL = 600.0


async def _try_fetch(sess, url: str):
    try:
        async with sess.get(url, timeout=aiohttp.ClientTimeout(total=6)) as r:
            if r.status != 200:
                return None
            if "nekos.best" in url:
                d = await r.json()
                return (d.get("results") or [{}])[0].get("url")
            d = await r.json()
            return d.get("url")
    except Exception:
        return None


async def cached_gif(action: str) -> str | None:
    """Cached anime gif URL. Falls back across providers. No crash."""
    import time as _t
    a = (action or "happy").strip().lower().replace(" ", "-")
    hit = _url_cache.get(a)
    if hit and _t.time() - hit[1] < _URL_TTL:
        return hit[0]
    if a in _endpoint_cache:
        url = await _try_fetch(await get_http_session(), _endpoint_cache[a])
        if url:
            _url_cache[a] = (url, _t.time())
            return url
    sess = await get_http_session()
    cands = ACTION_GIF_MAP.get(a, [a])
    # 1) nekos.best slugs
    for slug in cands:
        url = await _try_fetch(sess, f"https://nekos.best/api/v2/{slug}")
        if url:
            _endpoint_cache[a] = f"https://nekos.best/api/v2/{slug}"
            _url_cache[a] = (url, _t.time())
            return url
    # 2) waifu.pics slugs
    for slug in cands:
        url = await _try_fetch(sess, f"https://api.waifu.pics/sfw/{slug}")
        if url:
            _endpoint_cache[a] = f"https://api.waifu.pics/sfw/{slug}"
            _url_cache[a] = (url, _t.time())
            return url
    # 3) static fallback — always returns something
    return _STATIC_FALLBACK

def prompt_hash(prompt: str, w: int = 1024, h: int = 1024) -> str:
    return hashlib.sha256(f"{prompt}|{w}x{h}".encode()).hexdigest()[:32]

async def db_get_file(hkey: str):
    try:
        from .db_extra import _one
        r = await _one("SELECT file_id, url FROM media_cache WHERE hkey=?", (hkey,))
        return r
    except Exception:
        return None

async def db_put_file(hkey: str, file_id: str, url: str, mtype: str):
    try:
        from .db_extra import _run
        await _run(
            "INSERT OR REPLACE INTO media_cache (hkey,file_id,url,mtype) VALUES (?,?,?,?)",
            (hkey, file_id, url, mtype),
        )
    except Exception:
        pass

async def send_gif_first(client, chat_id: int, action: str, caption: str,
                         parse_mode=None, reply_markup=None):
    """Best practice: send URL directly (Telegram fetches) — saves 80% bandwidth."""
    url = await cached_gif(action)
    try:
        if url:
            return await client.send_animation(
                chat_id, url, caption=caption,
                parse_mode=parse_mode, reply_markup=reply_markup,
            )
    except Exception:
        pass
    return await client.send_message(chat_id, caption, parse_mode=parse_mode,
                                     reply_markup=reply_markup)


async def send_video_botapi(chat_id, file_id, caption, keyboard=None,
                            parse_mode="HTML"):
    """Send a video via Bot API HTTPS (most reliable for file_id reuse).

    Plain send (no reply threading) for maximum compatibility.
    Returns the sent message_id or None. Never raises.
    """
    import json as _json
    import os as _os
    import urllib.parse as _up
    import urllib.request as _url

    tok = _os.environ.get("BOT_TOKEN", "")
    if not tok or not file_id:
        return None

    def _blocking_send():
        try:
            payload = {"chat_id": str(chat_id), "video": file_id,
                       "caption": caption or "", "parse_mode": parse_mode}
            if keyboard:
                payload["reply_markup"] = _json.dumps({"inline_keyboard": keyboard})
            data = _up.urlencode(payload).encode()
            req = _url.Request(f"https://api.telegram.org/bot{tok}/sendVideo",
                               data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            resp = _json.load(_url.urlopen(req, timeout=40))
            if resp.get("ok"):
                return (resp.get("result") or {}).get("message_id")
        except Exception:
            pass
        return None

    import asyncio as _aio
    return await _aio.to_thread(_blocking_send)
