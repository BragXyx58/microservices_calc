from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib
import uuid
from database import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class Handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)

        if self.path == "/register":
            self.register(data)

        elif self.path == "/login":
            self.login(data)

    def register(self, data):
        conn = get_connection()
        cursor = conn.cursor()

        hashed = hash_password(data["password"])

        cursor.execute(
            "INSERT INTO Users (Username, PasswordHash) VALUES (?, ?)",
            data["username"],
            hashed
        )

        conn.commit()
        conn.close()

        self.respond({"message": "registered"})

    def login(self, data):
        conn = get_connection()
        cursor = conn.cursor()

        hashed = hash_password(data["password"])

        cursor.execute(
            "SELECT Id FROM Users WHERE Username=? AND PasswordHash=?",
            data["username"],
            hashed
        )

        row = cursor.fetchone()

        if not row:
            self.respond({"error": "invalid credentials"})
            return

        session_token = str(uuid.uuid4())

        cursor.execute(
            "INSERT INTO Sessions (UserId, SessionToken) VALUES (?, ?)",
            row[0],
            session_token
        )

        conn.commit()
        conn.close()

        self.respond({"session_token": session_token})

    def respond(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

server = HTTPServer(("0.0.0.0", 8000), Handler)
server.serve_forever()