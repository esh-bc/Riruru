# AGENT.md — Riruru Bot v2 Handbook

Read this FIRST before touching anything. It exists because every rule
below cost us a real debugging session in v1.

## What this is

Telegram bot **@riruruuu_bot** — economy, casino games, group moderation,
AI chat (Groq), anime utilities, admin panel. ~9,400 lines.
Live on Render (owns the token); this machine is dev only.

## Stack facts (non-negotiable)

- **Kittygram, NOT Pyrogram.** It's a Pyrogram fork (Bot API 9.4+).
  ALL new code imports from `src/compat.py` (`filters, enums, IKB`,
  `InlineKeyboardMarkup`, ...). Never import pyrogram directly.
- **DB is Turso libSQL**, via an `aiosqlite.connect` monkeypatch
  (`connect_db` in riruru.py). Write normal aiosqlite code; it just works.
- Secrets live in **`.env`** (gitignored, auto-loaded at import).
  Code defaults must be empty for secrets. GitHub push protection
  REJECTS partner-pattern secrets (bot tokens, `gsk_` keys) — never commit them.
- Handler decorator `group=N` is **priority order, NOT chat type**.
  Chat-type filtering is `filters.group` / `filters.private`.

## Gotchas that already bit us

1. **Kittygram statuses are enums, not strings.**
   `me.status == "administrator"` is ALWAYS False.
   Use `getattr(me.status, "value", str(me.status))`.
2. **BytesIO uploads need `.name`.** Kittygram silently drops
   in-memory files without it: `buf.name = "x.png"`.
3. **Telegram `file_id`s are bot-specific.** New bot token ⇒ re-upload
   every hardcoded file (hero video, etc.) to mint fresh IDs.
4. **Stale `.session` file locks bot identity.** After ANY token change:
   delete `riruru_bot.session*` or the old bot keeps logging in.
5. **`send_mood()` swallows ALL exceptions and forces HTML parse mode.**
   Never pass Markdown (`**`, backticks) — use `<b>`, `<code>`.
   It also takes `**kwargs` (absorbs `parse_mode=` from callers).
6. **Two coin purses exist — don't mix them.**
   `users.coins` = daily/work/casino. `wallet.balance/bank` = kill/rob/bal.
   AI user-context must report both.
7. **`users` table has NO `is_premium` column.** Premium lives in
   `protection.is_premium`. Use `is_premium_admin_view()`.
8. **Edit tool does substring matching.** A short `oldString` can match
   INSIDE another line and mangle the file (happened in `group_msg`).
   Always anchor edits with long, unique context.
9. **Never `pkill -f` with a pattern in your own command line** —
   the shell matches itself and dies. Kill by exact PID scan via
   `/proc` (match `argv[:3] == ['python3','-u','riruru.py']`), excluding self.
10. **One poller per token.** Local + Render on the same token = 409
    conflicts and flapping. Whoever owns the token runs; the other stays DOWN.
11. **The 359-test harness uses a FakeApp** — it never executes
    riruru.py decorators or live API paths. Green harness ≠ working bot.
    Always verify against the live log + real Bot API calls.
12. **Background processes die silently here.** After any reboot, confirm
    the process exists AND the log shows LIVE. `run_bot.sh` auto-restarts
    on crash, but nothing restarts the runner itself.
13. **New admin/command handlers**: register inside `main()` (loop running,
    before `app.start()`), use `group=1`, wrap everything in try/except,
    add `_maint_block(msg)` gate as first line (ADMINS bypass).
14. **Callback data ≤ 64 bytes.** Keep `adm_*` payloads tiny.
15. **`filters.user(ADMINS)`** restricts to admins. `ADMINS` includes owner
    + `ADMIN_IDS` env. Never let non-admins reach `adm_` callbacks.

## File map

- `riruru.py` (~5.5k lines) — everything core: config, AI, commands,
  admin panel, callbacks. TOO BIG — v2 should split it (see your_opinion.md).
- `src/handlers_*.py` — economy / powers / social / utility / games /
  dotmod (.ban/.mute/…) / ttt. Each has `register(app)`, imports
  `riruru as R` INSIDE register (circular-import guard — keep it).
- `src/{compat,utils,db_extra,media,images,workers}.py` — shared layers.
- `assets/faces/` — 50 mood PNGs (auto-downloaded on boot if missing).
- `run_bot.sh` — crash-loop runner. `.env` — secrets. Both local-only.

## Deploy / reboot ritual (every time, in order)

1. `python3 -m py_compile` changed files.
2. `python3 /tmp/opencode/harness.py` → expect **359 passed, 0 failed**.
3. Kill old PIDs (exact /proc scan, never pkill patterns).
4. `rm -f /tmp/opencode/riruru_test.log`, launch runner detached.
5. Wait ~55s, confirm: `AI keys`, `Bot : @riruruuu_bot`, `LIVE`, zero Tracebacks.
6. Confirm the RUNNING process env/token matches the intended bot.
7. `git add -A && git commit && git push origin main` (token via
   `http.extraHeader`, never in remote URL or files).

## Owner context

- Owner ID `8189708860`, in `ADMINS` always. Talk to them via Bot API
  sendMessage when something needs eyes on Telegram.
- House style: `ff()` fancy font on display text, blockquote tree cards
  (`✦ ┌─[` / `├─` / `└─`), HTML parse mode everywhere, face-mood photos
  on result cards, TEXT-ONLY for AI chat replies, anime GIFs kept for
  /kiss /hug /slap /punch /bite /murder /love /look.
- Language: user speaks Hinglish, short messages. Match energy, stay brief.
