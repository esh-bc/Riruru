#!/usr/bin/env python3
"""New games: hack / bluff / card. Benchmark: locks, timeouts, fees. # NEW"""
import asyncio
import random
import traceback
import time

HACK_GAMES: dict = {}   # msg_id -> state
BLUFF_GAMES: dict = {}  # chat_id -> state
CARD_DUELS: dict = {}   # challenger_id -> state

def register(app, bert=None):
    from src.compat import filters, enums, IKB as InlineKeyboardButton, InlineKeyboardMarkup
    import riruru as R
    from src.utils import ff, hcard, mention_html, flood_ok, err_wrong
    from src.db_extra import _run, ensure_wallet, get_wallet, games_enabled
    from src.media import cached_gif
    from riruru import send_mood

    async def gate(msg):
        if msg.chat.id < 0 and not await games_enabled(msg.chat.id):
            await msg.reply('ɢᴀᴍᴇꜱ ᴏꜰꜰ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴩ 🔒', parse_mode=enums.ParseMode.HTML)
            return False
        return True

    # /hack <amount> — 3x3 avoid firewalls # NEW
    @app.on_message(filters.command("hack"))
    async def hack_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if not await gate(msg): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/hack <amount>'), parse_mode=enums.ParseMode.HTML)
            try: bet = int(msg.command[1]); assert bet >= 10
            except Exception: return await msg.reply(err_wrong('/hack <amount min 10>'), parse_mode=enums.ParseMode.HTML)
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get('balance') or 0) < bet:
                return await msg.reply('ᴄᴏɪɴꜱ ᴋᴀᴍ ʜᴀɪ 💀', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?", (bet, msg.from_user.id))
            fw = set(random.sample(range(9), 3))
            kb = InlineKeyboardMarkup([[InlineKeyboardButton('🟩', callback_data=f'hack_{msg.from_user.id}_{bet}_{i}_{int(i in fw)}', style="primary") for i in range(r, r+3)] for r in (0, 3, 6)])
            m = await msg.reply(f'💻 <b>{ff("ʜᴀᴄᴋ")}</b> — pick tiles, avoid 🔴x3! 1/min ⏳', reply_markup=kb, parse_mode=enums.ParseMode.HTML)
            HACK_GAMES[m.id] = {'uid': msg.from_user.id, 'bet': bet, 'fw': fw, 'hits': set(), 'ts': time.time()}
            async def _to():
                await asyncio.sleep(300)
                if m.id in HACK_GAMES:
                    HACK_GAMES.pop(m.id, None)
                    try: await m.edit_text('⌛ ʜᴀᴄᴋ ᴇxᴩɪʀᴇᴅ — ʀᴇꜰᴜɴᴅᴇᴅ ✅')
                    except Exception: pass
                    await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (bet, msg.from_user.id))
            asyncio.create_task(_to())
        except Exception: traceback.print_exc()

    @app.on_callback_query(filters.regex(r'^hack_(\d+)_(\d+)_(\d+)_([01])$'))
    async def hack_cb(_, cq):
        try:
            uid, bet, idx, isfw = int(cq.data.split('_')[1]), int(cq.data.split('_')[2]), int(cq.data.split('_')[3]), cq.data.split('_')[4] == '1'
            if cq.from_user.id != uid:
                return await cq.answer('ᴛᴇʀɪ ɢᴀᴍᴇ ɴᴀʜɪ 🙈', show_alert=True)
            st = HACK_GAMES.get(cq.message.id)
            if not st: return await cq.answer('ᴇxᴩɪʀᴇᴅ~', show_alert=True)
            if isfw:
                HACK_GAMES.pop(cq.message.id, None)
                await cq.answer('🔴 ꜰɪʀᴇᴡᴀʟʟ!', show_alert=True)
                try: await cq.edit_message_text(f'🔴 <b>ꜰɪʀᴇᴡᴀʟʟ!</b> -{bet} 💀', parse_mode=enums.ParseMode.HTML)
                except Exception: pass
            else:
                st['hits'].add(idx)
                if len(st['hits']) >= 3:
                    HACK_GAMES.pop(cq.message.id, None)
                    await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (bet*2, uid))
                    await cq.answer(f'✅ +{bet*2} 💰', show_alert=True)
                    try: await cq.edit_message_text(f'✅ <b>ʜᴀᴄᴋᴇᴅ!</b> +{bet*2} 💰', parse_mode=enums.ParseMode.HTML)
                    except Exception: pass
                else:
                    await cq.answer(f'🟢 {len(st["hits"])}/3 safe')
                    await cq.edit_message_text(f'🟢 ꜱᴀꜰᴇ {len(st["hits"])}/3 — ᴄᴏɴᴛɪɴᴜᴇ~', parse_mode=enums.ParseMode.HTML)
        except Exception:
            try: await cq.answer()
            except Exception: pass

    # /bluff <amount> + /join + /call # NEW
    @app.on_message(filters.command("bluff"))
    async def bluff_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if not await gate(msg): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/bluff <amount>'), parse_mode=enums.ParseMode.HTML)
            try:
                bet = int(msg.command[1]); assert bet > 0
            except Exception:
                return await msg.reply(err_wrong('/bluff <amount>'), parse_mode=enums.ParseMode.HTML)
            if msg.chat.id in BLUFF_GAMES:
                return await msg.reply('ʙʟᴜꜰꜰ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ — /join', parse_mode=enums.ParseMode.HTML)
            BLUFF_GAMES[msg.chat.id] = {'pot': bet, 'players': [msg.from_user.id], 'round': 1}
            await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?", (bet, msg.from_user.id))
            await msg.reply(f'🃏 <b>ʙʟᴜꜰꜰ</b> started! Pot {bet}. Others: /join (4 rounds max)', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["join", "call"]))
    async def bluff_join_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            g = BLUFF_GAMES.get(msg.chat.id)
            if not g: return
            if msg.command[0] == 'join':
                if msg.from_user.id not in g['players']:
                    g['players'].append(msg.from_user.id)
                    await msg.reply(f'✅ {mention_html(msg.from_user.id, msg.from_user.first_name)} joined! Pot {g["pot"]}', parse_mode=enums.ParseMode.HTML)
            else:
                # /call — 50/50 resolve demo, winner takes pot minus 5%
                if len(g['players']) < 2: return await msg.reply('ɴᴇᴇᴅ 2+ ᴩʟᴀʏᴇʀꜱ 🃏', parse_mode=enums.ParseMode.HTML)
                winner = random.choice(g['players'])
                win = int(g['pot'] * len(g['players']) * 0.95)
                await ensure_wallet(winner)
                await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (win, winner))
                BLUFF_GAMES.pop(msg.chat.id, None)
                await send_mood(app, msg.chat.id, 'party', f'🏆 <b>ʙʟᴜꜰꜰ ᴏᴠᴇʀ!</b> Winner <code>{winner}</code> +{win} (5% fee) 🎉')
        except Exception: traceback.print_exc()

    # /card <amount> + /bet <amount> # NEW
    @app.on_message(filters.command("card"))
    async def card_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if not await gate(msg): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/card <amount>'), parse_mode=enums.ParseMode.HTML)
            try:
                bet = int(msg.command[1]); assert bet >= 10
            except Exception:
                return await msg.reply(err_wrong('/card <amount min 10>'), parse_mode=enums.ParseMode.HTML)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get('balance') or 0) < bet:
                return await msg.reply('ᴄᴏɪɴꜱ ᴋᴀᴍ ʜᴀɪ 💀', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?", (bet, msg.from_user.id))
            CARD_DUELS[msg.from_user.id] = {'bet': bet, 'card': random.randint(1, 10)}
            await msg.reply(f'🃏 Duel open for {bet}! Another user: reply <b>/bet {bet}</b>', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("bet"))
    async def bet_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            # support /bet <amount> gems (0.1 gem = 1000)
            is_gem = len(msg.command) > 2 and msg.command[2].lower().startswith('gem')
            if t and t.id in CARD_DUELS:
                d = CARD_DUELS.pop(t.id)
                bet = d['bet']
                await ensure_wallet(msg.from_user.id)
                w = await get_wallet(msg.from_user.id)
                if (w.get('balance') or 0) < bet:
                    CARD_DUELS[t.id] = d
                    return await msg.reply('ᴄᴏɪɴꜱ ᴋᴀᴍ ʜᴀɪ 💀', parse_mode=enums.ParseMode.HTML)
                await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?", (bet, msg.from_user.id))
                c1, c2 = d['card'], random.randint(1, 10)
                pot = int(bet * 2 * 0.95)
                if c1 == c2:
                    await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (bet, t.id))
                    await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (bet, msg.from_user.id))
                    return await send_mood(app, msg.chat.id, 'curious', f'🤝 Draw! {c1} vs {c2} — refunded')
                winner = t.id if c1 > c2 else msg.from_user.id
                loser = msg.from_user.id if c1 > c2 else t.id
                await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (pot, winner))
                await send_mood(app, msg.chat.id, 'cheerful', f'🃏 {c1} vs {c2} — Winner <code>{winner}</code> +{pot} (5% fee) 🏆')
                await send_mood(app, msg.chat.id, 'sad', f'🃏 {c1} vs {c2} — <code>{loser}</code> lost')
            elif is_gem:
                await msg.reply('💎 Gem bet: 0.1 gem = 1000 coins (demo — use /tgems to move gems first)', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()
