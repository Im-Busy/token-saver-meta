"""Dashboard server for token-saver-meta."""

from pathlib import Path
import http.server
import socketserver
import os
import sys


def serve_dashboard(port: int = 8080) -> None:
    """Serve the dashboard HTML on the given port."""
    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"

    if not (dashboard_dir / "index.html").exists():
        print(f"Dashboard not found at {dashboard_dir / 'index.html'}")
        print("Run: token-saver setup to generate dashboard")
        return

    os.chdir(str(dashboard_dir))

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Token Saver Meta Dashboard -> http://localhost:{port}")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    serve_dashboard(port)