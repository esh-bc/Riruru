#!/usr/bin/env python3
"""Recovery / Friends / Coupons / Intros / Relationships / Reminders / Rep. # NEW"""
import hashlib
import traceback
from datetime import datetime

def register(app, bert=None):
    from src.compat import filters, enums
    import riruru as R
    from src.utils import ff, hcard, mention_html, flood_ok, err_wrong, parse_dur, medal
    from src.db_extra import _one, _all, _run, ensure_wallet, get_wallet, add_xp
    from src.media import cached_gif
    from riruru import send_mood

    async def card(msg, act, title, rows, mood=None):
        txt = hcard(title, rows)
        if mood:
            return await send_mood(app, msg.chat.id, mood, txt, reply_to_id=msg.id)
        gif = await cached_gif(act)
        try:
            if gif: return await msg.reply_animation(gif, caption=txt, parse_mode=enums.ParseMode.HTML)
        except Exception: pass
        return await msg.reply(txt, parse_mode=enums.ParseMode.HTML)

    # ── Recovery (DM only; mpass reset-only since sha256 one-way) ──
    @app.on_message(filters.command("setpass") & filters.private)
    async def setpass_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/setpass <password>'), parse_mode=enums.ParseMode.HTML)
            h = hashlib.sha256(msg.command[1].encode()).hexdigest()
            await _run("INSERT OR REPLACE INTO account_recovery (user_id,password_hash,set_at) VALUES (?,?,?)",
                       (msg.from_user.id, h, datetime.utcnow().isoformat()))
            await send_mood(app, msg.chat.id, 'serious', 'ᴩᴀꜱꜱᴡᴏʀᴅ ꜱᴇᴛ ꜱᴇᴄᴜʀᴇʟʏ 🔐', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("mpass") & filters.private)
    async def mpass_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await send_mood(app, msg.chat.id, 'suspicious', 'ꜱᴇᴄᴜʀɪᴛʏ: ᴩᴀꜱꜱᴡᴏʀᴅ ɪꜱ ʜᴀꜱʜᴇᴅ (ꜱʜ256) — ᴄᴀɴɴᴏᴛ ꜱʜᴏᴡ. ᴜꜱᴇ /cpass old new 🔐',
                            reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("cpass") & filters.private)
    async def cpass_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 3:
                return await msg.reply(err_wrong('/cpass <old> <new>'), parse_mode=enums.ParseMode.HTML)
            old_h = hashlib.sha256(msg.command[1].encode()).hexdigest()
            r = await _one("SELECT password_hash FROM account_recovery WHERE user_id=?", (msg.from_user.id,))
            if not r or r.get('password_hash') != old_h:
                return await msg.reply('ᴡʀᴏɴɢ ᴏʟᴅ ᴩᴀꜱꜱ 💀', parse_mode=enums.ParseMode.HTML)
            new_h = hashlib.sha256(msg.command[2].encode()).hexdigest()
            await _run("UPDATE account_recovery SET password_hash=?, set_at=? WHERE user_id=?",
                       (new_h, datetime.utcnow().isoformat(), msg.from_user.id))
            await send_mood(app, msg.chat.id, 'cheerful', 'ᴩᴀꜱꜱᴡᴏʀᴅ ᴜᴩᴅᴀᴛᴇᴅ ✅', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("transfer") & filters.private)
    async def transfer_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 3:
                return await msg.reply(err_wrong('/transfer <old_id> <password>'), parse_mode=enums.ParseMode.HTML)
            try: old_id = int(msg.command[1])
            except Exception:
                return await msg.reply(err_wrong('/transfer <old_id> <password>'), parse_mode=enums.ParseMode.HTML)
            pwd = msg.command[2]
            # deleted check via get_chat
            try:
                c = await app.get_chat(old_id)
                if c and not getattr(c, 'is_deleted', False):
                    # if get_users succeeds, still allow? spec: cannot if active
                    try:
                        await app.get_users(old_id)
                        return await msg.reply('ᴏʟᴅ ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ꜱᴛɪʟʟ ᴀᴄᴛɪᴠᴇ ❌', parse_mode=enums.ParseMode.HTML)
                    except Exception: pass
            except Exception:
                pass  # exception => likely deleted, continue
            r = await _one("SELECT password_hash FROM account_recovery WHERE user_id=?", (old_id,))
            if not r or r.get('password_hash') != hashlib.sha256(pwd.encode()).hexdigest():
                return await msg.reply('ᴡʀᴏɴɢ ᴩᴀꜱꜱᴡᴏʀᴅ 💀', parse_mode=enums.ParseMode.HTML)
            # copy data: wallet, xp, premium, powers, achievements
            ow = await _one("SELECT balance,bank,gems FROM wallet WHERE user_id=?", (old_id,)) or {}
            ox = await _one("SELECT xp,level,total_kills,total_robs FROM user_xp WHERE user_id=?", (old_id,)) or {}
            op = await _one("SELECT is_premium FROM users WHERE user_id=?", (old_id,)) or {}
            await _run("INSERT OR IGNORE INTO wallet (user_id) VALUES (?)", (msg.from_user.id,))
            await _run("UPDATE wallet SET balance=?, bank=?, gems=? WHERE user_id=?",
                       (ow.get('balance', 0), ow.get('bank', 0), ow.get('gems', 0), msg.from_user.id))
            await _run("INSERT OR IGNORE INTO user_xp (user_id) VALUES (?)", (msg.from_user.id,))
            await _run("UPDATE user_xp SET xp=?, level=?, total_kills=?, total_robs=? WHERE user_id=?",
                       (ox.get('xp', 0), ox.get('level', 1), ox.get('total_kills', 0), ox.get('total_robs', 0), msg.from_user.id))
            if op.get('is_premium'):
                try: await _run("UPDATE users SET is_premium=1 WHERE user_id=?", (msg.from_user.id,))
                except Exception: pass
            for prow in await _all("SELECT power_id,activated_at,expires_at FROM user_powers WHERE user_id=?", (old_id,)):
                await _run("INSERT OR REPLACE INTO user_powers VALUES (?,?,?,?)",
                           (msg.from_user.id, prow[0], prow[1], prow[2]))
            for arow in await _all("SELECT achievement_id FROM achievements WHERE user_id=?", (old_id,)):
                try: await _run("INSERT OR IGNORE INTO achievements (user_id,achievement_id) VALUES (?,?)",
                                (msg.from_user.id, arow[0]))
                except Exception: pass
            await _run("INSERT OR REPLACE INTO recovery_transfers (old_id,new_id,transferred_at) VALUES (?,?,?)",
                       (old_id, msg.from_user.id, datetime.utcnow().isoformat()))
            await send_mood(app, msg.chat.id, 'tears_joy', 'ᴛʀᴀɴꜱꜰᴇʀ ᴅᴏɴᴇ ✅ ᴀʟʟ ᴅᴀᴛᴀ ᴍᴏᴠᴇᴅ~ 🌸', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    # ── Friends ──
    @app.on_message(filters.command("addf"))
    async def addf_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t or len(msg.command) < 2:
                return await msg.reply(err_wrong('/addf <tag> (reply)'), parse_mode=enums.ParseMode.HTML)
            tag = msg.command[1].lower()
            await _run("INSERT OR REPLACE INTO friends (user_id,friend_id,tag_name,added_at) VALUES (?,?,?,?)",
                       (msg.from_user.id, t.id, tag, datetime.utcnow().isoformat()))
            await send_mood(app, msg.chat.id, 'tears_joy', f'ꜰʀɪᴇɴᴅ ᴀᴅᴅᴇᴅ ᴀꜱ [{tag}] 💚', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    async def _friends_map(uid):
        return {r[0]: r[1] for r in await _all("SELECT tag_name,friend_id FROM friends WHERE user_id=?", (uid,))}

    @app.on_message(filters.command(["tag", "t"]))
    async def tag_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/tag <tag1> <tag2> | /t all'), parse_mode=enums.ParseMode.HTML)
            m = await _friends_map(msg.from_user.id)
            if not m:
                return await msg.reply('ɴᴏ ꜰʀɪᴇɴᴅꜱ ʏᴇᴛ — /addf first 💚', parse_mode=enums.ParseMode.HTML)
            args = [a.lower() for a in msg.command[1:]]
            ids = list(m.values()) if args == ['all'] else [m[a] for a in args if a in m]
            if not ids:
                return await msg.reply('ɴᴏ ᴍᴀᴛᴄʜɪɴɢ ᴛᴀɢꜱ 🙈', parse_mode=enums.ParseMode.HTML)
            outs = []
            for fid in ids[:20]:
                try:
                    u = await app.get_users(fid)
                    outs.append(mention_html(u.id, '@' + (u.username or u.first_name)))
                except Exception:
                    outs.append(f'<code>{fid}</code>')
            await msg.reply(' '.join(outs), parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("ctag"))
    async def ctag_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 3:
                return await msg.reply(err_wrong('/ctag <old> <new>'), parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE friends SET tag_name=? WHERE user_id=? AND tag_name=?",
                       (msg.command[2].lower(), msg.from_user.id, msg.command[1].lower()))
            await msg.reply('ᴛᴀɢ ᴜᴩᴅᴀᴛᴇᴅ ✅', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("delf"))
    async def delf_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/delf <tag>'), parse_mode=enums.ParseMode.HTML)
            await _run("DELETE FROM friends WHERE user_id=? AND tag_name=?",
                       (msg.from_user.id, msg.command[1].lower()))
            await msg.reply('ꜰʀɪᴇɴᴅ ʀᴇᴍᴏᴠᴇᴅ 🗑️', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("allf"))
    async def allf_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT tag_name,friend_id FROM friends WHERE user_id=?", (msg.from_user.id,))
            if not rows:
                return await msg.reply('ɴᴏ ꜰʀɪᴇɴᴅꜱ ʏᴇᴛ 💚', parse_mode=enums.ParseMode.HTML)
            lines = []
            for tag, fid in rows:
                try:
                    u = await app.get_users(fid)
                    nm = '@' + (u.username or u.first_name)
                except Exception: nm = str(fid)
                lines.append(f'{tag} → {nm}')
            await send_mood(app, msg.chat.id, 'cheerful', hcard('ᴍʏ ꜰʀɪᴇɴᴅꜱ', [('💚', f'f{i+1}', l) for i, l in enumerate(lines[:30])]),
                            reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("friend"))
    async def friend_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT COUNT(*) FROM friends WHERE user_id=?", (msg.from_user.id,))
            await msg.reply(f'👥 ꜰʀɪᴇɴᴅꜱ: <b>{rows[0][0] if rows else 0}</b>', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("friends"))
    async def friends_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await msg.reply(hcard('ꜰʀɪᴇɴᴅ ᴄᴍᴅꜱ', [
                ('➕', '/addf', 'ᴀᴅᴅ'), ('🏷️', '/tag', 'ᴍᴇɴᴛɪᴏɴ'),
                ('✏️', '/ctag', 'ʀᴇɴᴀᴍᴇ'), ('🗑️', '/delf', 'ᴅᴇʟ'),
                ('📜', '/allf', 'ʟɪꜱᴛ')]), parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    # ── Coupons ──
    @app.on_message(filters.command("create_coupon"))
    async def create_coupon_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if msg.chat.id > 0:
                return await msg.reply('ɢʀᴏᴜᴩ ᴏɴʟʏ 🙈', parse_mode=enums.ParseMode.HTML)
            if len(msg.command) < 4:
                return await msg.reply(err_wrong('/create_coupon <code> <amt> <max>'), parse_mode=enums.ParseMode.HTML)
            from src.db_extra import is_premium as _prem
            if not await _prem(msg.from_user.id):
                return await msg.reply('ᴩʀᴇᴍɪᴜᴍ ᴏɴʟʏ 💎', parse_mode=enums.ParseMode.HTML)
            m = await app.get_chat_member(msg.chat.id, msg.from_user.id)
            if m.status not in ('administrator', 'creator'):
                return await msg.reply('ᴀᴅᴍɪɴ ᴏɴʟʏ 🔒', parse_mode=enums.ParseMode.HTML)
            try:
                code, amt, mx = msg.command[1].upper(), int(msg.command[2]), int(msg.command[3])
                assert amt > 0 and mx > 0
            except Exception:
                return await msg.reply(err_wrong('/create_coupon <code> <amt> <max>'), parse_mode=enums.ParseMode.HTML)
            ex = await _one("SELECT code FROM coupons WHERE chat_id=?", (msg.chat.id,))
            if ex:
                return await msg.reply('ᴏɴᴇ ᴄᴏᴜᴩᴏɴ ᴩᴇʀ ɢʀᴏᴜᴩ ⚠️', parse_mode=enums.ParseMode.HTML)
            await ensure_wallet(msg.from_user.id)
            w = await get_wallet(msg.from_user.id)
            if (w.get('balance') or 0) < amt * mx:
                return await msg.reply('ʙᴀʟᴀɴᴄᴇ ᴋᴀᴍ ʜᴀɪ 💀', parse_mode=enums.ParseMode.HTML)
            await _run("UPDATE wallet SET balance=balance-? WHERE user_id=?", (amt * mx, msg.from_user.id))
            await _run("INSERT INTO coupons (code,creator_id,chat_id,amount,max_claims) VALUES (?,?,?,?,?)",
                       (code, msg.from_user.id, msg.chat.id, amt, mx))
            await card(msg, 'happy', 'ᴄᴏᴜᴩᴏɴ ᴄʀᴇᴀᴛᴇᴅ', [('🎟️', 'ᴄᴏᴅᴇ', f'<code>{code}</code>'),
                                                        ('💰', 'ᴀᴍᴛ', f'{amt} x{mx}')], mood='cool')
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("del_coupon"))
    async def del_coupon_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/del_coupon <code>'), parse_mode=enums.ParseMode.HTML)
            code = msg.command[1].upper()
            r = await _one("SELECT * FROM coupons WHERE code=?", (code,))
            if not r: return await msg.reply('ɴᴏ ꜱᴜᴄʜ ᴄᴏᴜᴩᴏɴ 🙈', parse_mode=enums.ParseMode.HTML)
            left = (r['max_claims'] - r['claims']) * r['amount']
            if left > 0:
                await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (left, msg.from_user.id))
            await _run("DELETE FROM coupons WHERE code=?", (code,))
            await msg.reply(f'ᴄᴏᴜᴩᴏɴ ᴅᴇʟᴇᴛᴇᴅ, ʀᴇꜰᴜɴᴅᴇᴅ {left} ✅', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("coupon"))
    async def coupon_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/coupon <code>'), parse_mode=enums.ParseMode.HTML)
            code = msg.command[1].upper()
            r = await _one("SELECT * FROM coupons WHERE code=?", (code,))
            if not r: return await msg.reply('ɪɴᴠᴀʟɪᴅ ᴄᴏᴜᴩᴏɴ 💀', parse_mode=enums.ParseMode.HTML)
            if r['claims'] >= r['max_claims']:
                return await msg.reply('ᴄᴏᴜᴩᴏɴ ꜰᴜʟʟ 💀', parse_mode=enums.ParseMode.HTML)
            ex = await _one("SELECT 1 FROM coupon_claims WHERE code=? AND user_id=?", (code, msg.from_user.id))
            if ex: return await msg.reply('ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ✅', parse_mode=enums.ParseMode.HTML)
            await ensure_wallet(msg.from_user.id)
            await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (r['amount'], msg.from_user.id))
            await _run("UPDATE coupons SET claims=claims+1 WHERE code=?", (code,))
            await _run("INSERT INTO coupon_claims (code,user_id) VALUES (?,?)", (code, msg.from_user.id))
            await card(msg, 'happy', 'ᴄᴏᴜᴩᴏɴ ᴄʟᴀɪᴍᴇᴅ', [('🎟️', 'ᴄᴏᴅᴇ', code), ('💰', 'ɢᴏᴛ', f"+{r['amount']}")], mood='greedy')
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("status"))
    async def status_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2:
                return await msg.reply(err_wrong('/status <code>'), parse_mode=enums.ParseMode.HTML)
            r = await _one("SELECT * FROM coupons WHERE code=?", (msg.command[1].upper(),))
            if not r: return await msg.reply('ɴᴏ ꜱᴜᴄʜ ᴄᴏᴜᴩᴏɴ 🙈', parse_mode=enums.ParseMode.HTML)
            await card(msg, 'happy', 'ᴄᴏᴜᴩᴏɴ ꜱᴛᴀᴛᴜꜱ', [
                ('🎟️', 'ᴄᴏᴅᴇ', r['code']), ('💰', 'ᴀᴍᴛ', f"{r['amount']}"),
                ('📊', 'ᴄʟᴀɪᴍꜱ', f"{r['claims']}/{r['max_claims']}"),
                ('⏳', 'ʟᴇꜰᴛ', f"{r['max_claims']-r['claims']}")])
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("coupons"))
    async def coupons_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await msg.reply(hcard('ᴄᴏᴜᴩᴏɴ ʜᴇʟᴩ', [
                ('🎟️', '/create_coupon', 'ᴍᴀᴋᴇ'), ('🗑️', '/del_coupon', 'ᴅᴇʟ'),
                ('🎫', '/coupon', 'ᴄʟᴀɪᴍ'), ('📊', '/status', 'ɪɴꜰᴏ')]),
                parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    # ── Intro / Relationships / Reminders / Rep ──
    @app.on_message(filters.command("setintro"))
    async def setintro_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            txt = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else ''
            if not txt or len(txt) > 200:
                return await msg.reply(err_wrong('/setintro <max 200 chars>'), parse_mode=enums.ParseMode.HTML)
            await _run("INSERT OR REPLACE INTO intros (user_id,intro_text,set_at) VALUES (?,?,?)",
                       (msg.from_user.id, txt, datetime.utcnow().isoformat()))
            await send_mood(app, msg.chat.id, 'cute_smile', 'ɪɴᴛʀᴏ ꜱᴀᴠᴇᴅ ✅', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("intro"))
    async def intro_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
            r = await _one("SELECT intro_text FROM intros WHERE user_id=?", (t.id,))
            await send_mood(app, msg.chat.id, 'peaceful', f'📝 {mention_html(t.id, t.first_name)}: {(r or {}).get("intro_text", "ɴᴏ ɪɴᴛʀᴏ ʏᴇᴛ~")}',
                            reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("marry"))
    async def marry_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t: return await msg.reply(err_wrong('/marry (reply)'), parse_mode=enums.ParseMode.HTML)
            from src.compat import InlineKeyboardMarkup, IKB as InlineKeyboardButton
            await _run("INSERT OR REPLACE INTO relationships (user_id,partner_id,relation_type,since) VALUES (?,?,?,?)",
                       (msg.from_user.id, t.id, 'pending', datetime.utcnow().isoformat()))
            kb = InlineKeyboardMarkup([[InlineKeyboardButton('💍 Accept', callback_data=f'marry_ok_{msg.from_user.id}_{t.id}', style="success"),
                                        InlineKeyboardButton('💔 Decline', callback_data=f'marry_no_{msg.from_user.id}_{t.id}', style="danger")]])
            await msg.reply(f'💍 {mention_html(msg.from_user.id, msg.from_user.first_name)} proposes to {mention_html(t.id, t.first_name)}!',
                            reply_markup=kb, parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_callback_query(filters.regex(r'^marry_(ok|no)_(\d+)_(\d+)$'))
    async def marry_cb(_, cq):
        try:
            act, a, b = cq.data.split('_')[1], int(cq.data.split('_')[2]), int(cq.data.split('_')[3])
            if cq.from_user.id != b:
                return await cq.answer('ᴏɴʟʏ ᴩʀᴏᴩᴏꜱᴇᴅ ᴄᴀɴ ᴀɴꜱᴡᴇʀ 💕', show_alert=True)
            if act == 'ok':
                await _run("INSERT OR REPLACE INTO relationships VALUES (?,?,?,?)",
                           (a, b, 'married', datetime.utcnow().isoformat()))
                await _run("INSERT OR REPLACE INTO relationships VALUES (?,?,?,?)",
                           (b, a, 'married', datetime.utcnow().isoformat()))
                await ensure_wallet(a); await ensure_wallet(b)
                await _run("UPDATE wallet SET balance=balance+500 WHERE user_id IN (?,?)", (a, b))
                await cq.edit_message_text(f'💒 Married! +500 each 🎉', parse_mode=enums.ParseMode.HTML)
            else:
                await _run("DELETE FROM relationships WHERE user_id=?", (a,))
                await cq.edit_message_text('💔 Declined~', parse_mode=enums.ParseMode.HTML)
            await cq.answer()
        except Exception:
            try: await cq.answer()
            except Exception: pass

    @app.on_message(filters.command("divorce"))
    async def divorce_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            await _run("DELETE FROM relationships WHERE user_id=? OR partner_id=?", (msg.from_user.id, msg.from_user.id))
            await ensure_wallet(msg.from_user.id)
            await _run("UPDATE wallet SET balance=MAX(0,balance-200) WHERE user_id=?", (msg.from_user.id,))
            await send_mood(app, msg.chat.id, 'sad', '💔 Divorced (-200) ~', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("relation"))
    async def relation_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            r = await _one("SELECT partner_id,relation_type,since FROM relationships WHERE user_id=?", (msg.from_user.id,))
            if not r: return await msg.reply('ꜱɪɴɢʟᴇ~ 💔', parse_mode=enums.ParseMode.HTML)
            await send_mood(app, msg.chat.id, 'longing', f"💕 {r['relation_type']} with <code>{r['partner_id']}</code> since {r['since'][:10]}",
                            reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("remind"))
    async def remind_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 3:
                return await msg.reply(err_wrong('/remind 30m <text>'), parse_mode=enums.ParseMode.HTML)
            p = parse_dur(msg.command[1])
            if not p: return await msg.reply(err_wrong('/remind 30m|2h|1d <text>'), parse_mode=enums.ParseMode.HTML)
            delta, _s = p
            txt = msg.text.split(None, 2)[2]
            at = (datetime.utcnow() + delta).isoformat()
            await _run("INSERT INTO reminders (user_id,chat_id,reminder_text,remind_at) VALUES (?,?,?,?)",
                       (msg.from_user.id, msg.chat.id, txt, at))
            await msg.reply(f'⏰ ɴᴏᴛᴇᴅ! ɪɴ {msg.command[1]} ⏳', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("myreminders"))
    async def myrem_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT id,reminder_text,remind_at FROM reminders WHERE user_id=? AND done=0 ORDER BY id DESC LIMIT 10",
                              (msg.from_user.id,))
            if not rows: return await msg.reply('ɴᴏ ᴩᴇɴᴅɪɴɢ ⏰', parse_mode=enums.ParseMode.HTML)
            await msg.reply(hcard('ᴍʏ ʀᴇᴍɪɴᴅᴇʀꜱ', [('⏰', f'#{r[0]}', f'{r[1][:40]} ({r[2][:16]})') for r in rows]),
                            parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("delreminder"))
    async def delrem_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if len(msg.command) < 2: return await msg.reply(err_wrong('/delreminder <id>'), parse_mode=enums.ParseMode.HTML)
            try:
                rid = int(msg.command[1])
            except Exception:
                return await msg.reply(err_wrong('/delreminder <id>'), parse_mode=enums.ParseMode.HTML)
            await _run("DELETE FROM reminders WHERE id=? AND user_id=?", (rid, msg.from_user.id))
            await msg.reply('ᴅᴇʟᴇᴛᴇᴅ ✅', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("rep"))
    async def rep_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t: return await msg.reply(err_wrong('/rep (reply)'), parse_mode=enums.ParseMode.HTML)
            r = await _one("SELECT last_given FROM reputation WHERE user_id=?", (msg.from_user.id,))
            if r and r.get('last_given'):
                try:
                    if (datetime.utcnow() - datetime.fromisoformat(r['last_given'])).total_seconds() < 12*3600:
                        return await msg.reply('12ʜ ᴄᴏᴏʟᴅᴏᴡɴ ⏳', parse_mode=enums.ParseMode.HTML)
                except Exception: pass
            await _run("INSERT OR IGNORE INTO reputation (user_id) VALUES (?)", (t.id,))
            await _run("UPDATE reputation SET rep_points=rep_points+1, last_received=? WHERE user_id=?",
                       (datetime.utcnow().isoformat(), t.id))
            await _run("INSERT OR IGNORE INTO reputation (user_id) VALUES (?)", (msg.from_user.id,))
            await _run("UPDATE reputation SET last_given=? WHERE user_id=?",
                       (datetime.utcnow().isoformat(), msg.from_user.id))
            await send_mood(app, msg.chat.id, 'heart_eyes', f'⭐ +1 ʀᴇᴩ ᴛᴏ {mention_html(t.id, t.first_name)}!', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    for _cmd, _tbl, _col, _ttl in [("toprep", "reputation", "rep_points", "ᴛᴏᴩ ʀᴇᴩ"),
                                   ("topxp", "user_xp", "xp", "ᴛᴏᴩ xᴩ"),
                                   ("streak", None, None, None)]:
        pass

    @app.on_message(filters.command("toprep"))
    async def toprep_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT user_id,rep_points FROM reputation ORDER BY rep_points DESC LIMIT 10")
            lines = []
            for i, r in enumerate(rows):
                try: u = await app.get_users(r[0]); nm = mention_html(u.id, u.first_name)
                except Exception: nm = f'<code>{r[0]}</code>'
                lines.append(f'{medal(i)} {nm} — <b>{r[1]}</b>')
            await send_mood(app, msg.chat.id, 'love', '✨ ╭── [ 🌸 '+ff('ᴛᴏᴩ ʀᴇᴩ')+' ]\n│\n\n' + ('\n'.join('├── '+l for l in lines) if lines else '└── ɴᴏ ᴅᴀᴛᴀ~'),
                            reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("topxp"))
    async def topxp_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rows = await _all("SELECT user_id,xp,level FROM user_xp ORDER BY xp DESC LIMIT 10")
            lines = []
            for i, r in enumerate(rows):
                try: u = await app.get_users(r[0]); nm = mention_html(u.id, u.first_name)
                except Exception: nm = f'<code>{r[0]}</code>'
                lines.append(f'{medal(i)} {nm} — <b>{r[1]}</b> (ʟ{r[2]})')
            await send_mood(app, msg.chat.id, 'determined', '✨ ╭── [ 🌸 '+ff('ᴛᴏᴩ xᴩ')+' ]\n│\n\n' + ('\n'.join('├── '+l for l in lines) if lines else '└── ɴᴏ ᴅᴀᴛᴀ~'),
                            reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["streak", "level"]))
    async def streak_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            from src.db_extra import get_xp as _gx
            x = await _gx(msg.from_user.id)
            s = await _one("SELECT * FROM streaks WHERE user_id=?", (msg.from_user.id,)) or {}
            xp, lvl = x.get('xp', 0), x.get('level', 1)
            import math
            need = int(100 * (lvl ** 1.5)) + 100
            pct = min(100, int(xp / max(1, need) * 100))
            bar = '█' * (pct // 10) + '░' * (10 - pct // 10)
            await send_mood(app, msg.chat.id, 'cheerful', hcard('ꜱᴛʀᴇᴀᴋ/xᴩ', [
                ('🔥', 'ꜱᴛʀᴇᴀᴋ', f"{s.get('current_streak',0)} (ʙᴇꜱᴛ {s.get('longest_streak',0)})"),
                ('⭐', 'ʟᴇᴠᴇʟ', f'{lvl} [{bar}] {pct}%')]), reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["leaderboard", "lb", "economy", "botinfo", "ping"]))
    async def miscinfo_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            cmd = msg.command[0]
            if cmd in ('leaderboard', 'lb'):
                await send_mood(app, msg.chat.id, 'cheerful', hcard('ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ', [
                    ('💰', '/toprich', 'ᴄᴏɪɴꜱ'), ('⚔️', '/topkill', 'ᴋɪʟʟꜱ'),
                    ('⭐', '/topxp', 'xᴩ'), ('💚', '/toprep', 'ʀᴇᴩ')]),
                    reply_to_id=msg.id)
            elif cmd == 'economy':
                await send_mood(app, msg.chat.id, 'curious', hcard('ᴇᴄᴏɴᴏᴍʏ', [
                    ('⚔️', '/kill', 'ᴋɪʟʟ'), ('🔫', '/rob', 'ʀᴏʙ'), ('🎁', '/give', 'ɢɪꜰᴛ'),
                    ('💰', '/bal', 'ʙᴀʟ'), ('🏦', '/wallet', 'ʙᴀɴᴋ'), ('💎', '/gems', 'ɢᴇᴍꜱ')]),
                    reply_to_id=msg.id)
            elif cmd == 'botinfo':
                import time as _t
                import riruru as _R
                up = int(_t.time() - _R.START_TIME); h, r = divmod(up, 3600); m, s = divmod(r, 60)
                st = await _one("SELECT (SELECT COUNT(*) FROM users) u, (SELECT COUNT(*) FROM groups) g")
                await send_mood(app, msg.chat.id, 'happy', hcard('ʙᴏᴛ ɪɴꜰᴏ', [
                    ('👥', 'ᴜꜱᴇʀꜱ', f"{st['u'] if st else 0}"), ('👪', 'ɢʀᴏᴜᴩꜱ', f"{st['g'] if st else 0}"),
                    ('⏱️', 'ᴜᴩᴛɪᴍᴇ', f'{h}h {m}m'), ('🌸', 'ᴠᴇʀ', '2.0 ᴍᴜʟᴛɪ')]),
                    reply_to_id=msg.id)
            else:  # ping
                import time as _t
                t0 = _t.time()
                await _one("SELECT 1")
                dbms = int((_t.time() - t0) * 1000)
                await send_mood(app, msg.chat.id, 'happy', hcard('ᴩɪɴɢ', [('🏓', 'ʙᴏᴛ', 'ᴀʟɪᴠᴇ'), ('🗄️', 'ᴅʙ', f'{dbms}ᴍꜱ')]),
                                reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["confession", "confess"]))
    async def confession_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if msg.command[0] == 'confession':
                txt = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else ''
                if not txt: return await msg.reply(err_wrong('/confession <text>'), parse_mode=enums.ParseMode.HTML)
                await _run("INSERT INTO confessions (from_id,chat_id,message) VALUES (?,?,?)",
                           (msg.from_user.id, msg.chat.id, txt))
                await send_mood(app, msg.chat.id, 'shy', f'💌 Anonymous: {txt}', reply_to_id=msg.id)
            else:
                t = msg.reply_to_message.from_user if msg.reply_to_message else None
                txt = ' '.join(msg.command[1:]) if len(msg.command) > 1 else ''
                if not t or not txt:
                    return await msg.reply(err_wrong('/confess (reply) <text>'), parse_mode=enums.ParseMode.HTML)
                await _run("INSERT INTO confessions (from_id,to_id,chat_id,message) VALUES (?,?,?,?)",
                           (msg.from_user.id, t.id, msg.chat.id, txt))
                try: await app.send_message(t.id, f'💌 Someone confessed to you: {txt}')
                except Exception: pass
                await send_mood(app, msg.chat.id, 'blush', 'ꜱᴇɴᴛ ᴀɴᴏɴʏᴍᴏᴜꜱʟʏ 💌', reply_to_id=msg.id)
        except Exception: traceback.print_exc()
