"""tuokou HTTP daemon.

A persistent background process that receives translation requests.
Eliminates the cold-start cost of launching a new Python process per keystroke.
"""

import json
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

from .translator import Translator
from .safety import classify, DangerLevel
from .executor import execute

HOST = "127.0.0.1"
PORT = 28630


class TuokouHandler(BaseHTTPRequestHandler):
    """HTTP request handler for translation and execution."""

    translator: Optional[Translator] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/translate":
            self._handle_translate(params)
        elif path == "/execute":
            self._handle_execute(params)
        elif path == "/status":
            self._json({"status": "ok", "version": "0.1.0"})
        else:
            self._json({"error": "not found"}, 404)

    # ---- Routes ----

    def _handle_translate(self, params: dict):
        q = self._get_param(params, "q")
        if not q:
            return self._json({"error": "missing q"}, 400)

        t = self._get_translator()
        command = t.translate(q)
        if not command:
            return self._json({"error": "Translation failed", "command": None, "level": "unknown"})

        level, warning = classify(command)
        level_str = level.value if isinstance(level, DangerLevel) else "unknown"

        output = None
        if level == DangerLevel.READ:
            output = execute(command)

        self._json({
            "command": command,
            "level": level_str,
            "warning": warning or "",
            "output": output or "",
        })

    def _handle_execute(self, params: dict):
        cmd = self._get_param(params, "cmd")
        if not cmd:
            return self._json({"error": "missing cmd"}, 400)

        output = execute(cmd)
        self._json({"output": output or ""})

    # ---- Helpers ----

    def _get_translator(self) -> Translator:
        if TuokouHandler.translator is None:
            TuokouHandler.translator = Translator()
        return TuokouHandler.translator

    def _get_param(self, params: dict, key: str) -> Optional[str]:
        vals = params.get(key)
        if vals and len(vals) > 0:
            return vals[0].strip()
        return None

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


def run_daemon():
    """Start the daemon server."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    server = HTTPServer((HOST, PORT), TuokouHandler)
    server.socket = sock

    if not hasattr(sys, "_called_from_test"):
        print(f"[tuokou] Daemon started: http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


def stop_daemon():
    """Send stop signal to the daemon."""
    import urllib.request

    try:
        req = urllib.request.Request(f"http://{HOST}:{PORT}/status")
        urllib.request.urlopen(req, timeout=3)
        import os
        os._exit(0)
    except Exception:
        pass


def is_running() -> bool:
    """Check if the daemon is currently running."""
    import urllib.request

    try:
        req = urllib.request.Request(f"http://{HOST}:{PORT}/status")
        resp = urllib.request.urlopen(req, timeout=2)
        return resp.status == 200
    except Exception:
        return False