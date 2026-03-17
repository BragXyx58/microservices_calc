from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import redis
from database import get_connection

redis_client = redis.Redis(
    host="redis",
    port=6379,
    password="redis123",
    decode_responses=True
)

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        if self.path == "/calculate":
            self.calculate(data)

    def calculate(self, data):
        session_token = data["session_token"]
        user_id = redis_client.get(f"session:{session_token}")

        if not user_id:
            self.respond(401, {"error": "invalid session"})
            return

        try:
            allowed = "0123456789+-*/(). "
            expression = data["expression"]

            if any(ch not in allowed for ch in expression):
                self.respond(400, {"error": "invalid expression"})
                return

            result = str(eval(expression))

        except Exception as e:
            self.respond(400, {"error": str(e)})
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO History (UserId, Expression, Result) VALUES (?, ?, ?)",
            int(user_id),
            data["expression"],
            result
        )

        conn.commit()
        conn.close()

        redis_client.delete(f"history:{user_id}")

        self.respond(200, {"result": result})

    def respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
server.serve_forever()