#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════╗
║   🌸 Riruru Bot — webserver.py                      ║
║   Keeps Render free tier alive via UptimeRobot       ║
╚══════════════════════════════════════════════════════╝

Render spins down free services after 15 min inactivity.
UptimeRobot pings /ping every 5 min → keeps it awake.

Run standalone:  python webserver.py
Run with bot:    started automatically by main.py (PORT env var)
"""

import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8080))  # Render sets PORT automatically
START_TIME = datetime.now(timezone.utc)

# ── Request handler ───────────────────────────────────
class PingHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Silence default HTTP logs (too noisy)
        pass

    def _send(self, code: int, body: str, content_type: str = "text/plain"):
        encoded = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        # ── /ping — UptimeRobot hits this ──────────────
        if path == "/ping":
            self._send(200, "pong 🌸")

        # ── / — simple status page ─────────────────────
        elif path == "/":
            uptime = datetime.now(timezone.utc) - START_TIME
            hours, rem = divmod(int(uptime.total_seconds()), 3600)
            mins, secs = divmod(rem, 60)
            body = (
                "🌸 Riruru Bot\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"Status  : ✅ Online\n"
                f"Uptime  : {hours}h {mins}m {secs}s\n"
                f"Server  : Render free tier\n"
                f"Ping at : /ping\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "Made with 💕 by @iam_esh"
            )
            self._send(200, body)

        # ── 404 for everything else ─────────────────────
        else:
            self._send(404, "not found~")

    # Handle HEAD (UptimeRobot sometimes sends HEAD)
    def do_HEAD(self):
        if self.path.split("?")[0].rstrip("/") in ("/ping", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


# ── Start server ──────────────────────────────────────
def start_webserver():
    """Start HTTP server in a daemon thread — won't block the bot."""
    server = HTTPServer(("0.0.0.0", PORT), PingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"  WebServer: ✅ Listening on port {PORT} — /ping for UptimeRobot")
    return server


if __name__ == "__main__":
    print(f"🌸 Riruru WebServer starting on port {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), PingHandler)
    print(f"✅ Listening — visit http://localhost:{PORT}/ping")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 WebServer stopped~")
        server.server_close()
