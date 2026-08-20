"""Localhost style server for DSVis.

The DSVis debugger HTML page is a self-contained static file, so the browser
cannot write style config back into the project directory on its own. This
tiny HTTP server (started as a detached process by ``render_debugger``) gives
the page a ``http://127.0.0.1:<port>`` endpoint to persist per-script styles.

Style files live at ``<cwd>/.dsvis/<script-stem>.json`` (the "specific
directory" of DSVis), NOT in the browser's localStorage on C:.

Endpoints
---------
- ``GET  /style?script=avlTree.py``  → ``{"style": <object> | null}``
- ``POST /style``  body ``{"script": "avlTree.py", "style": <object>}`` → 204
- ``GET  /ping`` → 204 (used by render_debugger to reuse a running server)

The server shuts itself down after ``--idle-timeout`` seconds without any
request, so it does not linger on the user's machine forever.
"""

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_IDLE_TIMEOUT_DEFAULT = 1800  # 30 minutes


class StyleHandler(BaseHTTPRequestHandler):
    server_version = "DSVisStyleServer/1.0"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @property
    def style_dir(self) -> Path:
        # Resolve lazily from the server's cwd so the server always writes to
        # the project directory it was launched from.
        return Path.cwd() / ".dsvis"

    def _style_path(self, script: str) -> Path:
        name = Path(script or "").name
        stem = name[:-3] if name.endswith(".py") else name
        if not stem:
            stem = "default"
        return self.style_dir / f"{stem}.json"

    def _query_params(self) -> dict:
        qs = (self.path.split("?", 1)[1] if "?" in self.path else "") or ""
        out = {}
        for pair in qs.split("&"):
            if not pair:
                continue
            k, _, v = pair.partition("=")
            out[k] = v
        return out

    def _touch(self):
        self.server.last_request = time.time()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _reply(self, code: int, obj=None, raw: bytes | None = None):
        if raw is None:
            raw = json.dumps(obj).encode("utf-8") if obj is not None else b""
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self._cors()
        self.end_headers()
        if raw:
            self.wfile.write(raw)

    # ------------------------------------------------------------------
    # HTTP methods
    # ------------------------------------------------------------------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self._touch()
        path = self.path.split("?", 1)[0]
        if path == "/ping":
            self.send_response(204)
            self._cors()
            self.end_headers()
            return
        if path == "/style":
            params = self._query_params()
            p = self._style_path(params.get("script", ""))
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    self._reply(200, {"style": data})
                except Exception:
                    self._reply(200, {"style": None, "error": "unreadable"})
            else:
                self._reply(200, {"style": None})
            return
        if path.startswith("/view/"):
            self._serve_view(path)
            return
        self._reply(404, {"error": "not found"})

    def do_POST(self):
        self._touch()
        path = self.path.split("?", 1)[0]
        if path != "/style":
            self._reply(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            script = body.get("script", "")
            style = body.get("style")
            if style is None:
                self._reply(400, {"error": "missing style"})
                return
            self.style_dir.mkdir(parents=True, exist_ok=True)
            p = self._style_path(script)
            p.write_text(json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8")
            self._reply(200, {"ok": True, "path": str(p)})
        except Exception as e:  # noqa: BLE001
            self._reply(400, {"error": str(e)})

    # ------------------------------------------------------------------
    # View hosting — serve generated debug pages from .dsvis/out/ over http://
    # ------------------------------------------------------------------
    def _view_dir(self) -> Path:
        return Path.cwd() / ".dsvis" / "out"

    @staticmethod
    def _view_name_ok(name: str) -> bool:
        if not name or len(name) > 120:
            return False
        return all(c.isalnum() or c in "._-" for c in name)

    def _serve_view(self, path: str):
        """GET /view/<name> → serve the generated page from .dsvis/out/."""
        name = path[len("/view/"):].strip("/")
        if not self._view_name_ok(name):
            self._reply(404, {"error": "bad name"})
            return
        vdir = self._view_dir()
        target = vdir / name
        try:
            resolved = target.resolve()
            if not str(resolved).startswith(str(vdir.resolve())):
                self._reply(403, {"error": "forbidden"})
                return
            data = resolved.read_bytes()
        except Exception:
            self._reply(404, {"error": "not found"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # keep stdout clean
        pass


class IdleHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, addr, handler, idle_timeout):
        super().__init__(addr, handler)
        self.last_request = time.time()
        self.idle_timeout = idle_timeout
        self._watcher = threading.Thread(target=self._watch, daemon=True)
        self._watcher.start()

    def _watch(self):
        while True:
            time.sleep(10)
            if time.time() - self.last_request > self.idle_timeout:
                threading.Thread(target=self.shutdown, daemon=True).start()
                return


def main(argv=None):
    parser = argparse.ArgumentParser(description="DSVis local style server")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--idle-timeout", type=int, default=_IDLE_TIMEOUT_DEFAULT)
    args = parser.parse_args(argv)

    try:
        server = IdleHTTPServer(("127.0.0.1", args.port), StyleHandler, args.idle_timeout)
    except OSError:
        # Port already in use — another DSVis style server is already running.
        return 0
    print(f"[dsvis] 样式服务已启动 http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
