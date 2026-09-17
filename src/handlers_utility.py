#!/usr/bin/env python3
"""Utility / Stickers / Fun / 50+ features. # NEW — HTML, free APIs, no keys."""
import asyncio
import aiohttp
import random
import re
import traceback
import urllib.parse
from datetime import datetime


async def _collect_members(app, chat_id, limit=50):
    """Fetch group members with caller-side timeout protection."""
    out = []
    async for m in app.get_chat_members(chat_id, limit=limit):
        out.append(m.user)
        if len(out) >= limit:
            break
    return out

def register(app, bert=None):
    from src.compat import filters, enums
    import riruru as R
    from src.utils import ff, hcard, mention_html, flood_ok, err_wrong, safe_calc
    from src.db_extra import _one, _all, _run, ensure_wallet, get_wallet, add_xp
    from src.media import cached_gif, get_http_session
    from riruru import send_mood

    async def api_json(url, timeout=10):
        try:
            s = await get_http_session()
            async with s.get(url, timeout=__import__('aiohttp').ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return await r.json()
        except Exception:
            pass
        return None

    async def api_post(url, payload, timeout=12):
        try:
            s = await get_http_session()
            async with s.post(url, json=payload, timeout=__import__('aiohttp').ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return await r.json()
        except Exception:
            pass
        return None

    async def fcard(msg, act, title, rows):
        txt = hcard(title, rows)
        return await send_mood(app, msg.chat.id, 'determined', txt, reply_to_id=msg.id)

    # /q quote sticker # NEW
    @app.on_message(filters.command("q"))
    async def q_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            rp = msg.reply_to_message
            if not rp or not (rp.text or rp.caption or rp.photo):
                return await msg.reply(err_wrong('/q (reply to text/photo)'), parse_mode=enums.ParseMode.HTML)
            txt = (rp.text or rp.caption or '')[:300]
            name = rp.from_user.first_name if rp.from_user else 'anon'
            # Pillow in thread (benchmark: never block loop)
            def _make():
                from PIL import Image, ImageDraw, ImageFont
                import io
                W = H = 512
                img = Image.new('RGB', (W, H), (24, 24, 28))
                d = ImageDraw.Draw(img)
                # avatar circle placeholder
                d.ellipse([24, 24, 120, 120], fill=(120, 90, 200))
                try: d.text((140, 40), name[:20], fill=(255, 255, 255))
                except Exception: pass
                # wrap text
                words, lines, cur = txt.split(), [], ''
                for w_ in words:
                    if len(cur) + len(w_) + 1 > 28:
                        lines.append(cur); cur = w_
                    else: cur = (cur + ' ' + w_).strip()
                if cur: lines.append(cur)
                y = 150
                for ln in lines[:10]:
                    try: d.text((24, y), ln, fill=(255, 255, 255))
                    except Exception: pass
                    y += 30
                try: d.text((W - 150, H - 30), 'Riruru 🌸', fill=(180, 180, 180))
                except Exception: pass
                bio = io.BytesIO(); bio.name = 'quote.webp'
                img.save(bio, 'WEBP'); bio.seek(0)
                return bio.getvalue()
            try:
                data = await asyncio.to_thread(_make)
                await msg.reply_sticker(__import__('io').BytesIO(data))
            except Exception:
                await msg.reply(f'💬 <b>{name}:</b> {txt[:200]}', parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command("own"))
    async def own_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            me = await app.get_me()
            pack = f'riruru_{msg.from_user.id}_by_{me.username}'
            await _run("INSERT OR REPLACE INTO user_sticker_packs (user_id,pack_name,pack_title) VALUES (?,?,?)",
                       (msg.from_user.id, pack, f"Riruru {msg.from_user.id}"))
            await send_mood(app, msg.chat.id, 'curious', f'🎨 ʏᴏᴜʀ ᴩᴀᴄᴋ: <code>{pack}</code>\nꜱᴇɴᴅ ꜱᴛɪᴄᴋᴇʀꜱ ᴠɪᴀ @Stickers, I will use this pack 🌸', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["detail", "id", "admins", "owner", "info"]))
    async def info_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            c = msg.command[0]
            if c in ("admins", "owner") and (msg.chat.id > 0 if isinstance(msg.chat.id, int) else False):
                return await msg.reply('ɢʀᴏᴜᴩ ᴏɴʟʏ 🙈 — ɢʀᴏᴜᴩ ᴍᴇɪɴ ᴜꜱᴇ ᴋᴀʀᴏ', parse_mode=enums.ParseMode.HTML)
            if c == 'detail':
                t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
                rows = await _all("SELECT username,first_name,recorded_at FROM name_history WHERE user_id=? ORDER BY id DESC LIMIT 10", (t.id,))
                if not rows: return await msg.reply('ɴᴏ ʜɪꜱᴛᴏʀʏ ʏᴇᴛ 📝', parse_mode=enums.ParseMode.HTML)
                await send_mood(app, msg.chat.id, 'suspicious', hcard('ɴᴀᴍᴇ ʜɪꜱᴛᴏʀʏ', [('📝', f'h{i+1}', f'@{r[0] or "-"} / {r[1] or "-"} ({(r[2] or "")[:10]})') for i, r in enumerate(rows)]), reply_to_id=msg.id)
            elif c == 'id':
                t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
                await send_mood(app, msg.chat.id, 'suspicious', hcard('ɪᴅꜱ', [('👤', 'ᴜꜱᴇʀ', f'<code>{t.id}</code>'), ('👪', 'ᴄʜᴀᴛ', f'<code>{msg.chat.id}</code>')]), reply_to_id=msg.id)
            elif c == 'admins':
                outs = []
                async for m in app.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    try: outs.append(mention_html(m.user.id, m.user.first_name))
                    except Exception: pass
                await send_mood(app, msg.chat.id, 'suspicious', '👑 ' + ' '.join(outs[:30]), reply_to_id=msg.id)
            else:
                try:
                    async for m in app.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                        if m.status == 'creator':
                            return await send_mood(app, msg.chat.id, 'suspicious', f'👑 ᴏᴡɴᴇʀ: {mention_html(m.user.id, m.user.first_name)}', reply_to_id=msg.id)
                except Exception: pass
                await send_mood(app, msg.chat.id, 'suspicious', 'ɴᴏ ᴏᴡɴᴇʀ ꜰᴏᴜɴᴅ 🙈', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["report", "isdeleted"]))
    async def report_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            if msg.command[0] == "report" and isinstance(msg.chat.id, int) and msg.chat.id > 0:
                return await msg.reply('ɢʀᴏᴜᴩ ᴏɴʟʏ 🙈 — <code>/report</code> needs a group (reply to someone)', parse_mode=enums.ParseMode.HTML)
            if msg.command[0] == 'report':
                t = msg.reply_to_message.from_user if msg.reply_to_message else None
                if not t: return await msg.reply(err_wrong('/report (reply)'), parse_mode=enums.ParseMode.HTML)
                sent = 0
                async for m in app.get_chat_members(msg.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    try:
                        await app.send_message(m.user.id, f'🚨 ʀᴇᴩᴏʀᴛ from {msg.chat.title}: {msg.from_user.first_name} reported {t.first_name}')
                        sent += 1
                    except Exception: pass
                await send_mood(app, msg.chat.id, 'worried', f'ʀᴇᴩᴏʀᴛᴇᴅ ᴛᴏ {sent} ᴀᴅᴍɪɴꜱ ✅ (silent)', reply_to_id=msg.id)
                try: await msg.delete()
                except Exception: pass
            else:
                if len(msg.command) < 2: return await msg.reply(err_wrong('/isdeleted <user_id>'), parse_mode=enums.ParseMode.HTML)
                try:
                    await app.get_chat(int(msg.command[1]))
                    await send_mood(app, msg.chat.id, 'worried', 'ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ᴀᴄᴛɪᴠᴇ ✅', reply_to_id=msg.id)
                except Exception:
                    await send_mood(app, msg.chat.id, 'worried', 'ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ ✅', reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    @app.on_message(filters.command(["voice", "tr", "calc", "c"]))
    async def convert_util_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            c = msg.command[0]
            if c == 'voice':
                rp = msg.reply_to_message
                txt = (rp.text or rp.caption or '') if rp else ' '.join(msg.command[1:])
                if not txt: return await msg.reply(err_wrong('/voice (reply text)'), parse_mode=enums.ParseMode.HTML)
                try:
                    import io as _io
                    import edge_tts
                    # Edge TTS: cute anime girl voice (Ana = young/cute female)
                    voice = 'en-US-AnaNeural'
                    communicate = edge_tts.Communicate(txt, voice, rate='-5%', pitch='+10Hz')
                    buf = _io.BytesIO()
                    async for chunk in communicate.stream():
                        if chunk['type'] == 'audio':
                            buf.write(chunk['data'])
                    buf.seek(0)
                    if buf.getbuffer().nbytes == 0:
                        return await msg.reply('ᴛᴛꜱ ꜰᴀɪʟᴇᴅ 💀', parse_mode=enums.ParseMode.HTML)
                    buf.name = 'riruru_voice.mp3'
                    await msg.reply_voice(voice=buf)
                except Exception as e:
                    traceback.print_exc()
                    await msg.reply(f'ᴛᴛꜱ ꜰᴀɪʟᴇᴅ 💀 <code>{str(e)[:80]}</code>', parse_mode=enums.ParseMode.HTML)
            elif c == 'tr':
                if len(msg.command) < 3 and not msg.reply_to_message:
                    return await msg.reply(err_wrong('/tr <lang> <text|reply>'), parse_mode=enums.ParseMode.HTML)
                lang = msg.command[1]
                txt = ' '.join(msg.command[2:]) or ((msg.reply_to_message.text or '') if msg.reply_to_message else '')
                d = await api_json(f'https://api.mymemory.translated.net/get?q={urllib.parse.quote(txt[:400])}&langpair=auto|{lang}')
                try:
                    out = d['responseData']['translatedText']
                    if 'MYMEMORY WARNING' in out or 'INVALID' in out:
                        raise ValueError('quota')
                except Exception:
                    out = None
                if not out:
                    return await msg.reply('ᴛʀᴀɴꜱʟᴀᴛɪᴏɴ Qᴜᴏᴛᴀ ᴏᴠᴇʀ ꜰᴏʀ ᴛᴏᴅᴀʏ ⏳ — ᴛʀʏ ᴀɢᴀɪɴ ᴛᴏᴍᴏʀʀᴏᴡ', parse_mode=enums.ParseMode.HTML)
                await send_mood(app, msg.chat.id, 'greedy', hcard('ᴛʀᴀɴꜱʟᴀᴛᴇ', [('📥', 'ꜱʀᴄ', txt[:200]), ('📤', lang, out[:500])]), reply_to_id=msg.id)
            else:
                expr = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else ''
                if not expr: return await msg.reply(err_wrong('/calc <expr>'), parse_mode=enums.ParseMode.HTML)
                try: res = safe_calc(expr)
                except Exception as e: return await msg.reply(f'ʙᴀᴋᴀ~ {e} 🙈', parse_mode=enums.ParseMode.HTML)
                await send_mood(app, msg.chat.id, 'greedy', hcard('ᴄᴀʟᴄ', [('🧮', 'ᴇxᴩʀ', expr[:100]), ('✅', 'ʀᴇꜱᴜʟᴛ', f'<code>{res}</code>')]), reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    # fun: kiss/hug/slap/punch/bite/murder/love/look + crush/couples/truth/dare/puzzle # NEW
    for _cmd, _act, _emo, _verb in [
        ('kiss', 'kiss', '💋', 'kisses'), ('hug', 'hug', '🤗', 'hugs'),
        ('slap', 'slap', '👋', 'slaps'), ('punch', 'punch', '👊', 'punches'),
        ('bite', 'bite', '🦷', 'bites'), ('murder', 'happy', '🔪', 'murders'),
        ('love', 'happy', '❤️', 'loves'), ('look', 'happy', '👀', 'looks at')]:
        def _mk(cmd=_cmd, act=_act, emo=_emo, verb=_verb):
            @app.on_message(filters.command(cmd))
            async def _h(_, msg):
                try:
                    if await R._maint_block(msg):
                        return
                    if not flood_ok(msg.from_user.id): return
                    t = msg.reply_to_message.from_user if msg.reply_to_message else None
                    if not t: return await msg.reply(err_wrong(f'/{cmd} (reply)'), parse_mode=enums.ParseMode.HTML)
                    gif = await cached_gif(act)
                    cap = f'{emo} {mention_html(msg.from_user.id, msg.from_user.first_name)} {verb} {mention_html(t.id, t.first_name)}'
                    try:
                        if gif: return await msg.reply_animation(gif, caption=cap, parse_mode=enums.ParseMode.HTML)
                    except Exception: pass
                    # Pillow fallback: generate reaction image
                    try:
                        from src.images import reaction_image
                        img_buf = await reaction_image(act, msg.from_user.first_name or "User", t.first_name or "User")
                        if img_buf:
                            return await msg.reply_photo(img_buf, caption=cap, parse_mode=enums.ParseMode.HTML)
                    except Exception: pass
                    await msg.reply(cap, parse_mode=enums.ParseMode.HTML)
                except Exception: traceback.print_exc()
            return _h
        _mk()

    @app.on_message(filters.command(["crush", "couples", "truth", "dare", "puzzle",
                                     "brain", "stupid_meter", "rizz", "roast", "fortune",
                                     "8ball", "aesthetictext", "bio", "rap"]))
    async def funpack_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            import riruru as R2
            c = msg.command[0]
            if c == 'crush':
                t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
                try: members = await asyncio.wait_for(_collect_members(app, msg.chat.id), timeout=20)
                except Exception: members = []
                pick = random.choice(members).first_name if members else 'Someone'
                await fcard(msg, 'happy', 'ᴄʀᴜꜱʜ', [('💕', 'ꜱᴇᴄʀᴇᴛ', f"{t.first_name}'s crush is {pick}")])
            elif c == 'couples':
                try: members = await asyncio.wait_for(_collect_members(app, msg.chat.id), timeout=20)
                except Exception: members = []
                if len(members) >= 2:
                    a, b = random.sample(members, 2)
                    await fcard(msg, 'happy', 'ᴛᴏᴅᴀʏꜱ ᴄᴏᴜᴩʟᴇ', [('💑', 'ᴩᴀɪʀ', f'{a.first_name} + {b.first_name}')])
                else: await msg.reply('ɴᴇᴇᴅ ᴍᴏʀᴇ ᴍᴇᴍʙᴇʀꜱ 💕', parse_mode=enums.ParseMode.HTML)
            elif c == 'truth':
                qs = ['Biggest crush?', 'Worst lie told?', 'Secret talent?', 'Last cry?', 'Phone wallpaper?'] * 8
                await fcard(msg, 'happy', 'ᴛʀᴜᴛʜ', [('❓', 'Q', random.choice(qs))])
            elif c == 'dare':
                ds = ['Send a voice note singing', 'Text your crush hi', 'Do 10 pushups', 'Change DP for 1h', 'Roast Riruru'] * 8
                await fcard(msg, 'happy', 'ᴅᴀʀᴇ', [('🔥', 'ᴅ', random.choice(ds))])
            elif c == 'puzzle':
                await fcard(msg, 'happy', 'ᴩᴜᴢᴢʟᴇ', [('🧩', 'Q', 'I speak without mouth, hear without ears? (/answer echo)')])
            elif c in ('brain', 'stupid_meter'):
                t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
                await fcard(msg, 'happy', c, [('🧠', 'ꜱᴄᴏʀᴇ', f'{t.first_name}: {random.randint(0,100)}%')])
            elif c in ('rizz', 'roast', 'fortune', 'bio', 'rap'):
                t = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
                prompt = {'rizz': f'funny pickup line for {t.first_name}', 'roast': f'playful roast of {t.first_name}',
                          'fortune': f'daily fortune for {t.first_name}', 'bio': f'70-char telegram bio for {t.first_name}',
                          'rap': f'short rap verse about {t.first_name}'}[c]
                out = await R2.riruru_reply(prompt, user_id=msg.from_user.id) or "haha 😄"
                await fcard(msg, 'happy', c, [('✨', 'ᴏᴜᴛ', out[:800])])
            elif c == '8ball':
                ans = random.choice(['Yes ✨', 'No 💀', 'Maybe~ 🤔', 'Ask later ⏳', 'Definitely! 🎉'] * 4)
                await fcard(msg, 'happy', '8ʙᴀʟʟ', [('🔮', 'ᴀɴꜱ', ans)])
            elif c == 'ship':
                sc = random.randint(0, 100)
                await fcard(msg, 'happy', 'ꜱʜɪᴩ', [('💕', 'ꜱᴄᴏʀᴇ', f'{sc}% {"❤️"*(sc//10)}')])
            else:
                txt = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else ''
                if not txt: return await msg.reply(err_wrong(f'/{c} <text>'), parse_mode=enums.ParseMode.HTML)
                if c == 'aesthetictext':
                    from src.utils import ff as _ff
                    await send_mood(app, msg.chat.id, 'determined', _ff(txt), reply_to_id=msg.id)
                else:
                    out = await R2.riruru_reply(f'{c}: {txt}', user_id=msg.from_user.id) or "haha bata? 😄"
                    await send_mood(app, msg.chat.id, 'determined', out[:1000], reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    # free-API pack: meme/joke/fact/quote/weather/crypto/anime/waifu/neko/word/horoscope/rate/news # NEW
    @app.on_message(filters.command(["meme", "joke", "fact", "quote", "weather", "crypto",
                                     "anime", "waifu", "neko", "cat", "dog", "wallpaper", "word", "horoscope",
                                     "rate", "news", "rps", "guess"]))
    async def apipack_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            c = msg.command[0]
            arg = ' '.join(msg.command[1:])
            if c == 'meme':
                d = await api_json('https://meme-api.com/gimme')
                if d and d.get('url'):
                    try: return await msg.reply_photo(d['url'], caption=f"😂 {d.get('title','')[:100]}")
                    except Exception: pass
                await msg.reply('ᴍᴇᴍᴇ ꜰᴀɪʟᴇᴅ 💀', parse_mode=enums.ParseMode.HTML)
            elif c == 'joke':
                d = await api_json('https://official-joke-api.appspot.com/random_joke')
                if d and d.get('setup'):
                    setup, punch = d.get('setup', '...'), d.get('punchline', '...')
                else:  # fallback: jokeapi.dev
                    j = await api_json('https://v2.jokeapi.dev/joke/Any?type=single&safe-mode')
                    setup = (j or {}).get('joke', '...') if j and not j.get('error') else '...'
                    punch = '😂'
                await send_mood(app, msg.chat.id, 'laughing', hcard('ᴊᴏᴋᴇ', [('😂', 'ꜱᴇᴛᴜᴩ', setup[:400]), ('🤣', 'ᴩᴜɴᴄʜ', punch[:400])]), reply_to_id=msg.id)
            elif c == 'fact':
                d = await api_json('https://uselessfacts.jsph.pl/api/v2/facts/random')
                await send_mood(app, msg.chat.id, 'peaceful', hcard('ꜰᴀᴄᴛ', [('🧠', 'ᴅɪᴅ ʏᴏᴜ ᴋɴᴏᴡ', (d or {}).get('text', '...')[:500])]), reply_to_id=msg.id)
            elif c == 'quote':
                d = await api_json('https://zenquotes.io/api/random')
                q = (d or [{}])[0] if isinstance(d, list) else {}
                if not q.get('q'):  # fallback: dummyjson
                    j = await api_json('https://dummyjson.com/quotes/random')
                    q = {'q': (j or {}).get('quote', '...'), 'a': (j or {}).get('author', '?')}
                await send_mood(app, msg.chat.id, 'peaceful', hcard('Qᴜᴏᴛᴇ', [('💬', 'ᴛᴇxᴛ', q.get('q', '...')[:400]), ('✍️', 'ʙʏ', q.get('a', '?'))]), reply_to_id=msg.id)
            elif c == 'weather':
                if not arg: return await msg.reply(err_wrong('/weather <city>'), parse_mode=enums.ParseMode.HTML)
                d = await api_json(f'https://wttr.in/{urllib.parse.quote(arg)}?format=j1')
                try:
                    cur = d['current_condition'][0]
                    await send_mood(app, msg.chat.id, 'cute_smile', hcard('ᴡᴇᴀᴛʜᴇʀ', [('🌡️', 'ᴛᴇᴍᴩ', cur['temp_C']+'°C'), ('☁️', 'ᴄᴏɴᴅ', cur['weatherDesc'][0]['value']), ('💧', 'ʜᴜᴍ', cur['humidity']+'%')]), reply_to_id=msg.id)
                except Exception: await msg.reply('ᴡᴇᴀᴛʜᴇʀ ꜰᴀɪʟᴇᴅ 💀', parse_mode=enums.ParseMode.HTML)
            elif c == 'crypto':
                coin = (arg or 'bitcoin').lower().replace(' ', '-')
                shown, chg, src = None, None, 'coingecko'
                d = await api_json(f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd&include_24hr_change=true')
                try:
                    p = d[coin]
                    shown, chg = f"${p['usd']}", f"{p.get('usd_24h_change', 0):.2f}%"
                except Exception:
                    # fallback: Kraken public ticker (no key, very reliable)
                    pair = {'bitcoin': 'XBTUSD', 'ethereum': 'ETHUSD', 'dogecoin': 'DOGEUSD',
                            'solana': 'SOLUSD', 'xrp': 'XRPUSD', 'cardano': 'ADAUSD'}.get(coin, coin.upper() + 'USD')
                    k = await api_json(f'https://api.kraken.com/0/public/Ticker?pair={pair}')
                    try:
                        info = next(iter((k or {}).get('result', {}).values()))
                        shown, chg = f"${float(info['c'][0]):,.2f}", 'live'
                        src = 'kraken'
                    except Exception:
                        pass
                if shown is None:
                    return await msg.reply('ᴄᴏɪɴ ɴᴏᴛ ꜰᴏᴜɴᴅ 💀 — ᴛʀʏ <code>/crypto bitcoin</code>', parse_mode=enums.ParseMode.HTML)
                await send_mood(app, msg.chat.id, 'curious', hcard('ᴄʀʏᴩᴛᴏ', [('🪙', coin, shown), ('📈', '24ʜ', chg), ('🔗', 'ꜱʀᴄ', src)]), reply_to_id=msg.id)
            elif c == 'anime':
                if not arg: return await msg.reply(err_wrong('/anime <name>'), parse_mode=enums.ParseMode.HTML)
                title = eps = score = syn = poster = status = None
                # Try AniList first (more reliable, has banner images)
                g = await api_post('https://graphql.anilist.co',
                    {"query": "query($s:String){Media(search:$s,type:ANIME){title{romaji english}episodes averageScore description coverImage{large}bannerImage status}}",
                     "variables": {"s": arg[:80]}})
                try:
                    m = g['data']['Media']
                    title = (m['title'].get('english') or m['title'].get('romaji') or '?')[:60]
                    eps = str(m.get('episodes') or '?')
                    sc = m.get('averageScore')
                    score = f"{sc / 10:.1f}" if sc else '?'
                    syn = re.sub(r'<[^>]+>', '', m.get('description') or '')[:300]
                    # Prefer banner (16:9), fallback to cover
                    poster = m.get('bannerImage') or (m.get('coverImage') or {}).get('large')
                    status = m.get('status', '?')
                except Exception:
                    pass
                # Fallback: Jikan
                if not title:
                    d = await api_json(f'https://api.jikan.moe/v4/anime?q={urllib.parse.quote(arg)}&limit=5')
                    try:
                        results = d.get('data', [])
                        best = None
                        arg_lower = arg.lower()
                        for a in results:
                            t = (a.get('title') or '').lower()
                            if arg_lower in t or t in arg_lower:
                                best = a
                                break
                        if not best and results:
                            best = results[0]
                        if best:
                            title = best['title'][:60]
                            eps = str(best.get('episodes', '?'))
                            score = str(best.get('score', '?'))
                            syn = re.sub(r'<[^>]+>', '', (best.get('synopsis') or ''))[:300]
                            poster = best.get('images', {}).get('jpg', {}).get('large_image_url')
                            status = best.get('status', '?')
                    except Exception:
                        pass
                if not title:
                    return await msg.reply('ᴀɴɪᴍᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ 💀', parse_mode=enums.ParseMode.HTML)
                detail = (
                    "<blockquote>"
                    f"✦ ┌─[ 🎬 <b>{title}</b> ]\n"
                    f"│\n"
                    f"├─ 📺 Episodes: <code>{eps}</code>\n"
                    f"├─ ⭐ Score: <code>{score}</code>\n"
                    f"├─ 📊 Status: <code>{status or '?'}</code>\n"
                    f"│\n"
                    f"├─ 📝 Synopsis:\n"
                    f"│  <i>{syn or 'N/A'}</i>\n"
                    f"│\n"
                    f"└─ 🎬 <i>enjoy~</i>\n"
                    "</blockquote>"
                )
                if poster:
                    try:
                        await msg.reply_photo(poster, caption=detail, parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        await msg.reply(detail, parse_mode=enums.ParseMode.HTML)
                else:
                    await msg.reply(detail, parse_mode=enums.ParseMode.HTML)
            elif c in ('waifu', 'neko'):
                # PRIMARY: nekos.best (waifu.pics DNS is dead) — verified 200 live
                d = await api_json(f'https://nekos.best/api/v2/{c}')
                url = ((d or {}).get('results') or [{}])[0].get('url')
                if not url:
                    d3 = await api_json('https://api.nekosapi.com/v4/images/random?rating=safe&limit=1')
                    try:
                        url = d3[0].get('url')
                    except Exception:
                        pass
                if not url:
                    d2 = await api_json(f'https://api.waifu.pics/sfw/{c}')
                    url = (d2 or {}).get('url')
                if url:
                    try:
                        return await msg.reply_photo(url, caption=f'🌸 {c}~', parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        pass
                await msg.reply('ɪᴍᴀɢᴇ ꜰᴀɪʟᴇᴅ 💀 — ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ', parse_mode=enums.ParseMode.HTML)
            elif c == 'cat':
                d = await api_json('https://cataas.com/cat?json=true')
                try:
                    url = 'https://cataas.com' + d['url']
                    return await msg.reply_photo(url, caption='🐱 ᴍᴇᴏᴡ~', parse_mode=enums.ParseMode.HTML)
                except Exception:
                    pass
                await msg.reply('ᴄᴀᴛ ꜰᴀɪʟᴇᴅ 💀 — ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ', parse_mode=enums.ParseMode.HTML)
            elif c == 'dog':
                d = await api_json('https://dog.ceo/api/breeds/image/random')
                try:
                    url = d['message']
                    assert url.startswith('http')
                    return await msg.reply_photo(url, caption='🐶 ᴡᴏᴏꜰ~', parse_mode=enums.ParseMode.HTML)
                except Exception:
                    pass
                await msg.reply('ᴅᴏɢ ꜰᴀɪʟᴇᴅ 💀 — ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ', parse_mode=enums.ParseMode.HTML)
            elif c == 'wallpaper':
                # 4K anime wallpapers: konachan.net (SFW) -> safebooru (SFW), HD only
                query = (arg or 'wallpaper').lower().strip()
                presets = {'baddie': 'solo looking_at_viewer', 'cute': 'cat_ears smile',
                           'aesthetic': 'scenery', '4k': 'wallpaper', 'hd': 'wallpaper'}
                tries = [presets.get(query, query or 'wallpaper'), 'wallpaper']
                sent = False
                for tq in tries:
                    tags = urllib.parse.quote(tq.replace(' ', '+'))
                    cands = []
                    d = await api_json(f'https://konachan.net/post.json?limit=20&tags={tags}')
                    try:
                        for p in d or []:
                            if (p.get('width') or 0) >= 1920 and p.get('file_url'):
                                cands.append((p.get('score', 0), p))
                    except Exception:
                        pass
                    if not cands:
                        d2 = await api_json(f'https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1&limit=20&tags={tags}')
                        try:
                            for p in d2 or []:
                                if (p.get('width') or 0) >= 1280 and p.get('file_url'):
                                    cands.append((p.get('score', 0), p))
                        except Exception:
                            pass
                    if cands:
                        cands.sort(key=lambda x: x[0], reverse=True)
                        sc, p = random.choice(cands[:8])
                        url = p['file_url']
                        if url.startswith('//'):
                            url = 'https:' + url
                        info = f"{p.get('width')}x{p.get('height')} · ⭐{sc}"
                        try:
                            await msg.reply_photo(url, caption=f'🌸 <b>ᴡᴀʟʟᴩᴀᴩᴇʀ</b> [{tq}] · {info}', parse_mode=enums.ParseMode.HTML)
                            sent = True
                        except Exception:
                            samp = p.get('sample_url') or p.get('jpeg_url')
                            try:
                                if samp:
                                    if samp.startswith('//'):
                                        samp = 'https:' + samp
                                    await msg.reply_photo(samp, caption=f'🌸 <b>ᴡᴀʟʟᴩᴀᴩᴇʀ</b> [{tq}] · {info} (sample)', parse_mode=enums.ParseMode.HTML)
                                    sent = True
                            except Exception:
                                pass
                    if sent:
                        break
                if not sent:
                    await msg.reply('ᴡᴀʟʟᴩᴀᴩᴇʀ ɴᴀʜɪ ᴍɪʟᴀ 💀 — ᴛʀʏ <code>/wallpaper hatsune_miku</code> or <code>/wallpaper cute</code>', parse_mode=enums.ParseMode.HTML)
            elif c == 'word':
                d = await api_json('https://api.dictionaryapi.dev/api/v2/entries/en/' + (arg or 'serendipity'))
                try:
                    w0 = d[0]; m0 = w0['meanings'][0]['definitions'][0]
                    await send_mood(app, msg.chat.id, 'peaceful', hcard('ᴡᴏʀᴅ', [('📖', w0['word'], m0.get('definition', '')[:300]), ('✏️', 'ᴇx', (m0.get('example') or '-')[:200])]), reply_to_id=msg.id)
                except Exception: await msg.reply('ᴡᴏʀᴅ ɴᴏᴛ ꜰᴏᴜɴᴅ 💀', parse_mode=enums.ParseMode.HTML)
            elif c == 'horoscope':
                sign = (arg or 'aries').lower()
                if sign not in ('aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                                'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'):
                    return await msg.reply(err_wrong('/horoscope <sign> e.g. leo'), parse_mode=enums.ParseMode.HTML)
                txt = None
                d = await api_json(f'https://freehoroscopeapi.com/api/v1/get-horoscope/daily?sign={sign}')
                try:
                    txt = d['data']['horoscope']
                except Exception:
                    c2 = await api_json(f'https://api.cosmyday.com/content/daily/{sign}')
                    try:
                        txt = c2['content']
                    except Exception:
                        pass
                if not txt:
                    return await msg.reply('ʜᴏʀᴏꜱᴄᴏᴩᴇ ꜰᴀɪʟᴇᴅ 💀 — ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ', parse_mode=enums.ParseMode.HTML)
                await send_mood(app, msg.chat.id, 'curious', hcard('ʜᴏʀᴏꜱᴄᴏᴩᴇ', [('🔮', sign, txt[:600])]), reply_to_id=msg.id)
            elif c == 'rate':
                parts = (arg or '').upper().split()
                if len(parts) < 2:
                    return await msg.reply(err_wrong('/rate <FROM> <TO> [amount] e.g. /rate USD INR 100'), parse_mode=enums.ParseMode.HTML)
                frm, to = parts[0], parts[1]
                try:
                    amt = float(parts[2]) if len(parts) > 2 else 1.0
                except Exception:
                    amt = 1.0
                d = await api_json(f'https://open.er-api.com/v6/latest/{frm}')
                try:
                    rate = d['rates'][to]
                    out = rate * amt
                    await send_mood(app, msg.chat.id, 'curious', hcard('ʀᴀᴛᴇ', [('💱', 'ᴩᴀɪʀ', f'{amt:g} {frm} → {to}'), ('✅', 'ᴏᴜᴛ', f'<code>{out:,.2f} {to}</code>'), ('📊', 'ʀᴀᴛᴇ', f'1 {frm} = {rate} {to}')]), reply_to_id=msg.id)
                except Exception:
                    await msg.reply('ʙᴀᴅ ᴄᴜʀʀᴇɴᴄʏ ᴄᴏᴅᴇ 💀 — ᴜꜱᴇ 3-ʟᴇᴛᴛᴇʀ ᴄᴏᴅᴇꜱ ʟɪᴋᴇ USD INR', parse_mode=enums.ParseMode.HTML)
            elif c == 'news':
                topic = arg or 'technology'
                d = await api_json(f'https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(topic)}&tags=story&hitsPerPage=5')
                try:
                    hits = (d or {}).get('hits', [])
                    if not hits:
                        raise ValueError('empty')
                    lines = [f"📰 {h.get('title', '?')[:90]}" for h in hits[:5]]
                    await send_mood(app, msg.chat.id, 'curious', hcard('ɴᴇᴡꜱ', [('🔥', topic[:20], '\n'.join(lines)[:900])]), reply_to_id=msg.id)
                except Exception:
                    await msg.reply('ɴᴏ ɴᴇᴡꜱ ꜰᴏᴜɴᴅ 💀 — ᴛʀʏ ᴀɴᴏᴛʜᴇʀ ᴛᴏᴩɪᴄ', parse_mode=enums.ParseMode.HTML)
            elif c == 'rps':
                if not arg or arg.lower() not in ('rock', 'paper', 'scissors'):
                    return await msg.reply(err_wrong('/rps rock|paper|scissors'), parse_mode=enums.ParseMode.HTML)
                bot = random.choice(['rock', 'paper', 'scissors'])
                win = (arg.lower(), bot) in [('rock', 'scissors'), ('paper', 'rock'), ('scissors', 'paper')]
                draw = arg.lower() == bot
                await ensure_wallet(msg.from_user.id)
                if not draw:
                    await _run("UPDATE wallet SET balance=balance+? WHERE user_id=?", (50 if win else -50, msg.from_user.id))
                await fcard(msg, 'happy' if win else 'sad', 'ʀᴩꜱ', [('🤖', 'ʙᴏᴛ', bot), ('🏆', 'ʀᴇꜱᴜʟᴛ', 'ᴅʀᴀᴡ' if draw else ('ᴡɪɴ +50' if win else 'ʟᴏꜱᴇ -50'))])
            elif c == 'guess':
                await send_mood(app, msg.chat.id, 'curious', hcard('ɢᴜᴇꜱꜱ', [('🎯', 'ɢᴀᴍᴇ', 'I picked 1-100! Reply numbers, 5 tries. (demo)')]), reply_to_id=msg.id)
        except Exception: traceback.print_exc()

    # text fun: colortext/ascii/reverse/mock/emojify/poll/vote/typerace (tictactoe lives in handlers_ttt) # NEW
    @app.on_message(filters.command(["colortext", "ascii", "reverse", "mock", "emojify",
                                     "poll", "vote", "typerace"]))
    async def textfun_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id): return
            c = msg.command[0]
            body = msg.text.split(None, 1)[1] if len(msg.text.split(None, 1)) > 1 else ''
            if c == 'reverse':
                t = (msg.reply_to_message.text if msg.reply_to_message and msg.reply_to_message.text else body)
                await msg.reply(f'<code>{t[::-1][:1000]}</code>', parse_mode=enums.ParseMode.HTML)
            elif c == 'mock':
                t = (msg.reply_to_message.text if msg.reply_to_message and msg.reply_to_message.text else body)
                await msg.reply(''.join(x.upper() if i % 2 else x.lower() for i, x in enumerate(t))[:1000])
            elif c == 'emojify':
                t = (msg.reply_to_message.text if msg.reply_to_message and msg.reply_to_message.text else body)
                await msg.reply(' ✨ '.join(t.split())[:1000] + ' ✨')
            elif c == 'colortext':
                await msg.reply(f'<spoiler>{body[:500] or "hi"}</spoiler>', parse_mode=enums.ParseMode.HTML)
            elif c == 'ascii':
                await msg.reply(f'<pre>{body[:30] or "RIRURU"}\n████ 🌸 ████</pre>', parse_mode=enums.ParseMode.HTML)
            elif c == 'poll':
                parts = [p.strip() for p in body.split('|')]
                if len(parts) < 3: return await msg.reply(err_wrong('/poll Q | opt1 | opt2'), parse_mode=enums.ParseMode.HTML)
                from src.compat import InlineKeyboardMarkup, IKB as InlineKeyboardButton
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(f'{o[:20]} (0)', callback_data=f'pollx_{i}', style="primary") for i, o in enumerate(parts[1:4])]])
                await msg.reply(f'📊 <b>{parts[0][:200]}</b>', reply_markup=kb, parse_mode=enums.ParseMode.HTML)
            elif c == 'vote':
                await msg.reply('🗳️ Vote noted! Results in 60s (demo) ✅', parse_mode=enums.ParseMode.HTML)
            elif c == 'typerace':
                s = random.choice(['Riruru is the cutest bot ever', 'Type fast to win coins now', 'Hinglish typing race go go'])
                await msg.reply(hcard('ᴛʏᴩᴇʀᴀᴄᴇ', [('⌨️', 'ᴛʏᴩᴇ', f'<code>{s}</code>'), ('🏆', 'ᴩʀɪᴢᴇ', '300')]), parse_mode=enums.ParseMode.HTML)
            else:  # tictactoe
                from src.compat import InlineKeyboardMarkup, IKB as InlineKeyboardButton
                kb = InlineKeyboardMarkup([[InlineKeyboardButton('⬜', callback_data=f'ttt_{i}', style="primary") for i in range(r, r+3)] for r in (0, 3, 6)])
                await msg.reply('⭕ TicTacToe — X starts! (demo board)', reply_markup=kb, parse_mode=enums.ParseMode.HTML)
        except Exception: traceback.print_exc()
