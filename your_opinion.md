# your_opinion.md — builder's retrospective, v1.1.1

Honest notes from the agent that built v1 with the owner, so v2
(built by me or anyone else) doesn't pay for the same lessons twice.

## How v1 went

Genuinely good collaboration: specs arrived in chunks, live testing
caught real bugs fast, and "fix forward" beat "perfect first try".
The bot that shipped — economy, casino, moderation, Groq persona,
admin panel with live API-key rotation — is dense and has a real
identity (blockquote cards + face moods + the Riruru prompt, which
is the best artifact in the repo).

## Problems we faced (each one happened at least once)

1. **Enum-vs-string admin lockout.** Kittygram returns status enums;
   string comparison silently failed CLOSED and blocked every group
   admin from mod commands. Silent boolean bugs are the worst kind —
   no traceback, just "not working".
2. **Ghost image uploads.** Pillow generated perfect images that never
   arrived — Kittygram requires `.name` on BytesIO. The send helper
   swallowed the error, so there was NOTHING in the logs.
3. **Swallowed exceptions as a pattern.** `send_mood` catching everything
   cost hours across three separate incidents. Helpers must log.
4. **Stale session hijack.** New token deployed, old bot kept logging in
   because of `riruru_bot.session`. Diagnosed only via `/proc` env
   inspection. Non-obvious; now documented.
5. **Edit tool substring mangle.** A short match string pasted itself
   into the middle of `group_msg` and broke the anti-abuse block.
   Only caught because compile + harness run every time.
6. **Silent process death.** The bot died twice with zero traceback
   (env reaping/OOM). We only noticed because commands stopped.
   The crash-loop runner fixes crashes, not a dead runner — v2 needs
   a real watchdog or healthcheck that pages someone.
7. **Harness blind spots.** 359 green while the admin panel and new
   handlers were never exercised (FakeApp). A green suite that skips
   new code creates false confidence. New code needs new tests.
8. **Two purses, one name.** `users.coins` vs `wallet.balance` caused
   the AI to quote wrong balances to users. Parallel money systems
   without a single source of truth will keep biting.
9. **Unearnable currency.** `/img` cost credits that no command granted
   — a dead feature behind a paywall with no income. Economy sinks
   need matching faucets, always.
10. **Secrets in code, then in chat.** Tokens and keys lived in source,
    chat history, and shell commands before sanitization. Push
    protection saved the repo; nothing saved the chat log. Rotate on
    a schedule, not after an incident.

## What v2 should do (my actual recommendation)

1. **Split `riruru.py`.** 5,467 lines in one file is the #1 risk.
   `ai.py`, `admin.py`, `commands_*`, `gates.py`. Nothing else matters
   as much as this.
2. **Unify money.** One balance (+bank), one ledger (`transaction_logs`
   already exists — use it for everything).
3. **Commit the harness + extend it.** Every new handler ships with a
   FakeApp test or it doesn't ship.
4. **Structured logging.** Drop `print`-debugging; log handler, user,
   latency, and Groq key index. Half of v1's mysteries would have been
   one grep.
5. **Exception policy.** Helpers return `(ok, value)` or log loudly.
   Bare `except: pass` on a send path is banned.
6. **Staging bot.** Test on a second bot token before touching prod.
   We debugged on live users more than once — it worked, but it's luck,
   not process.
7. **Rotate all v1 secrets at v2 kickoff** (BotFather, Groq x3, Turso,
   GitHub token) since they all appeared in chat/shell history.

## Working style that worked (keep)

- Small chunks, verify each: compile → harness → reboot → live log.
- Owner tests live, reports symptoms; agent diagnoses with evidence
  before theorizing.
- `ff()` font + blockquote cards on everything user-facing.
- No file is "done" until the LIVE log says so.

— Muse Spark, Sep 2026. See you in v2. 🌸
