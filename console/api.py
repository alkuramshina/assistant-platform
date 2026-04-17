"""HTTP JSON API for the prototype console."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import db
from .deploy import DeploymentEngine, DeploymentError, Runner
from .models import BotInput, LogInput


class ConsoleAPI(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        db_path: str | Path,
        bot_root: str | Path | None = None,
        runner: Runner | None = None,
    ):
        super().__init__(server_address, ConsoleHandler)
        self.db_path = Path(db_path)
        self.bot_root = Path(bot_root or self.db_path.parent / "bots")
        self.runner = runner


class ConsoleHandler(BaseHTTPRequestHandler):
    server: ConsoleAPI
    static_root = Path(__file__).parent / "static"

    def do_GET(self) -> None:
        try:
            self._handle_get()
        except Exception as exc:  # pragma: no cover - defensive response
            self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        try:
            self._handle_post()
        except ValueError as exc:
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover - defensive response
            self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _handle_get(self) -> None:
        parts = self._path_parts()
        if parts == []:
            self._static_file("index.html")
            return
        if parts and parts[0] == "static":
            self._static_file("/".join(parts[1:]))
            return
        if parts == ["health"]:
            self._json({"ok": True})
            return

        with db.connect(self.server.db_path) as conn:
            if parts == ["api", "bots"]:
                self._json({"bots": db.list_bots(conn)})
                return
            if len(parts) == 3 and parts[:2] == ["api", "bots"]:
                bot = db.get_bot(conn, parts[2])
                self._json_or_404("bot", bot)
                return
            if len(parts) == 4 and parts[:2] == ["api", "bots"] and parts[3] == "logs":
                logs = db.list_logs(conn, parts[2])
                self._json_or_404("logs", {"logs": logs} if logs is not None else None)
                return

        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def _handle_post(self) -> None:
        parts = self._path_parts()
        payload = self._read_json()
        with db.connect(self.server.db_path) as conn:
            if parts == ["api", "bots"]:
                bot = db.create_bot(conn, BotInput.from_payload(payload))
                self._json({"bot": bot}, HTTPStatus.CREATED)
                return
            if len(parts) == 4 and parts[:2] == ["api", "bots"] and parts[3] in {"start", "stop"}:
                bot = db.get_bot(conn, parts[2])
                if bot is None:
                    self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                    return
                try:
                    result = self._deployment().start(bot) if parts[3] == "start" else self._deployment().stop(bot)
                except DeploymentError as exc:
                    self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                bot = db.set_bot_status(conn, parts[2], result["status"])
                self._json_or_404("bot", bot)
                return
            if len(parts) == 4 and parts[:2] == ["api", "bots"] and parts[3] == "logs":
                log = db.add_log(conn, parts[2], LogInput.from_payload(payload))
                self._json_or_404("log", {"log": log} if log is not None else None, HTTPStatus.CREATED)
                return

        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def _path_parts(self) -> list[str]:
        path = urlparse(self.path).path
        return [part for part in path.split("/") if part]

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def _deployment(self) -> DeploymentEngine:
        return DeploymentEngine(self.server.bot_root, self.server.runner)

    def _static_file(self, relative_path: str) -> None:
        if not relative_path:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        target = (self.static_root / unquote(relative_path)).resolve()
        root = self.static_root.resolve()
        if root not in target.parents and target != root:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_or_404(
        self,
        key: str,
        value: object | None,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        if value is None:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if isinstance(value, dict) and key in value:
            self._json(value, status)
        else:
            self._json({key: value}, status)

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(
    db_path: str | Path,
    host: str = "127.0.0.1",
    port: int = 8787,
    bot_root: str | Path | None = None,
) -> None:
    db.connect(db_path).close()
    server = ConsoleAPI((host, port), db_path, bot_root)
    print(f"console API listening on http://{host}:{port}")
    server.serve_forever()
