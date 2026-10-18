"""本地单进程 Web 服务（标准库，无框架依赖）。"""

from __future__ import annotations

import json
import socket
import sys
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from webapp import api  # noqa: E402

HOST = "127.0.0.1"
DEFAULT_PORT = 8770
STATIC = Path(__file__).resolve().parent / "static"
TEMPLATES = Path(__file__).resolve().parent / "templates"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def pick_port(preferred: int = DEFAULT_PORT, limit: int = 30) -> int:
    for port in range(preferred, preferred + limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((HOST, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"端口 {preferred}–{preferred + limit - 1} 均被占用")


class Handler(BaseHTTPRequestHandler):
    server_version = "Qinshu/1.0.0"
    protocol_version = "HTTP/1.1"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, data) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, status: int, code: str, message: str) -> None:
        self._json(status, {"error": {"code": code, "message": message}})

    def _file(self, path: Path) -> None:
        if not path.is_file():
            self._error(404, "not_found", "文件不存在")
            return
        self._send(200, path.read_bytes(), MIME.get(path.suffix, "application/octet-stream"))

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in ("/", "/index.html"):
            self._file(TEMPLATES / "index.html")
        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            target = (STATIC / rel).resolve()
            if STATIC.resolve() not in target.parents:
                self._error(404, "not_found", "文件不存在")
            else:
                self._file(target)
        elif path == "/api/health":
            self._json(200, {"ok": True, "app": "qinshu"})
        elif path == "/api/categories":
            self._json(200, api.categories())
        elif path == "/api/lessons":
            query = parse_qs(urlsplit(self.path).query)
            self._json(200, api.lessons(query))
        elif path.startswith("/api/lessons/"):
            try:
                lesson_id = int(path[len("/api/lessons/"):])
                self._json(200, api.get_lesson(lesson_id))
            except ValueError:
                self._error(400, "invalid_input", "课例 id 必须是整数")
            except KeyError:
                self._error(404, "not_found", "课例不存在")
        elif path == "/api/birds":
            self._json(200, api.bird_list())
        elif path.startswith("/api/birds/"):
            code = unquote(path[len("/api/birds/"):])
            try:
                self._json(200, api.bird_profile(code))
            except KeyError:
                self._error(404, "not_found", "未知禽星")
        else:
            self._error(404, "not_found", "路径不存在")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        try:
            payload = self._body()
            if path == "/api/chart":
                self._json(200, api.chart_from_payload(payload))
            elif path == "/api/guide":
                self._json(200, api.guide_from_payload(payload))
            elif path == "/api/reading":
                self._json(200, api.reading_from_payload(payload))
            elif path == "/api/lessons":
                self._json(200, api.create_lesson(payload))
            else:
                self._error(404, "not_found", "路径不存在")
        except (ValueError, TypeError) as exc:
            self._error(400, "invalid_input", str(exc))
        except KeyError as exc:
            self._error(404, "not_found", str(exc))
        except Exception as exc:
            self._error(500, "internal_error", str(exc))

    def do_PATCH(self) -> None:
        path = urlsplit(self.path).path
        if not path.startswith("/api/lessons/"):
            self._error(404, "not_found", "路径不存在")
            return
        try:
            lesson_id = int(path[len("/api/lessons/"):])
            self._json(200, api.patch_lesson(lesson_id, self._body()))
        except ValueError:
            self._error(400, "invalid_input", "课例 id 必须是整数")
        except KeyError as exc:
            self._error(404, "not_found", str(exc))
        except Exception as exc:
            self._error(500, "internal_error", str(exc))

    def do_DELETE(self) -> None:
        path = urlsplit(self.path).path
        if not path.startswith("/api/lessons/"):
            self._error(404, "not_found", "路径不存在")
            return
        try:
            lesson_id = int(path[len("/api/lessons/"):])
            self._json(200, api.remove_lesson(lesson_id))
        except ValueError:
            self._error(400, "invalid_input", "课例 id 必须是整数")
        except KeyError as exc:
            self._error(404, "not_found", str(exc))
        except Exception as exc:
            self._error(500, "internal_error", str(exc))

    def log_message(self, fmt, *args) -> None:
        sys.stderr.write("[qinshu] " + fmt % args + "\n")


def _already_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/api/health", timeout=0.6) as response:
            return response.status == 200
    except Exception:
        return False


def run(port: int = DEFAULT_PORT, open_browser: bool = True) -> int:
    if _already_running(port):
        url = f"http://{HOST}:{port}/"
        print(f"禽枢已在运行：{url}")
        if open_browser:
            webbrowser.open(url)
        return 0
    real_port = pick_port(port)
    server = QuietServer((HOST, real_port), Handler)
    url = f"http://{HOST}:{real_port}/"
    print("=" * 50)
    print("  禽枢 · 演禽起课器")
    print(f"  {url}")
    print("  Ctrl+C 关闭")
    print("=" * 50)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已关闭")
    finally:
        server.server_close()
    return 0


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        import traceback
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        traceback.print_exception(*sys.exc_info())


def main() -> None:
    raise SystemExit(run())
