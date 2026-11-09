#!/usr/bin/env python3
"""Minimal FastAGI bridge for HOID."""

import socketserver


class HOIDHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # Read Asterisk's AGI environment.
        while True:
            line = self.rfile.readline()
            if not line or line in (b"\n", b"\r\n"):
                break

        print("HOID: Incoming FastAGI call", flush=True)

        # Tell Asterisk to play our existing greeting.
        self.wfile.write(
            b"STREAM FILE custom/hoid-greeting \"\"\n"
        )
        self.wfile.flush()

        response = self.rfile.readline().decode().strip()
        print(f"HOID: Asterisk responded: {response}", flush=True)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("127.0.0.1", 4573), HOIDHandler) as server:
        print("HOID FastAGI listening on 127.0.0.1:4573", flush=True)
        server.serve_forever()
