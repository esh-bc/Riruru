#!/usr/bin/env python3
"""Economy: kill/revive/protect/give/bal/wallet/pfp/leaderboards/open/claim. # NEW
HTML + ff() + tree cards + Kittygram styles. Flood-safe, economy-gated.
"""
import asyncio
import random
import traceback
from datetime import datetime, timedelta

_KILL_CD: dict = {}
_ROB2_CD: dict = {}

def _cd_ok(d: dict, uid: int, secs: int) -> int:
    now = __import__("time").time()
    last = d.get(uid, 0)
    left = int(secs - (now - last))
    if left > 0:
        return left
    d[uid] = now
    return 0


def register(app, bert=None):
    from src.compat import filters, enums
    from src.compat import InlineKeyboardMarkup
    # late imports: riruru globals already defined when this is imported at bottom
    import riruru as R
    from src.utils import ff, hcard, mention_html, flood_ok, err_wrong, err_cool, medal
    from src.db_extra import (get_wallet, get_xp, add_xp, is_premium, is_protected,
                              has_power, economy_enabled, apply_bank_interest,
                              ensure_wallet, ensure_xp, _one, _all, _run)
    from src.media import cached_gif
    from riruru import send_mood

    async def _eco_gate(msg) -> bool:
        try:
            if msg.chat and msg.chat.id < 0:
                if not await economy_enabled(msg.chat.id):
                    await msg.reply(f'ᴇᴄᴏɴᴏᴍʏ ɪꜱ ᴄʟᴏꜱᴇᴅ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴩ 🔒')
                    return False
        except Exception:
            pass
        return True

    async def _reply_card(msg, gif_action, title, rows, kb=None):
        gif = await cached_gif(gif_action)
        txt = hcard(title, rows)
        try:
            if gif:
                return await msg.reply_animation(gif, caption=txt,
                    parse_mode=enums.ParseMode.HTML, reply_markup=kb)
        except Exception:
            pass
        return await msg.reply(txt, parse_mode=enums.ParseMode.HTML, reply_markup=kb)

    # /kill <reply> # NEW
    @app.on_message(filters.command("kill"))
    async def kill_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if not await _eco_gate(msg):
                return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t:
                return await send_mood(app, msg.chat.id, 'confused',
                    err_wrong('/kill (reply to user)'), parse_mode=enums.ParseMode.HTML)
            if t.id == msg.from_user.id:
                return await send_mood(app, msg.chat.id, 'confused',
                    'ꜱᴇʟꜰ-ᴋɪʟʟ? ʙᴀᴋᴀ~ 🙈', parse_mode=enums.ParseMode.HTML)
            if t.is_bot:
                return await send_mood(app, msg.chat.id, 'dead',
                    'ʙᴏᴛꜱ ᴀʀᴇ ɪᴍᴍᴏʀᴛᴀʟ 💀', parse_mode=enums.ParseMode.HTML)
            left = _cd_ok(_KILL_CD, msg.from_user.id, 3600)
            if left:
                return await send_mood(app, msg.chat.id, 'sleepy',
                    err_cool(mins=max(1, left // 60)), parse_mode=enums.ParseMode.HTML)
            # Check if victim is dead
            await ensure_wallet(t.id)
            w_victim = await get_wallet(t.id)
            if w_victim.get("is_dead"):
                return await send_mood(app, msg.chat.id, 'dead',
                    f'💀 {mention_html(t.id, t.first_name)} ɪꜱ ᴀʟʀᴇᴀᴅʏ ᴅᴇᴀᴅ!\nᴜꜱᴇ /ʀᴇᴠɪᴠᴇ ᴛᴏ ʙʀɪɴɢ ᴛʜᴇᴍ ʙᴀᴄᴋ',
                    parse_mode=enums.ParseMode.HTML)
            if await is_protected(t.id) or await has_power(t.id, 'ghost'):
                return await send_mood(app, msg.chat.id, 'sweating',
                    'ᴜꜱᴇʀ ɪꜱ ᴘʀᴏᴛᴇᴄᴛᴇᴅ 🛡️', parse_mode=enums.ParseMode.HTML)
            prem = await is_premium(msg.from_user.id)
            coins = random.randint(200, 400) if prem else random.randint(100, 200)
            xp = random.randint(10, 20) if prem else random.randint(0, 10)
            if await has_power(msg.from_user.id, 'shield'):
                coins *= 2
                xp *= 2
            await ensure_wallet(msg.from_user.id)
            await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?",
                       (coins, msg.from_user.id))
            # Mark victim as dead
            await _run("UPDATE wallet SET is_dead=1 WHERE user_id=?", (t.id,))
            await ensure_xp(msg.from_user.id)
            _, lvl = await add_xp(msg.from_user.id, xp)
            await _run("UPDATE user_xp SET total_kills=total_kills+1, daily_kills=daily_kills+1 WHERE user_id=?",
                       (msg.from_user.id,))
            await _run("INSERT INTO kills (killer_id,victim_id,coins,xp,timestamp) VALUES (?,?,?,?,?)",
                       (msg.from_user.id, t.id, coins, xp, datetime.utcnow().isoformat()))
            tot = await _one("SELECT total_kills FROM user_xp WHERE user_id=?", (msg.from_user.id,))
            await send_mood(app, msg.chat.id, 'wink', hcard('ᴋɪʟʟ ʀᴇᴘᴏʀᴛ', [
                ('🗡️', 'ᴋɪʟʟᴇʀ', mention_html(msg.from_user.id, msg.from_user.first_name)),
                ('💀', 'ᴠɪᴄᴛɪᴍ', mention_html(t.id, t.first_name)),
                ('💰', 'ʀᴇᴡᴀʀᴅ', f'${coins}'),
                ('⭐', 'xᴩ ɢᴀɪɴᴇᴅ', f'{xp} (ʟᴠʟ {lvl})'),
                ('🔥', 'ᴛᴏᴛᴀʟ ᴋɪʟʟꜱ', f'{(tot or {}).get("total_kills", 1)}'),
                ('⚰️', 'ꜱᴛᴀᴛᴜꜱ', f'{mention_html(t.id, t.first_name)} ɪꜱ ᴅᴇᴀᴅ 💀'),
            ]))
        except Exception:
            traceback.print_exc()

    # /revive # NEW
    @app.on_message(filters.command("revive"))
    async def revive_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if not await _eco_gate(msg):
                return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get("balance") or 0) < 500:
                return await send_mood(app, msg.chat.id, 'crying',
                    'ɴᴇᴇᴅ 500 ᴄᴏɪɴꜱ ᴛᴏ ʀᴇᴠɪᴠᴇ 💀', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET balance=balance-500 WHERE user_id=?",
                       (msg.from_user.id,))
            # Clear dead status
            await _run("UPDATE wallet SET is_dead=0 WHERE user_id=?", (t.id,))
            await send_mood(app, msg.chat.id, 'cheerful', hcard('ʀᴇᴠɪᴠᴇᴅ', [
                ('💚', 'ᴜꜱᴇʀ', mention_html(t.id, t.first_name)),
                ('💰', 'ᴄᴏꜱᴛ', '500 ᴄᴏɪɴꜱ'),
                ('✨', 'ꜱᴛᴀᴛᴜꜱ', 'ᴀʟɪᴠᴇ ᴀɢᴀɪɴ~'),
            ]))
        except Exception:
            traceback.print_exc()

    # /protect 1d|2d # NEW
    @app.on_message(filters.command("protect"))
    async def protect_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if not await _eco_gate(msg):
                return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            arg = (msg.command[1].lower() if len(msg.command) > 1 else '1d')
            prem = await is_premium(msg.from_user.id)
            if arg not in ('1d', '2d'):
                return await send_mood(app, msg.chat.id, 'confused',
                    err_wrong('/protect 1d  (premium: 1d/2d)'), parse_mode=enums.ParseMode.HTML)
            if arg == '2d' and not prem:
                return await send_mood(app, msg.chat.id, 'annoyed',
                    '2ᴅ ɪꜱ ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ 💎 ᴜꜱᴇ /premium', parse_mode=enums.ParseMode.HTML)
            cost = 3000 if arg == '2d' else 2000
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get("balance") or 0) < cost:
                return await send_mood(app, msg.chat.id, 'crying',
                    f'ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ 💀', parse_mode=enums.ParseMode.HTML)
            days = 2 if arg == '2d' else 1
            until = (datetime.utcnow() + timedelta(days=days)).isoformat()
            await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?",
                       (cost, msg.from_user.id))
            await _run("INSERT OR REPLACE INTO protection (user_id,protected_until) VALUES (?,?)",
                       (msg.from_user.id, until))
            await send_mood(app, msg.chat.id, 'determined', hcard('ᴩʀᴏᴛᴇᴄᴛɪᴏɴ ᴏɴ', [
                ('🛡️', 'ᴅᴜʀᴀᴛɪᴏɴ', arg),
                ('💰', 'ᴄᴏꜱᴛ', f'{cost}'),
                ('⏳', 'ᴜɴᴛɪʟ', until[:16]),
            ]))
        except Exception:
            traceback.print_exc()

    # /give <reply> <amount> (taxed, new — /pay legacy stays) # NEW
    @app.on_message(filters.command("give"))
    async def give_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if not await _eco_gate(msg):
                return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t or len(msg.command) < 2:
                return await send_mood(app, msg.chat.id, 'confused',
                    err_wrong('/give (reply) <amount>'), parse_mode=enums.ParseMode.HTML)
            try:
                amt = int(msg.command[-1]); assert amt >= 100
            except Exception:
                return await send_mood(app, msg.chat.id, 'annoyed',
                    'ᴍɪɴ 100 ᴄᴏɪɴꜱ 💀', parse_mode=enums.ParseMode.HTML)
            prem = await is_premium(msg.from_user.id)
            tax = int(amt * (0.05 if prem else 0.10))
            net = amt - tax
            await ensure_wallet(msg.from_user.id)
            await ensure_wallet(t.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get("balance") or 0) < amt:
                return await send_mood(app, msg.chat.id, 'crying',
                    'ɪᴛɴᴇ ᴄᴏɪɴꜱ ɴᴀʜɪ ʜᴀɪ 💀', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?", (amt, msg.from_user.id))
            await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (net, t.id))
            await send_mood(app, msg.chat.id, 'love', hcard('ɢɪꜰᴛ ꜱᴇɴᴛ', [
                ('🎁', 'ᴛᴏ', mention_html(t.id, t.first_name)),
                ('💰', 'ᴀᴍᴏᴜɴᴛ', f'{amt}'),
                ('🧾', 'ᴛᴀx', f'{tax} ({5 if prem else 10}%)'),
                ('✨', 'ʀᴇᴄᴇɪᴠᴇᴅ', f'{net}'),
            ]))
        except Exception:
            traceback.print_exc()

    # /bal /balance # NEW
    @app.on_message(filters.command(["bal", "balance"]))
    async def bal_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
            await R.ensure_user(t.id, t.username, t.first_name)
            gain = await apply_bank_interest(t.id)
            w = await get_wallet(t.id)
            x = await get_xp(t.id)
            prot = '🛡️ ᴏɴ' if await is_protected(t.id) else 'ᴏꜰꜰ'
            prem = '💎 ʏᴇꜱ' if await is_premium(t.id) else 'ɴᴏ'
            await send_mood(app, msg.chat.id, 'cheerful', hcard('ʙᴀʟᴀɴᴄᴇ', [
                ('👤', 'ᴜꜱᴇʀ', mention_html(t.id, t.first_name)),
                ('💰', 'ᴡᴀʟʟᴇᴛ', f'{w.get("balance", 0)}'),
                ('🏦', 'ʙᴀɴᴋ', f'{w.get("bank", 0)} (+{gain})'),
                ('💎', 'ɢᴇᴍꜱ', f'{w.get("gems", 0)}'),
                ('⭐', 'xᴩ/ʟᴠʟ', f'{x.get("xp", 0)} / {x.get("level", 1)}'),
                ('🛡️', 'ᴩʀᴏᴛᴇᴄᴛ', prot),
                ('👑', 'ᴩʀᴇᴍɪᴜᴍ', prem),
            ]))
        except Exception:
            traceback.print_exc()

    # /wallet deposit|withdraw <amount> # NEW
    @app.on_message(filters.command("wallet"))
    async def wallet_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if not await _eco_gate(msg):
                return
            if len(msg.command) < 3:
                return await send_mood(app, msg.chat.id, 'confused',
                    err_wrong('/wallet deposit|withdraw <amount>'), parse_mode=enums.ParseMode.HTML)
            act, amt_s = msg.command[1].lower(), msg.command[2]
            try:
                amt = int(amt_s); assert amt > 0
            except Exception:
                return await send_mood(app, msg.chat.id, 'annoyed',
                    err_wrong('/wallet deposit|withdraw <amount>'), parse_mode=enums.ParseMode.HTML)
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            gain = await apply_bank_interest(msg.from_user.id)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if act == 'deposit':
                if (w.get("balance") or 0) < amt:
                    return await send_mood(app, msg.chat.id, 'crying',
                        'ᴡᴀʟʟᴇᴛ ᴍᴇɪɴ ɪᴛɴᴇ ɴᴀʜɪ 💀', parse_mode=enums.ParseMode.HTML)
                await _run("UPDATE wallet SET balance=balance-?, bank=bank+? WHERE user_id=?",
                           (amt, amt, msg.from_user.id))
            elif act == 'withdraw':
                if (w.get("bank") or 0) < amt:
                    return await send_mood(app, msg.chat.id, 'crying',
                        'ʙᴀɴᴋ ᴍᴇɪɴ ɪᴛɴᴇ ɴᴀʜɪ 💀', parse_mode=enums.ParseMode.HTML)
                await _run("UPDATE wallet SET bank=bank-?, balance=balance+? WHERE user_id=?",
                           (amt, amt, msg.from_user.id))
            else:
                return await send_mood(app, msg.chat.id, 'confused',
                    err_wrong('/wallet deposit|withdraw <amount>'), parse_mode=enums.ParseMode.HTML)
            w2 = await get_wallet(msg.from_user.id)
            mood = 'greedy' if act == 'deposit' else 'content'
            await send_mood(app, msg.chat.id, mood, hcard('ʙᴀɴᴋ ᴅᴏɴᴇ', [
                ('🏦', 'ᴀᴄᴛɪᴏɴ', act),
                ('💰', 'ᴀᴍᴏᴜɴᴛ', f'{amt}'),
                ('💼', 'ᴡᴀʟʟᴇᴛ', f'{w2.get("balance", 0)}'),
                ('🏦', 'ʙᴀɴᴋ', f'{w2.get("bank", 0)}'),
                ('📈', 'ɪɴᴛᴇʀᴇꜱᴛ', f'+{gain} (2%/4% daily)'),
            ]))
        except Exception:
            traceback.print_exc()

    # /pfp # NEW
    @app.on_message(filters.command("pfp"))
    async def pfp_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
            await R.ensure_user(t.id, t.username, t.first_name)
            await apply_bank_interest(t.id)
            w = await get_wallet(t.id); x = await get_xp(t.id)
            prot = '🛡️ ᴏɴ' if await is_protected(t.id) else 'ᴏꜰꜰ'
            prem = '💎' if await is_premium(t.id) else '—'
            emo = await _one("SELECT emoji FROM user_emoji WHERE user_id=?", (t.id,))
            txt = hcard('ᴩʀᴏꜰɪʟᴇ', [
                ('👤', 'ᴜꜱᴇʀ', mention_html(t.id, t.first_name)),
                ('💰', 'ᴡᴀʟʟᴇᴛ/ʙᴀɴᴋ', f'{w.get("balance",0)}/{w.get("bank",0)}'),
                ('💎', 'ɢᴇᴍꜱ', f'{w.get("gems",0)}'),
                ('⭐', 'xᴩ/ʟᴠʟ', f'{x.get("xp",0)}/{x.get("level",1)}'),
                ('⚔️', 'ᴋɪʟʟꜱ/ʀᴏʙꜱ', f'{x.get("daily_kills",0)}ᴅ/{x.get("daily_robs",0)}ᴅ'),
                ('🛡️', 'ᴩʀᴏᴛᴇᴄᴛ', prot),
                ('👑', 'ᴩʀᴇᴍ', prem),
                ('😀', 'ᴇᴍᴏᴊɪ', (emo or {}).get('emoji', '—')),
            ])
            try:
                ph = await asyncio.wait_for(app.get_profile_photos(t.id, limit=1), timeout=15)
                if ph and ph.photos:
                    fid = ph.photos[0][-1].file_id
                    return await msg.reply_photo(fid, caption=txt,
                        parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
            await msg.reply(txt, parse_mode=enums.ParseMode.HTML)
        except Exception:
            traceback.print_exc()

    # leaderboards # NEW
    @app.on_message(filters.command("toprich"))
    async def toprich_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            rows = await _all("SELECT user_id, balance+bank AS tot FROM wallet ORDER BY tot DESC LIMIT 10")
            lines = []
            for i, r in enumerate(rows):
                try:
                    u = await app.get_users(r[0])
                    nm = mention_html(u.id, u.first_name)
                except Exception:
                    nm = f'<code>{r[0]}</code>'
                lines.append(f'{medal(i)} {nm} — <b>{r[1]}</b>')
            txt = f'✨ ╭── [ 🌸 {ff("ᴛᴏᴩ ʀɪᴄʜ")} ]\n│\n\n' + ('\n'.join(f'├── {l}' for l in lines) if lines else '└── ɴᴏ ᴅᴀᴛᴀ ʏᴇᴛ~')
            await send_mood(app, msg.chat.id, 'greedy', txt)
        except Exception:
            traceback.print_exc()

    @app.on_message(filters.command("topkill"))
    async def topkill_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            rows = await _all("SELECT user_id, total_kills FROM user_xp ORDER BY total_kills DESC LIMIT 10")
            lines = []
            for i, r in enumerate(rows):
                try:
                    u = await app.get_users(r[0])
                    nm = mention_html(u.id, u.first_name)
                except Exception:
                    nm = f'<code>{r[0]}</code>'
                lines.append(f'{medal(i)} {nm} — <b>{r[1]}</b> ⚔️')
            txt = f'✨ ╭── [ 🌸 {ff("ᴛᴏᴩ ᴋɪʟʟ")} ]\n│\n\n' + ('\n'.join(f'├── {l}' for l in lines) if lines else '└── ɴᴏ ᴅᴀᴛᴀ ʏᴇᴛ~')
            await send_mood(app, msg.chat.id, 'furious', txt)
        except Exception:
            traceback.print_exc()

    # /open /close admin # NEW
    @app.on_message(filters.command(["open", "close"]))
    async def openclose_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if msg.chat.id > 0:
                return await msg.reply('ɢʀᴏᴜᴩ ᴏɴʟʏ 🙈', parse_mode=enums.ParseMode.HTML)
            m = await app.get_chat_member(msg.chat.id, msg.from_user.id)
            if m.status not in ('administrator', 'creator') and not R.is_owner(msg.from_user.id):
                return await msg.reply('ᴀᴅᴍɪɴ ᴏɴʟʏ 🔒', parse_mode=enums.ParseMode.HTML)
            on = msg.command[0] == 'open'
            await _run("INSERT OR IGNORE INTO group_economy (chat_id) VALUES (?)", (msg.chat.id,))
            await _run("UPDATE group_economy SET economy_enabled=? WHERE chat_id=?",
                       (1 if on else 0, msg.chat.id))
            await msg.reply(f'ᴇᴄᴏɴᴏᴍʏ {"ᴏᴩᴇɴᴇᴅ ✅" if on else "ᴄʟᴏꜱᴇᴅ 🔒"}',
                            parse_mode=enums.ParseMode.HTML)
        except Exception:
            traceback.print_exc()

    # /claim when added to group # NEW (POLISH: separate claimed flag, never clobbers economy_enabled)
    @app.on_message(filters.command("claim"))
    async def claim_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            if msg.chat.id > 0:
                return await msg.reply('ɢʀᴏᴜᴩ ᴍᴇɪɴ ᴜꜱᴇ ᴋᴀʀᴏ 🙈', parse_mode=enums.ParseMode.HTML)
            await _run("INSERT OR IGNORE INTO group_economy (chat_id) VALUES (?)", (msg.chat.id,))
            r = await _one("SELECT claimed FROM group_economy WHERE chat_id=?", (msg.chat.id,))
            if r and r.get("claimed"):
                return await msg.reply('ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ✅', parse_mode=enums.ParseMode.HTML)
            await ensure_wallet(msg.from_user.id)
            await _run("UPDATE wallet SET balance=balance+1000 WHERE user_id=?", (msg.from_user.id,))
            await _run("UPDATE group_economy SET claimed=1 WHERE chat_id=?", (msg.chat.id,))
            await send_mood(app, msg.chat.id, 'tears_joy', hcard('ᴛʜᴀɴᴋ ʏᴏᴜ', [
                ('🎉', 'ʙᴏɴᴜꜱ', '+1000 ᴄᴏɪɴꜱ'),
                ('🌸', 'ᴛᴏ', mention_html(msg.from_user.id, msg.from_user.first_name)),
            ]))
        except Exception:
            traceback.print_exc()
