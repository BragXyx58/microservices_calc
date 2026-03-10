import tkinter as tk
import requests

AUTH_URL = "http://localhost:8001"
CALC_URL = "http://localhost:8002"
HISTORY_URL = "http://localhost:8003"

session_token = None
current_user = None

def register():
    username = entry_username.get()
    password = entry_password.get()

    requests.post(
        f"{AUTH_URL}/register",
        json={"username": username, "password": password}
    )


def login():
    global session_token, current_user

    username = entry_username.get()
    password = entry_password.get()

    r = requests.post(
        f"{AUTH_URL}/login",
        json={"username": username, "password": password}
    )

    if r.status_code == 200:
        session_token = r.json()["session_token"]
        current_user = username
        open_calculator()



def calculate():
    expression = entry_expression.get()

    r = requests.post(
        f"{CALC_URL}/calculate",
        json={
            "expression": expression,
            "session_token": session_token
        }
    )

    if r.status_code == 200:
        result = r.json()["result"]
        label_result.config(text=result)
        load_history()


def load_history():

    history_list.delete(0, tk.END)

    username = current_user

    r = requests.get(
        f"{HISTORY_URL}/history?username={username}"
    )

    if r.status_code == 200:

        history = r.json()

        for item in history:

            text = f"{item['id']} | {item['created_at']} | {item['expression']} = {item['result']}"

            history_list.insert(tk.END, text)


def rollback():

    selection = history_list.curselection()

    if not selection:
        return

    value = history_list.get(selection[0])

    operation_id = value.split("|")[0].strip()

    r = requests.post(
        f"{HISTORY_URL}/rollback",
        json={"id": operation_id}
    )

    if r.status_code == 200:
        data = r.json()
        result = data["result"]
        expression = data["expression"]
        label_result.config(text=result)
        entry_expression.delete(0, tk.END)
        entry_expression.insert(0, expression)

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

    tk.Label(root, text="History").pack()

    global history_list
    history_list = tk.Listbox(root, width=40)
    history_list.pack()

    tk.Button(root, text="Refresh history", command=load_history).pack()

    tk.Button(root, text="Rollback operation", command=rollback).pack()

    load_history()


root = tk.Tk()
root.title("Microservice Calculator")
root.geometry("400x500")

tk.Label(root, text="Username").pack()

entry_username = tk.Entry(root)
entry_username.pack()

tk.Label(root, text="Password").pack()

entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Register", command=register).pack()

tk.Button(root, text="Login", command=login).pack()

root.mainloop()