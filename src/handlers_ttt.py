#!/usr/bin/env python3
"""TicTacToe: challenge+accept PvP and vs-bot mode + poll votes. # NEW
/tictactoe (reply) -> opponent must Accept -> X (challenger) starts
/tictactoe bot     -> instant game vs Riruru (win > block > center > corner > random)
"""
import asyncio
import random
import traceback

TTT_GAMES: dict = {}   # gid "chatid_msgid" -> {p1, p2|BOT, board, turn, msg_id, chat_id}
TTT_WINS = ((0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6))


def _winner(b):
    for a, c, d in TTT_WINS:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    return None


def _bot_move(b):
    me, op = "O", "X"
    for i in range(9):
        if not b[i]:
            b[i] = me
            if _winner(b) == me:
                b[i] = ""
                return i
            b[i] = ""
    for i in range(9):
        if not b[i]:
            b[i] = op
            if _winner(b) == op:
                b[i] = ""
                return i
            b[i] = ""
    if not b[4]:
        return 4
    corners = [i for i in (0, 2, 6, 8) if not b[i]]
    if corners:
        return random.choice(corners)
    free = [i for i in range(9) if not b[i]]
    return random.choice(free) if free else -1


def register(app, bert=None):
    from src.compat import filters, enums, IKB as InlineKeyboardButton, InlineKeyboardMarkup
    import riruru as R
    from src.utils import ff, hcard, mention_html, flood_ok, err_wrong
    from src.media import cached_gif

    def _board_kb(gid, board, over=False):
        emo = {"X": "❌", "O": "⭕", "": "⬜"}
        rows = []
        for r in range(3):
            row = []
            for c in range(3):
                i = r * 3 + c
                if over or board[i]:
                    row.append(InlineKeyboardButton(emo[board[i]], callback_data="ttt_noop", style="primary"))
                else:
                    row.append(InlineKeyboardButton(emo[""], callback_data=f"ttt_move_{gid}_{i}", style="primary"))
            rows.append(row)
        return InlineKeyboardMarkup(rows)

    async def _expire(gid, delay=300):
        await asyncio.sleep(delay)
        g = TTT_GAMES.pop(gid, None)
        if g:
            try:
                await app.edit_message_text(g["chat_id"], g["msg_id"], "⌛ TicTacToe expired — /tictactoe to play again~")
            except Exception:
                pass

    def _render(g):
        b = g["board"]
        w = _winner(b)
        p1m = g["p1m"]
        p2m = g["p2m"]
        if w:
            who = p1m if w == "X" else p2m
            return f"🏆 <b>{ff('Game Over')}</b> — {who} wins! {w}"
        if all(b):
            return f"🤝 <b>{ff('Draw')}</b> — nobody wins~"
        cur = p1m if g["turn"] == "X" else p2m
        return (f"⭕ <b>{ff('TicTacToe')}</b> {p1m} (❌) vs {p2m} (⭕)\n"
                f"👉 Turn: {cur} ({g['turn']})")

    @app.on_message(filters.command("tictactoe"))
    async def ttt_h(_, msg):
        try:
            if await R._maint_block(msg):
                return
            if not flood_ok(msg.from_user.id):
                return
            await R.ensure_user(msg.from_user.id, msg.from_user.username, msg.from_user.first_name)
            args = [a.lower() for a in msg.command[1:]]
            me_m = mention_html(msg.from_user.id, msg.from_user.first_name)
            if args and args[0] == "bot":
                board = [""] * 9
                m = await msg.reply(
                    f"⭕ <b>{ff('TicTacToe')}</b> {me_m} (❌) vs Riruru (⭕)\n👉 Your move — tap a tile!",
                    reply_markup=_board_kb("pending", board), parse_mode=enums.ParseMode.HTML)
                gid = f"{msg.chat.id}_{m.id}"
                TTT_GAMES[gid] = {"p1": msg.from_user.id, "p2": "BOT", "p1m": me_m,
                                  "p2m": "Riruru 🌸", "board": board, "turn": "X",
                                  "turn_x_is_p1": True, "chat_id": msg.chat.id, "msg_id": m.id}
                try:
                    await m.edit_reply_markup(_board_kb(gid, board))
                except Exception:
                    pass
                asyncio.create_task(_expire(gid))
                return
            t = msg.reply_to_message.from_user if msg.reply_to_message else None
            if not t:
                return await msg.reply(err_wrong('/tictactoe (reply to a friend) or /tictactoe bot'),
                                       parse_mode=enums.ParseMode.HTML)
            if t.id == msg.from_user.id:
                return await msg.reply('ᴋʜᴜᴅ ꜱᴇ ɴᴀʜɪ~ ᴜꜱᴇ <code>/tictactoe bot</code> 🙈',
                                       parse_mode=enums.ParseMode.HTML)
            if t.is_bot:
                return await msg.reply('ᴜꜱᴇ <code>/tictactoe bot</code> ᴛᴏ ᴩʟᴀʏ ᴍᴇ~ 🌸',
                                       parse_mode=enums.ParseMode.HTML)
            await R.ensure_user(t.id, t.username, t.first_name)
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Accept", callback_data=f"ttt_ch_{msg.chat.id}_{msg.id}", style="success"),
                 InlineKeyboardButton("❌ Decline", callback_data=f"ttt_dec_{msg.chat.id}_{msg.id}", style="danger")],
            ])
            m = await msg.reply(
                f"🎮 {me_m} challenges {mention_html(t.id, t.first_name)} to <b>TicTacToe</b>!\n"
                f"{mention_html(t.id, t.first_name)}, accept?",
                reply_markup=kb, parse_mode=enums.ParseMode.HTML)
            TTT_GAMES[f"ch_{msg.chat.id}_{msg.id}"] = {
                "p1": msg.from_user.id, "p2": t.id, "p1m": me_m,
                "p2m": mention_html(t.id, t.first_name),
                "chall_msg": m.id, "chat_id": msg.chat.id, "pending": True}
            asyncio.create_task(_expire(f"ch_{msg.chat.id}_{msg.id}", 120))
        except Exception:
            traceback.print_exc()

    @app.on_callback_query(filters.regex(r"^ttt_(ch|dec)_(-?\d+)_(\d+)$"))
    async def ttt_challenge_cb(_, cq):
        try:
            act, cid, mid = cq.data.split("_")[1], int(cq.data.split("_")[2]), int(cq.data.split("_")[3])
            key = f"ch_{cid}_{mid}"
            g = TTT_GAMES.get(key)
            if not g:
                return await cq.answer("Challenge expired~ /tictactoe to play again", show_alert=True)
            if cq.from_user.id != g["p2"]:
                return await cq.answer("Only the challenged player answers 🙈", show_alert=True)
            await cq.answer()
            if act == "dec":
                TTT_GAMES.pop(key, None)
                try:
                    await cq.edit_message_text(f"💔 {g['p2m']} declined the duel~", parse_mode=enums.ParseMode.HTML)
                except Exception:
                    pass
                return
            # accepted -> live board, challenger (X) starts
            TTT_GAMES.pop(key, None)
            board = [""] * 9
            gid = f"{cid}_{g['chall_msg']}"
            TTT_GAMES[gid] = {"p1": g["p1"], "p2": g["p2"], "p1m": g["p1m"], "p2m": g["p2m"],
                              "board": board, "turn": "X", "turn_x_is_p1": True,
                              "chat_id": cid, "msg_id": g["chall_msg"]}
            try:
                await cq.edit_message_text(_render(TTT_GAMES[gid]),
                                           reply_markup=_board_kb(gid, board),
                                           parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
            asyncio.create_task(_expire(gid))
        except Exception:
            try:
                await cq.answer()
            except Exception:
                pass

    @app.on_callback_query(filters.regex(r"^ttt_move_(.+)_(\d+)$"))
    async def ttt_move_cb(_, cq):
        try:
            # gid itself contains '_' (negative chat ids) -> strip prefix, split tail idx
            tail = cq.data[len("ttt_move_"):]
            gid, idx_s = tail.rsplit("_", 1)
            idx = int(idx_s)
            g = TTT_GAMES.get(gid)
            if not g or g.get("pending"):
                return await cq.answer("Game over or expired~ /tictactoe", show_alert=True)
            mark = "X" if cq.from_user.id == g["p1"] else ("O" if cq.from_user.id == g["p2"] else None)
            if mark is None:
                return await cq.answer("Spectators can't move 🙈", show_alert=True)
            if g["turn"] != mark:
                return await cq.answer("Not your turn ⏳", show_alert=True)
            if not 0 <= idx < 9 or g["board"][idx]:
                return await cq.answer("Tile taken~ 🟦", show_alert=True)
            await cq.answer()
            g["board"][idx] = mark
            w = _winner(g["board"])
            if w or all(g["board"]):
                TTT_GAMES.pop(gid, None)
                try:
                    await R.record_game(g["p1"] if w == "X" else g["p2"], "tictactoe", bool(w))
                except Exception:
                    pass
                gif = await cached_gif("happy" if w else "sad")
                txt = _render(g)
                try:
                    if gif:
                        await cq.edit_message_text(txt, reply_markup=_board_kb(gid, g["board"], over=True),
                                                   parse_mode=enums.ParseMode.HTML)
                    else:
                        raise RuntimeError("no gif")
                except Exception:
                    try:
                        await cq.edit_message_text(txt, reply_markup=_board_kb(gid, g["board"], over=True),
                                                   parse_mode=enums.ParseMode.HTML)
                    except Exception:
                        pass
                return
            g["turn"] = "O" if mark == "X" else "X"
            # bot reply move
            if g["p2"] == "BOT" and g["turn"] == "O":
                await asyncio.sleep(1)
                bi = _bot_move(g["board"])
                if bi >= 0:
                    g["board"][bi] = "O"
                    w2 = _winner(g["board"])
                    if w2 or all(g["board"]):
                        TTT_GAMES.pop(gid, None)
                        try:
                            await R.record_game(g["p1"], "tictactoe", False)
                        except Exception:
                            pass
                        try:
                            await cq.edit_message_text(_render(g), reply_markup=_board_kb(gid, g["board"], over=True),
                                                       parse_mode=enums.ParseMode.HTML)
                        except Exception:
                            pass
                        return
                    g["turn"] = "X"
            try:
                await cq.edit_message_text(_render(g), reply_markup=_board_kb(gid, g["board"]),
                                           parse_mode=enums.ParseMode.HTML)
            except Exception:
                pass
        except Exception:
            try:
                await cq.answer()
            except Exception:
                pass

    @app.on_callback_query(filters.regex(r"^ttt_noop$"))
    async def ttt_noop_cb(_, cq):
        try:
            await cq.answer("Game over~ /tictactoe for a new one 🌸")
        except Exception:
            pass

    # dead-button fix: poll votes tally
    _POLLS: dict = {}

    @app.on_callback_query(filters.regex(r"^pollx_(\d+)$"))
    async def pollx_cb(_, cq):
        try:
            idx = int(cq.data.split("_")[1])
            key = (cq.message.chat.id, cq.message.id) if cq.message and cq.message.chat else (0, 0)
            p = _POLLS.get(key, {})
            if cq.from_user.id in p.get("voters", set()):
                return await cq.answer("Already voted ✅")
            p.setdefault("tally", {})[idx] = p.setdefault("tally", {}).get(idx, 0) + 1
            p.setdefault("voters", set()).add(cq.from_user.id)
            _POLLS[key] = p
            await cq.answer(f"Voted ✅ ({sum(p['tally'].values())} total)")
        except Exception:
            try:
                await cq.answer()
            except Exception:
                pass
