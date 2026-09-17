#!/usr/bin/env python3
"""Dot-mod commands (.ban/.mute/...) + admin internals. Called from group_msg."""
import traceback
import os
from datetime import datetime, timedelta

FACES_DIR = "assets/faces"

async def _send_mod_image(app, chat_id, action, user_name="", detail="", fallback_text=""):
    """Send mood face image with caption, fall back to text."""
    mood_map = {
        'ban': 'furious', 'unban': 'peaceful', 'kick': 'smug',
        'mute': 'annoyed', 'unmute': 'peaceful', 'warn': 'serious',
        'unwarn': 'peaceful', 'warns': 'suspicious', 'promote': 'cheerful',
        'demote': 'serious', 'success': 'cheerful', 'error': 'worried',
    }
    mood = mood_map.get(action, 'happy')
    img = f"{FACES_DIR}/{mood}.png"
    if not os.path.exists(img):
        img = f"{FACES_DIR}/happy.png"
    if os.path.exists(img):
        try:
            await app.send_photo(chat_id, img, caption=fallback_text)
            return
        except Exception:
            pass
    await app.send_message(chat_id, fallback_text)


async def handle_dot(app, msg) -> bool:
    """Return True if handled. Silent variants delete cmd msg."""
    try:
        text = (msg.text or '').strip()
        if not text or text[0] not in ('.', '!'):
            return False
        parts = text[1:].split()
        if not parts:
            return False
        cmd = parts[0].lower()
        args = parts[1:]
        silent = cmd.startswith('s') and cmd[1:] in ('ban', 'mute', 'kick') or cmd in ('sban', 'smute', 'skick')
        base = cmd
        for alias, real in (('sban', 'ban'), ('dban', 'ban'), ('smute', 'mute'),
                            ('dmute', 'mute'), ('skick', 'kick')):
            if cmd == alias:
                base = real
        if base not in ('ban', 'unban', 'kick', 'mute', 'unmute', 'warn', 'unwarn',
                        'warns', 'promote', 'demote', 'demote_all', 'title',
                        'pin', 'unpin', 'd', 'help', 'add', 'remove', 'res'):
            return False
        # admin check
        try:
            me = await app.get_chat_member(msg.chat.id, msg.from_user.id)
            s = getattr(me.status, 'value', str(me.status)) if me.status else ''
            if s not in ('administrator', 'creator', 'owner'):
                import riruru as R
                if not R.is_owner(msg.from_user.id):
                    await msg.reply('ᴀᴅᴍɪɴ ᴏɴʟʏ 🔒')
                    return True
        except Exception:
            # get_chat_member failed — fallback: check if user is owner
            import riruru as R
            if not R.is_owner(msg.from_user.id):
                await msg.reply('ᴀᴅᴍɪɴ ᴏɴʟʏ 🔒')
                return True
        t = msg.reply_to_message.from_user if msg.reply_to_message else None
        if silent:
            try: await msg.delete()
            except Exception: pass

        async def need(perm: str) -> bool:
            try:
                botm = await app.get_chat_member(msg.chat.id, (await app.get_me()).id)
                priv = getattr(botm, 'privileges', None)
                ok = True
                if priv is not None:
                    ok = bool(getattr(priv, 'can_restrict_members', True)) if perm == 'restrict' else True
                    if perm == 'pin':
                        ok = bool(getattr(priv, 'can_pin_messages', True))
                    if perm == 'promote':
                        ok = bool(getattr(priv, 'can_promote_members', True))
                    if perm == 'delete':
                        ok = bool(getattr(priv, 'can_delete_messages', True))
                if not ok:
                    await app.send_message(msg.chat.id, f'ɪ ɴᴇᴇᴅ {perm} ᴩᴇʀᴍɪꜱꜱɪᴏɴ 🙏')
                    return False
                return True
            except Exception:
                # Can't check bot permissions — try the action anyway
                return True

        if base == 'help':
            await app.send_message(msg.chat.id,
                '.ban .unban .kick .mute <30m/1h/1d> .unmute .warn .unwarn .warns .promote .demote .title .pin .unpin .d')
            return True
        if base == 'd':
            if msg.reply_to_message and await need('delete'):
                try: await msg.reply_to_message.delete()
                except Exception: pass
            return True
        if base == 'pin':
            if msg.reply_to_message and await need('pin'):
                try: await app.pin_chat_message(msg.chat.id, msg.reply_to_message.id)
                except Exception: pass
            return True
        if base == 'unpin':
            if await need('pin'):
                try: await app.unpin_chat_message(msg.chat.id)
                except Exception: pass
            return True
        if not t and base in ('ban', 'unban', 'kick', 'mute', 'unmute', 'warn', 'unwarn', 'warns', 'promote', 'demote', 'title'):
            await app.send_message(msg.chat.id, 'ʀᴇᴩʟʏ ᴋᴀʀᴏ ᴜꜱᴇʀ ᴩᴇ 🙈')
            return True
        if base == 'ban':
            if await need('restrict'):
                try:
                    await app.ban_chat_member(msg.chat.id, t.id)
                    if cmd == 'dban' and msg.reply_to_message:
                        try: await msg.reply_to_message.delete()
                        except Exception: pass
                    await _send_mod_image(app, msg.chat.id, 'ban', t.first_name,
                                          f"Banned by {msg.from_user.first_name}",
                                          f'🚫 Banned {t.first_name}')
                except Exception as e:
                    await _send_mod_image(app, msg.chat.id, 'error', t.first_name,
                                          str(e)[:50], f'ꜰᴀɪʟᴇᴅ: {e}')
            return True
        if base == 'unban':
            if await need('restrict'):
                try:
                    await app.unban_chat_member(msg.chat.id, t.id)
                    await _send_mod_image(app, msg.chat.id, 'unban', t.first_name,
                                          f"Unbanned by {msg.from_user.first_name}",
                                          f'✅ Unbanned {t.first_name}')
                except Exception as e:
                    await app.send_message(msg.chat.id, f'ꜰᴀɪʟᴇᴅ: {e}')
            return True
        if base == 'kick':
            if await need('restrict'):
                try:
                    await app.ban_chat_member(msg.chat.id, t.id)
                    await app.unban_chat_member(msg.chat.id, t.id)
                    await _send_mod_image(app, msg.chat.id, 'kick', t.first_name,
                                          f"Kicked by {msg.from_user.first_name}",
                                          f'👢 Kicked {t.first_name}')
                except Exception as e:
                    await app.send_message(msg.chat.id, f'ꜰᴀɪʟᴇᴅ: {e}')
            return True
        if base == 'mute':
            if await need('restrict'):
                dur = 3600
                if args:
                    a = args[-1].lower()
                    if a.endswith('m') and a[:-1].isdigit(): dur = int(a[:-1]) * 60
                    elif a.endswith('h') and a[:-1].isdigit(): dur = int(a[:-1]) * 3600
                    elif a.endswith('d') and a[:-1].isdigit(): dur = int(a[:-1]) * 86400
                try:
                    from kittygram.types import ChatPermissions as _CP
                    await app.restrict_chat_member(msg.chat.id, t.id,
                        permissions=_CP(can_send_messages=False),
                        until_date=datetime.utcnow() + timedelta(seconds=dur))
                    if cmd == 'dmute' and msg.reply_to_message:
                        try: await msg.reply_to_message.delete()
                        except Exception: pass
                    await _send_mod_image(app, msg.chat.id, 'mute', t.first_name,
                                          f"Muted {dur//60}m by {msg.from_user.first_name}",
                                          f'🔇 Muted {t.first_name} {dur//60}m')
                except Exception as e:
                    await app.send_message(msg.chat.id, f'ꜰᴀɪʟᴇᴅ: {e}')
            return True
        if base == 'unmute':
            if await need('restrict'):
                try:
                    from kittygram.types import ChatPermissions as _CP
                    await app.restrict_chat_member(msg.chat.id, t.id,
                        permissions=_CP(can_send_messages=True,
                            can_send_media_messages=True, can_send_other_messages=True,
                            can_add_web_page_previews=True))
                    await _send_mod_image(app, msg.chat.id, 'unmute', t.first_name,
                                          f"Unmuted by {msg.from_user.first_name}",
                                          f'🔊 Unmuted {t.first_name}')
                except Exception as e:
                    await app.send_message(msg.chat.id, f'ꜰᴀɪʟᴇᴅ: {e}')
            return True
        if base in ('warn', 'unwarn', 'warns'):
            import aiosqlite, os
            DB = os.environ.get('DB_PATH', 'mochi.db')
            async with aiosqlite.connect(DB) as db:
                if base == 'warn':
                    await db.execute("INSERT INTO warn_records (chat_id,user_id,reason,issued_by) VALUES (?,?,?,?)",
                                     (msg.chat.id, t.id, ' '.join(args) or 'warn', msg.from_user.id))
                    await db.commit()
                    async with db.execute("SELECT COUNT(*) FROM warn_records WHERE chat_id=? AND user_id=?",
                                          (msg.chat.id, t.id)) as cur:
                        n = (await cur.fetchone() or [0])[0]
                    if n >= 3:
                        try:
                            await app.ban_chat_member(msg.chat.id, t.id)
                            await db.execute("DELETE FROM warn_records WHERE chat_id=? AND user_id=?", (msg.chat.id, t.id))
                            await db.commit()
                        except Exception: pass
                        await _send_mod_image(app, msg.chat.id, 'ban', t.first_name,
                                              "Auto-banned: 3 warns", f'🚫 {t.first_name} auto-banned (3 warns)')
                    else:
                        await _send_mod_image(app, msg.chat.id, 'warn', t.first_name,
                                              f"Warn {n}/3", f'⚠️ Warn {n}/3 to {t.first_name}')
                elif base == 'unwarn':
                    await db.execute("DELETE FROM warn_records WHERE rowid IN (SELECT rowid FROM warn_records WHERE chat_id=? AND user_id=? ORDER BY id DESC LIMIT 1)",
                                     (msg.chat.id, t.id))
                    await db.commit()
                    await _send_mod_image(app, msg.chat.id, 'unmute', t.first_name,
                                          "Removed 1 warn", f'✅ -1 warn for {t.first_name}')
                else:
                    async with db.execute("SELECT reason,issued_at FROM warn_records WHERE chat_id=? AND user_id=? ORDER BY id DESC",
                                          (msg.chat.id, t.id)) as cur:
                        rows = await cur.fetchall()
                    if not rows:
                        await app.send_message(msg.chat.id, f'✅ {t.first_name} Clean')
                    else:
                        lines = [f'Warns for {t.first_name}: {len(rows)}']
                        lines += [f'- {r[0]} ({r[1]})' for r in rows[:5]]
                        await app.send_message(msg.chat.id, '\n'.join(lines))
            return True
        if base in ('promote', 'demote', 'demote_all', 'title', 'add', 'remove', 'res'):
            if await need('promote'):
                try:
                    if base == 'promote':
                        lvl = int(args[-1]) if args and args[-1].isdigit() else 1
                        from src.compat import enums as E
                        await app.promote_chat_member(msg.chat.id, t.id,
                            privileges=E.ChatPrivileges(can_manage_chat=lvl >= 1, can_delete_messages=lvl >= 1,
                                can_restrict_members=lvl >= 2, can_promote_members=lvl >= 3,
                                can_pin_messages=True, is_anonymous=False))
                        await _send_mod_image(app, msg.chat.id, 'promote', t.first_name,
                                              f"Level {lvl} by {msg.from_user.first_name}",
                                              f'⬆️ Promoted {t.first_name} L{lvl}')
                    elif base == 'demote':
                        from src.compat import enums as E
                        await app.promote_chat_member(msg.chat.id, t.id,
                            privileges=E.ChatPrivileges(is_anonymous=False))
                        await _send_mod_image(app, msg.chat.id, 'demote', t.first_name,
                                              f"Demoted by {msg.from_user.first_name}",
                                              f'⬇️ Demoted {t.first_name}')
                    elif base == 'title' and len(args) >= 1:
                        await app.set_administrator_custom_title(msg.chat.id, t.id, ' '.join(args)[:16])
                        await _send_mod_image(app, msg.chat.id, 'success', t.first_name,
                                              f"Title: {' '.join(args)[:16]}",
                                              f'✏️ Title set for {t.first_name}')
                except Exception as e:
                    await _send_mod_image(app, msg.chat.id, 'error', t.first_name,
                                          str(e)[:50], f'ꜰᴀɪʟᴇᴅ: {e}')
            return True
        return True
    except Exception:
        traceback.print_exc()
        return False
