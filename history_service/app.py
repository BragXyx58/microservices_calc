from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from database import get_connection

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        history = []
        try:
            from urllib.parse import urlparse, parse_qs

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
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "User not found"}).encode())
                    return

                user_id = user_row[0]

                cursor.execute(
                    "SELECT Id, Expression, Result, CreatedAt FROM History WHERE UserId = ? ORDER BY CreatedAt ASC",
                    user_id
                )

                rows = cursor.fetchall()

                for r in rows:
                    history.append({
                        "id": r[0],
                        "expression": r[1],
                        "result": r[2],
                        "created_at": str(r[3])[:19]
                    })

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(history).encode())

        except Exception as e:
            print("ERROR GET /history:", e)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

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
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "User not found"}).encode())
                    return

                user_id = user_row[0]

                cursor.execute(
                    "INSERT INTO History (UserId, Expression, Result) VALUES (?, ?, ?)",
                    user_id,
                    data["operation"],
                    data["result"]
                )

                conn.commit()
                self.send_response(200)
                self.end_headers()


            elif self.path == "/rollback":
                cursor.execute(
                    "SELECT Result, Expression FROM History WHERE Id = ?",
                    data["id"]
                )
                row = cursor.fetchone()
                if not row:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Operation not found"}).encode())
                    return
                result = row[0]
                expression = row[1]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "result": result,
                    "expression": expression
                }).encode())

        except Exception as e:
            print("ERROR POST:", e)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("History service running on port 8000...")
server.serve_forever()