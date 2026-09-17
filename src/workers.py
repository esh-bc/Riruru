#!/usr/bin/env python3
"""Background workers: reminders / interest / daily reset. DB-driven, restart-safe. # NEW"""
import asyncio
import traceback
from datetime import datetime, timedelta

async def reminder_worker(app):
    from src.compat import HTML
    from src.db_extra import _all, _run
    while True:
        try:
            await asyncio.sleep(60)
            now = datetime.utcnow().isoformat()
            rows = await _all("SELECT id,user_id,chat_id,reminder_text FROM reminders WHERE done=0 AND remind_at<=?", (now,))
            for rid, uid, cid, txt in rows:
                try:
                    await app.send_message(cid, f'⏰ <a href="tg://user?id={uid}">Reminder</a>: {txt}',
                                           parse_mode=HTML)
                except Exception:
                    try: await app.send_message(uid, f'⏰ Reminder: {txt}')
                    except Exception: pass
                await _run("UPDATE reminders SET done=1 WHERE id=?", (rid,))
        except asyncio.CancelledError:
            break
        except Exception:
            traceback.print_exc()
            await asyncio.sleep(5)

async def interest_worker():
    from src.db_extra import _all, _run, has_power
    while True:
        try:
            await asyncio.sleep(3600)
            rows = await _all("SELECT user_id,bank,last_interest FROM wallet WHERE bank>0")
            now = datetime.utcnow()
            for uid, bank, last in rows:
                try:
                    ld = datetime.fromisoformat(last) if last else None
                except Exception:
                    ld = None
                if ld and (now - ld) < timedelta(hours=24):
                    continue
                rate = 0.04 if await has_power(uid, 'banker') else 0.02
                gain = int((bank or 0) * rate)
                if gain > 0:
                    await _run("UPDATE wallet SET bank=bank+?, last_interest=? WHERE user_id=?",
                               (gain, now.isoformat(), uid))
        except asyncio.CancelledError:
            break
        except Exception:
            traceback.print_exc()
            await asyncio.sleep(10)

async def daily_reset_worker():
    from src.db_extra import _run
    while True:
        try:
            now = datetime.utcnow()
            # next midnight IST = 18:30 UTC
            nxt = (now + timedelta(days=1)).replace(hour=18, minute=30, second=0, microsecond=0)
            if nxt <= now:
                nxt += timedelta(days=1)
            await asyncio.sleep(max(60, (nxt - now).total_seconds()))
            await _run("UPDATE user_xp SET daily_kills=0, daily_robs=0, last_reset=?", (datetime.utcnow().isoformat(),))
            await _run("UPDATE wallet SET gem_usage_today=0, gem_usage_reset=?", (datetime.utcnow().isoformat(),))
        except asyncio.CancelledError:
            break
        except Exception:
            traceback.print_exc()
            await asyncio.sleep(60)
