#!/usr/bin/env python3
"""Gems / Powers / Premium. # NEW"""
import traceback
from datetime import datetime, timedelta

def register(app, bert=None):
    from src.compat import filters, enums
    import riruru as R
    from src.utils import ff, hcard, mention_html, flood_ok, err_wrong
    from src.db_extra import (get_wallet, is_premium, ensure_wallet, has_power,
                              _one, _all, _run)
    from src.media import cached_gif
    from riruru import send_mood

    async def card(msg, mood, title, rows):
        txt = hcard(title, rows)
        await send_mood(app, msg.chat.id, mood, txt)

    @app.on_message(filters.command("gems"))
    async def gems_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            await card(msg, 'greedy', 'ɢᴇᴍꜱ', [
                ('💎', 'ʙᴀʟᴀɴᴄᴇ', f'{w.get("gems",0)} (≈{(w.get("gems",0))*10000} ᴄᴏɪɴꜱ)'),
                ('📊', 'ᴅᴀɪʟʏ ᴜꜱᴇ', f'{w.get("gem_usage_today",0)}/50'),
                ('💱', 'ʀᴀᴛᴇ', '1 ɢᴇᴍ = 10,000 ᴄᴏɪɴꜱ (ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ ᴛᴏ ᴄᴏɴᴠᴇʀᴛ)'),
            ])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("convert"))
    async def convert_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/convert <gems>'), parse_mode=enums.ParseMode.HTML)
            try: amt = int(msg.command[1]); assert amt > 0
            except Exception:
                return await msg.reply(err_wrong('/convert <gems>'), parse_mode=enums.ParseMode.HTML)
            if not await is_premium(msg.from_user.id):
                return await msg.reply('ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ 💎 /premium', parse_mode=enums.ParseMode.HTML)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            used = w.get('gem_usage_today', 0) or 0
            if used + amt > 50:
                return await msg.reply(f'ᴅᴀɪʟʏ ʟɪᴍɪᴛ 50 💎 ({used}/50 ᴜꜱᴇᴅ)',
                                       parse_mode=enums.ParseMode.HTML)
            if (w.get('gems', 0) or 0) < amt:
                return await msg.reply('ɪᴛɴᴇ ɢᴇᴍꜱ ɴᴀʜɪ 💎', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET gems=gems-?, balance=balance+?, gem_usage_today=COALESCE(gem_usage_today,0)+? WHERE user_id=?",
                       (amt, amt * 10000, amt, msg.from_user.id))
            await card(msg, 'greedy', 'ᴄᴏɴᴠᴇʀᴛᴇᴅ', [
                ('💎', 'ɢᴇᴍꜱ', f'-{amt}'), ('💰', 'ᴄᴏɪɴꜱ', f'+{amt*10000}')])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("powers"))
    async def powers_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT id,name,gem_cost,duration_days FROM powers")
            txt = [f'✨ ╭── [ 🌸 {ff("ᴩᴏᴡᴇʀꜱ")} ]', '│', '']
            for pid, nm, cost, dur in rows:
                txt.append(f'├── ⚡ <b>{nm}</b> <code>{pid}</code> — {cost}💎/{dur}d')
            txt.append('└── ᴜꜱᴇ /pinfo &lt;id&gt; · /activate &lt;id&gt;')
            await send_mood(app, msg.chat.id, 'determined', '\n'.join(txt))
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("pinfo"))
    async def pinfo_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/pinfo <id>'), parse_mode=enums.ParseMode.HTML)
            r = await _one("SELECT * FROM powers WHERE id=?", (msg.command[1].lower(),))
            if not r:
                return await msg.reply('ɴᴏ ꜱᴜᴄʜ ᴩᴏᴡᴇʀ 🙈', parse_mode=enums.ParseMode.HTML)
            await card(msg, 'curious', 'ᴩᴏᴡᴇʀ ɪɴꜰᴏ', [
                ('⚡', 'ɴᴀᴍᴇ', r['name']), ('📝', 'ᴅᴇꜱᴄ', r['description']),
                ('💎', 'ᴄᴏꜱᴛ', f"{r['gem_cost']}"), ('⏳', 'ᴅᴜʀᴀᴛɪᴏɴ', f"{r['duration_days']}d")])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("activate"))
    async def activate_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/activate <id>'), parse_mode=enums.ParseMode.HTML)
            pid = msg.command[1].lower()
            r = await _one("SELECT * FROM powers WHERE id=?", (pid,))
            if not r:
                return await msg.reply('ɴᴏ ꜱᴜᴄʜ ᴩᴏᴡᴇʀ 🙈', parse_mode=enums.ParseMode.HTML)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get('gems', 0) or 0) < r['gem_cost']:
                return await msg.reply('ɢᴇᴍꜱ ᴋᴀᴍ ʜᴀɪ 💎', parse_mode=enums.ParseMode.HTML)
            exp = (datetime.utcnow() + timedelta(days=r['duration_days'])).isoformat()
            await _run("UPDATE wallet SET gems=gems-? WHERE user_id=?", (r['gem_cost'], msg.from_user.id))
            await _run("INSERT OR REPLACE INTO user_powers (user_id,power_id,activated_at,expires_at) VALUES (?,?,?,?)",
                       (msg.from_user.id, pid, datetime.utcnow().isoformat(), exp))
            await card(msg, 'cool', 'ᴩᴏᴡᴇʀ ᴏɴ', [
                ('⚡', 'ᴩᴏᴡᴇʀ', r['name']), ('⏳', 'ᴜɴᴛɪʟ', exp[:16])])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["mypowers", "mp"]))
    async def mypowers_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT power_id, expires_at FROM user_powers WHERE user_id=?", (msg.from_user.id,))
            live = []
            for pid, exp in rows:
                try:
                    left = datetime.fromisoformat(exp) - datetime.utcnow()
                    if left.total_seconds() > 0:
                        live.append((pid, f'{int(left.total_seconds()//86400)}d {int(left.total_seconds()%86400//3600)}h'))
                except Exception: pass
            if not live:
                return await msg.reply('ɴᴏ ᴀᴄᴛɪᴠᴇ ᴩᴏᴡᴇʀꜱ ⚡ /powers', parse_mode=enums.ParseMode.HTML)
            await card(msg, 'cheerful', 'ᴍʏ ᴩᴏᴡᴇʀꜱ', [('⚡', p, l) for p, l in live])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("ph"))
    async def ph_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await msg.reply(hcard('ᴩᴏᴡᴇʀ ʜᴇʟᴩ', [
                ('📜', '/powers', 'ʟɪꜱᴛ'), ('🔍', '/pinfo', 'ᴅᴇᴛᴀɪʟ'),
                ('⚡', '/activate', 'ᴏɴ'), ('🎒', '/mypowers', 'ᴍɪɴᴇ')]),
                parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("premium"))
    async def premium_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            from src.compat import InlineKeyboardMarkup, IKB as InlineKeyboardButton
            kb = InlineKeyboardMarkup([[InlineKeyboardButton('💎 ɢᴇᴛ ᴩʀᴇᴍɪᴜᴍ', url='https://t.me/RiruruBot?start=want_premium')]])
            await card(msg, 'excited', 'ᴩʀᴇᴍɪᴜᴍ', [
                ('🎁', 'ᴅᴀɪʟʏ', '$5000+200xᴩ (ᴠꜱ $2000+50)'), ('🔫', 'ʀᴏʙ', '$50ᴋ (ᴠꜱ $10ᴋ)'),
                ('⚔️', 'ᴋɪʟʟ', '$200-400 (ᴠꜱ $100-200)'), ('🛡️', 'ᴩʀᴏᴛᴇᴄᴛ', '2ᴅ ᴏᴩᴛɪᴏɴ'),
                ('🧾', 'ɢɪᴠᴇ ᴛᴀx', '5% (ᴠꜱ 10%)'), ('👁️', '/check', 'ꜱᴇᴇ ᴩʀᴏᴛᴇᴄᴛɪᴏɴ'),
                ('😀', '/setemoji', 'ᴄᴜꜱᴛᴏᴍ ᴇᴍᴏᴊɪ'), ('💱', 'ɢᴇᴍꜱ', 'ɢᴇᴍ→ᴄᴏɪɴ ᴄᴏɴᴠᴇʀᴛ')])
            try: await msg.reply('ᴛᴀᴩ ʙᴇʟᴏᴡ ᴛᴏ ʀᴇQᴜᴇꜱᴛ 👇', reply_markup=kb,
                                 parse_mode=enums.ParseMode.HTML)
            except Exception: pass
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("check"))
    async def check_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if not await is_premium(msg.from_user.id):
                return await msg.reply('ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ 💎', parse_mode=enums.ParseMode.HTML)
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t:
                return await msg.reply(err_wrong('/check (reply)'), parse_mode=enums.ParseMode.HTML)
            r = await _one("SELECT protected_until FROM protection WHERE user_id=?", (t.id,))
            await card(msg, 'curious', 'ᴄʜᴇᴄᴋ', [
                ('👤', 'ᴜꜱᴇʀ', mention_html(t.id, t.first_name)),
                ('🛡️', 'ᴩʀᴏᴛᴇᴄᴛᴇᴅ', (r or {}).get('protected_until', 'ᴏꜰꜰ') or 'ᴏꜰꜰ')])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("setemoji"))
    async def setemoji_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if not await is_premium(msg.from_user.id):
                return await msg.reply('ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ 💎', parse_mode=enums.ParseMode.HTML)
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/setemoji <emoji>'), parse_mode=enums.ParseMode.HTML)
            emo = msg.command[1]
            t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
            await _run("INSERT OR REPLACE INTO user_emoji (user_id,emoji,set_at) VALUES (?,?,?)",
                       (t.id, emo, datetime.utcnow().isoformat()))
            await msg.reply(f'ᴇᴍᴏᴊɪ ꜱᴇᴛ {emo} ꜰᴏʀ {mention_html(t.id, t.first_name)} ✅',
                            parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("tgems"))
    async def tgems_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t or len(msg.command) < 2:
                return await msg.reply(err_wrong('/tgems (reply) <gems>'), parse_mode=enums.ParseMode.HTML)
            try: amt = int(msg.command[-1]); assert amt > 0
            except Exception:
                return await msg.reply(err_wrong('/tgems (reply) <gems>'), parse_mode=enums.ParseMode.HTML)
            if await has_power(msg.from_user.id, 'ghost'):
                pass
            await ensure_wallet(msg.from_user.id); await ensure_wallet(t.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get('gems', 0) or 0) < amt:
                return await msg.reply('ɢᴇᴍꜱ ᴋᴀᴍ ʜᴀɪ 💎', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET gems=gems-? WHERE user_id=?", (amt, msg.from_user.id))
            await _run("UPDATE wallet SET gems=gems+? WHERE user_id=?", (amt, t.id))
            await card(msg, 'love', 'ɢᴇᴍꜱ ꜱᴇɴᴛ', [
                ('💎', 'ᴛᴏ', mention_html(t.id, t.first_name)), ('💎', 'ᴀᴍᴏᴜɴᴛ', f'{amt}')])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["bank", "interest"]))
    async def bank_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            from src.db_extra import apply_bank_interest as _abi
            gain = await _abi(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            rate = '4%' if await has_power(msg.from_user.id, 'banker') else '2%'
            await card(msg, 'tears_joy', 'ʙᴀɴᴋ', [
                ('🏦', 'ʙᴀʟᴀɴᴄᴇ', f'{w.get("bank",0)}'), ('📈', 'ʀᴀᴛᴇ', f'{rate}/ᴅᴀʏ'),
                ('✨', 'ᴄᴏʟʟᴇᴄᴛᴇᴅ', f'+{gain}')])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["gemmine", "minigem"]))
    async def mine_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await ensure_wallet(msg.from_user.id)
            # 1/day via gem_usage_reset guard reuse: use last_interest? use separate check in wallet
            w = await get_wallet(msg.from_user.id)
            today = datetime.utcnow().date().isoformat()
            if (w.get('gem_usage_reset') or '') == f'mine:{today}':
                return await msg.reply('ᴀʟʀᴇᴀᴅʏ ᴍɪɴᴇᴅ ᴛᴏᴅᴀʏ ⛏️', parse_mode=enums.ParseMode.HTML)
            g = __import__('random').randint(0, 2)
            await _run("UPDATE wallet SET gems=gems+?, gem_usage_reset=? WHERE user_id=?",
                       (g, f'mine:{today}', msg.from_user.id))
            await card(msg, 'greedy' if g > 0 else 'pout', 'ɢᴇᴍ ᴍɪɴᴇ', [('⛏️', 'ꜰᴏᴜɴᴅ', f'{g} 💎')])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("mystery"))
    async def mystery_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get('balance') or 0) < 1000:
                return await msg.reply('ɴᴇᴇᴅ 1000 ᴄᴏɪɴꜱ 🎁', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET balance=balance-1000 WHERE user_id=?", (msg.from_user.id,))
            r = __import__('random').choice([('coins', 1500), ('coins', 500), ('gems', 1), ('xp', 100)])
            if r[0] == 'coins':
                await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (r[1], msg.from_user.id))
            elif r[0] == 'gems':
                await _run("UPDATE wallet SET gems=gems+? WHERE user_id=?", (r[1], msg.from_user.id))
            else:
                from src.db_extra import add_xp as _axp
                await _axp(msg.from_user.id, r[1])
            await card(msg, 'surprised', 'ᴍʏꜱᴛᴇʀʏ ʙᴏx', [('🎁', 'ʀᴇᴡᴀʀᴅ', f'{r[1]} {r[0]}')])
        except Exception: traceback.print_exc()
