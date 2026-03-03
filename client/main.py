import tkinter as tk
import requests

AUTH_URL = "http://localhost:8001"
CALC_URL = "http://localhost:8002"

session_token = None

def register():
    username = entry_username.get()
    password = entry_password.get()
    requests.post(f"{AUTH_URL}/register", json={"username": username, "password": password})

def login():
    global session_token
    username = entry_username.get()
    password = entry_password.get()
    r = requests.post(f"{AUTH_URL}/login", json={"username": username, "password": password})
    if r.status_code == 200:
        session_token = r.json()["session_token"]
        open_calculator()

def calculate():
    expression = entry_expression.get()
    r = requests.post(f"{CALC_URL}/calculate", json={
        "expression": expression,
        "session_token": session_token
    })
    if r.status_code == 200:
        label_result.config(text=r.json()["result"])

def open_calculator():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="Expression").pack()
    global entry_expression
    entry_expression = tk.Entry(root)
    entry_expression.pack()

    tk.Button(root, text="Calculate", command=calculate).pack()

    global label_result
    label_result = tk.Label(root, text="")
    label_result.pack()

root = tk.Tk()
root.title("Microservice Calculator")

tk.Label(root, text="Username").pack()
entry_username = tk.Entry(root)
entry_username.pack()

tk.Label(root, text="Password").pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Register", command=register).pack()
tk.Button(root, text="Login", command=login).pack()

root.mainloop()