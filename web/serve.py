#!/usr/bin/env python3
"""Static server with no-store caching — so edits are always seen on refresh.
Usage: python3 serve.py [port]   (default 8750)
"""
import sys, http.server, socketserver

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8750

class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()
    def log_message(self, *a):
        pass

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), H) as httpd:
    print(f"VARA showcase (no-cache) → http://localhost:{PORT}/")
    httpd.serve_forever()
