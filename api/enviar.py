import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler


TARGET_URL = os.environ.get("TARGET_URL", "")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
CODIGO = os.environ.get("CODIGO", "")


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
        if not TARGET_URL:
            self._respond(500, {"error": "TARGET_URL no configurada"})
            return

        # Read and parse JSON body from frontend
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw)
        except Exception:
            self._respond(400, {"error": "JSON inválido"})
            return

        fecha       = payload.get("fecha", "")
        hora_inicio = payload.get("hora_inicio", "")
        actividad_id = payload.get("actividadId", "")

        # Validate required fields
        if not fecha or not hora_inicio or not actividad_id:
            self._respond(400, {"error": "Faltan campos: fecha, hora_inicio, actividadId"})
            return

        # Calculate hora_fin = hora_inicio + 1 hour
        try:
            t = datetime.strptime(hora_inicio, "%H:%M")
            hora_fin = (t + timedelta(hours=1)).strftime("%H:%M")
        except ValueError:
            self._respond(400, {"error": "Formato de hora inválido. Usa HH:MM"})
            return

        # Build form-encoded body
        form_data = urllib.parse.urlencode({
            "fecha":       fecha,
            "hora_inicio": hora_inicio,
            "hora_fin":    hora_fin,
            "sala": "",
            "actividadId": actividad_id,
            "gimnasioId": 233,
            "clienteId": 59747,
            "tipo": "N",
            "sesiones_restantes": 0,
            "sesiones_restantes_extras": 0,
            "token": {AUTH_TOKEN},
            "flags_token": 1
        })
        body = form_data.encode("utf-8")

        req = urllib.request.Request(
            TARGET_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type":  "application/x-www-form-urlencoded",
                "User-Agent": "Dart/3.9 (dart:io)",
                "Codigo": f"Bearer {CODIGO}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                status  = resp.status
                content = resp.read()
            try:
                server_data = json.loads(content)
            except Exception:
                server_data = {}
            self._respond(status, {
                "ok": True,
                "status": status,
                "hora_fin": hora_fin,
                "mensaje": server_data.get("mensaje", ""),
                "posicion": server_data.get("posicion", ""),
            })

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            self._respond(e.code, {"ok": False, "status": e.code, "detail": error_body})

        except Exception as e:
            self._respond(502, {"ok": False, "error": str(e)})

    def _respond(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
