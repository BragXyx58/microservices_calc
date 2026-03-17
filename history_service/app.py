from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import redis
from urllib.parse import urlparse, parse_qs
from database import get_connection

redis_client = redis.Redis(
    host="redis",
    port=6379,
    password="redis123",
    decode_responses=True
)

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            parsed = urlparse(self.path)

            if parsed.path == "/history":
                params = parse_qs(parsed.query)
                username = params["username"][0]

                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT Id FROM Users WHERE Username = ?",
                    username
                )
                user_row = cursor.fetchone()

                if not user_row:
                    conn.close()
                    self.respond(404, {"error": "User not found"})
                    return

                user_id = user_row[0]

                cached_history = redis_client.get(f"history:{user_id}")
                if cached_history:
                    conn.close()
                    self.respond(200, json.loads(cached_history))
                    return

                cursor.execute(
                    "SELECT Id, Expression, Result, CreatedAt FROM History WHERE UserId = ? ORDER BY CreatedAt ASC",
                    user_id
                )

                rows = cursor.fetchall()
                conn.close()

                history = []
                for r in rows:
                    history.append({
                        "id": r[0],
                        "expression": r[1],
                        "result": r[2],
                        "created_at": str(r[3])[:19]
                    })

                redis_client.setex(
                    f"history:{user_id}",
                    60,
                    json.dumps(history)
                )

                self.respond(200, history)

        except Exception as e:
            print("ERROR GET /history:", e)
            self.respond(500, {"error": str(e)})

    def do_POST(self):
        try:
            length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(length))

            conn = get_connection()
            cursor = conn.cursor()

            if self.path == "/save":
                cursor.execute(
                    "SELECT Id FROM Users WHERE Username = ?",
                    data["username"]
                )
                user_row = cursor.fetchone()

                if not user_row:
                    conn.close()
                    self.respond(404, {"error": "User not found"})
                    return

                user_id = user_row[0]

                cursor.execute(
                    "INSERT INTO History (UserId, Expression, Result) VALUES (?, ?, ?)",
                    user_id,
                    data["operation"],
                    data["result"]
                )

                conn.commit()
                conn.close()

                redis_client.delete(f"history:{user_id}")

                self.respond(200, {"message": "saved"})

            elif self.path == "/rollback":
                cursor.execute(
                    "SELECT UserId, Result, Expression FROM History WHERE Id = ?",
                    data["id"]
                )
                row = cursor.fetchone()
                conn.close()

                if not row:
                    self.respond(404, {"error": "Operation not found"})
                    return

                user_id = row[0]
                result = row[1]
                expression = row[2]

                redis_client.delete(f"history:{user_id}")

                self.respond(200, {
                    "result": result,
                    "expression": expression
                })

        except Exception as e:
            print("ERROR POST:", e)
            self.respond(500, {"error": str(e)})

    def respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("History service running on port 8000...")
server.serve_forever()