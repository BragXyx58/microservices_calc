from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib
import uuid
import redis
from database import get_connection

redis_client = redis.Redis(
    host="redis",
    port=6379,
    password="redis123",
    decode_responses=True
)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            if self.path == "/register":
                self.register(data)
            elif self.path == "/login":
                self.login(data)
            else:
                self.respond(404, {"error": "not found"})

        except Exception as e:
            print("ERROR do_POST:", e)
            self.respond(500, {"error": str(e)})

    def register(self, data):
        conn = None

        try:
            username = data["username"]
            password = data["password"]

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT Id FROM Users WHERE Username = ?",
                username
            )
            existing_user = cursor.fetchone()

            if existing_user:
                self.respond(409, {"error": "user already exists"})
                return

            hashed = hash_password(password)

            cursor.execute(
                "INSERT INTO Users (Username, PasswordHash) VALUES (?, ?)",
                username,
                hashed
            )

            conn.commit()
            self.respond(200, {"message": "registered"})

        except Exception as e:
            print("ERROR register:", e)
            self.respond(500, {"error": str(e)})

        finally:
            if conn:
                conn.close()

    def login(self, data):
        conn = None

        try:
            username = data["username"]
            password = data["password"]
            hashed = hash_password(password)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT Id FROM Users WHERE Username = ? AND PasswordHash = ?",
                username,
                hashed
            )

            row = cursor.fetchone()

            if not row:
                self.respond(401, {"error": "invalid credentials"})
                return

            user_id = row[0]
            session_token = str(uuid.uuid4())

            redis_client.setex(
                f"session:{session_token}",
                3600,
                user_id
            )

            self.respond(200, {"session_token": session_token})

        except Exception as e:
            print("ERROR login:", e)
            self.respond(500, {"error": str(e)})

        finally:
            if conn:
                conn.close()

    def respond(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
print("Auth service running on port 8000...")
server.serve_forever()