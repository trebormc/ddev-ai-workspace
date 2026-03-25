#!/usr/bin/env python3
"""Desktop notification bridge for DDEV AI containers.

Receives HTTP POST requests from Docker containers and shows desktop
notifications with optional sound on the host machine.

Usage:
    python3 ai-notify-bridge.py [port] [sound_file]

From inside a container:
    curl -s -X POST http://host.docker.internal:5454/notify \
      -H 'Content-Type: application/json' \
      -d '{"title":"Task complete","message":"All done"}'
"""

import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5454
SOUND_FILE = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/sounds/freedesktop/stereo/dialog-information.oga"


class NotificationHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/notify':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                title = data.get('title', 'Notification')
                message = data.get('message', '')

                subprocess.Popen([
                    'notify-send',
                    '--app-name=DDEV AI',
                    '--urgency=normal',
                    title,
                    message
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                subprocess.Popen([
                    'paplay',
                    SOUND_FILE
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                response = {
                    'success': True,
                    'backend': 'notify-send + paplay',
                    'message': 'Notification sent with sound'
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))

                print(f"  Notification: {title} - {message}")

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                print(f"  Error: {e}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/':
            response = {
                'name': 'ddev-ai-notify-bridge',
                'status': 'ok',
                'port': PORT,
                'sound': SOUND_FILE
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', PORT), NotificationHandler)
    print(f'Notification bridge running on http://localhost:{PORT}')
    print(f'Sound: {SOUND_FILE}')
    print(f'Listening for POST /notify ...')
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
        sys.exit(0)
