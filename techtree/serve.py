"""Serve ui/ and data/ on localhost. Stdlib only."""
import http.server, os, socketserver, webbrowser
from pathlib import Path


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(Path.cwd()), **k)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.path = "/ui/index.html"
        return super().do_GET()

    def log_message(self, *a):
        pass


def run(port: int = 8787, open_browser: bool = True):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        url = f"http://127.0.0.1:{port}/"
        print(f"techtree: serving {url}  (ctrl-c to stop)")
        if open_browser and not os.environ.get("TECHTREE_NO_BROWSER"):
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
