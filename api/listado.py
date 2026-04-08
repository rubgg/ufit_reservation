import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

TARGET_URL = os.environ.get("TARGET_URL", "")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
CLIENT_ID  = os.environ.get("CLIENT_ID", "")


class handler(BaseHTTPRequestHandler):

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if not TARGET_URL or not CLIENT_ID:
            self._respond(500, {"error": "TARGET_URL o CLIENT_ID no configurados"})
            return

        url = f"{TARGET_URL}/listado_reservas_cliente/{CLIENT_ID}"

        req = urllib.request.Request(
            url,
            data=b"",
            method="POST",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
            reservas = json.loads(content)
            self._respond(200, {"ok": True, "reservas": reservas})
        except urllib.error.HTTPError as e:
            self._respond(e.code, {"ok": False, "error": e.read().decode("utf-8", errors="replace")})
        except Exception as e:
            self._respond(502, {"ok": False, "error": str(e)})

    def _respond(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)