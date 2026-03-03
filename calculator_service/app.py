from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from database import get_connection

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        if self.path == "/calculate":
            self.calculate(data)

    def calculate(self, data):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT UserId FROM Sessions WHERE SessionToken=?",
            data["session_token"]
        )

        row = cursor.fetchone()

        if not row:
            self.respond({"error": "invalid session"})
            return

        user_id = row[0]
        result = str(eval(data["expression"]))

        cursor.execute(
            "INSERT INTO History (UserId, Expression, Result) VALUES (?, ?, ?)",
            user_id,
            data["expression"],
            result
        )

        conn.commit()
        conn.close()

        self.respond({"result": result})

    def respond(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
server.serve_forever()