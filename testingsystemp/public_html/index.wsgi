import os
import sys

sys.path.append('/path/to/env/lib/python3.10/site-packages/')
sys.path.insert(0, '/path/to/testingsystemp/public_html/')

import json
import threading
import datetime as dt
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.utils import secure_filename

from users import USERS
from testlib import evaluate

app = Flask(__name__)
app.secret_key = "super-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"py", "cpp"}

TASKS = {
    "compress_string": {
        "description": """Напишите программу, которая при вводе любого набора символов, будет их сжимать. Например: 
Ввод: AABCCCDE 
Вывод: 2AB3CDE;

Ввод: ABBBBBBDGGE 
Вывод: A6BD2GE
""",
        "languages": ["py"],
    },
    "date_format_converter": {
        "description": """Напишите функцию, которая конвертирует дату в формате ДД/ММ/ГГГГ в ГГГГММДД.
Ввод: 22/02/2024
Вывод: 20240222
""",
        "languages": ["py"],
    },
    "math_expression": {
        "description": """Запрограммируйте математическое выражение (а + b - f / a) + f * а * а - (a + b)
Ввод: 1 2 3
Вывод: 0
""",
        "languages": ["cpp"],
    },
    "pow_manual": {
        "description": """
        Возведите число x в степень n не используя pow.
Ввод: 2(enter)3
Вывод: 8

        """,
        "languages": ["cpp"],
    },
    "permute_n": {
        "description": """Напишите алгоритм, выдающий без повторений все перестановки N чисел (на python). Категория: олимпиадное программирование.
Ввод: 3
Вывод (например, но программа воспринимает только в таком формате, так что лучше сделайте так, как она ее поймет): [(1, 2, 3), (1, 3, 2), (2, 1, 3), (2, 3, 1), (3, 1, 2), (3, 2, 1)] 
""",
        "languages": ["py"],
    },
}

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "submissions.json")
lock = threading.Lock()

def load_submissions():
    if not os.path.exists(SUBMISSIONS_FILE):
        return
    with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            for username, submissions in data.items():
                user = USERS.get(username)
                if not user:
                    continue
                user["submissions"] = []
                for sub in submissions:
                    # Преобразуем строку обратно в datetime
                    sub["timestamp"] = dt.datetime.fromisoformat(sub["timestamp"])
                    user["submissions"].append(sub)
            print(f"[LOAD_SUBMISSIONS] Загружено данных о отправках из {SUBMISSIONS_FILE}")
        except Exception as e:
            print(f"[LOAD_SUBMISSIONS] Ошибка при загрузке: {e}")

def save_submissions():
    with lock:
        data = {}
        for username, user in USERS.items():
            subs = user.get("submissions", [])
            data[username] = []
            for sub in subs:
                sub_copy = sub.copy()
                if isinstance(sub_copy.get("timestamp"), dt.datetime):
                    sub_copy["timestamp"] = sub_copy["timestamp"].isoformat()
                data[username].append(sub_copy)
        try:
            with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[SAVE_SUBMISSIONS] Данные об отправках сохранены в {SUBMISSIONS_FILE}")
        except Exception as e:
            print(f"[SAVE_SUBMISSIONS] Ошибка при сохранении: {e}")

load_submissions()

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Пожалуйста, войдите в систему.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

@app.route("/")
@login_required
def index():
    return render_template("index.html", tasks=TASKS, USERS=USERS)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = USERS.get(username)
        if user and user["password"] == password:
            session["user"] = username
            print(f"[LOGIN] Пользователь вошёл: {username}")
            return redirect(url_for("index"))
        flash("Неверный логин или пароль.")
    return render_template("login.html", tasks=TASKS, USERS=USERS)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/task/<task_id>")
@login_required
def task_detail(task_id):
    task = TASKS.get(task_id)
    if not task:
        return "Задача не найдена", 404

    user = USERS.get(session["user"])
    submissions = [
        s for s in user.get("submissions", []) if s["task_id"] == task_id
    ]

    return render_template(
        "task.html",
        task=task,
        task_id=task_id,
        USERS=USERS,
        submissions=submissions
    )

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload/<task_id>", methods=["POST"])
@login_required
def upload(task_id):
    task = TASKS.get(task_id)
    if not task:
        flash("Задача не найдена.")
        return redirect(url_for("index"))

    file = request.files.get("solution")
    if not file or file.filename == "":
        flash("Файл не выбран.")
        return redirect(url_for("task_detail", task_id=task_id))

    if not allowed_file(file.filename):
        flash("Недопустимое расширение файла.")
        return redirect(url_for("task_detail", task_id=task_id))

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in task["languages"]:
        flash(f"Эта задача не поддерживает язык {ext}.")
        return redirect(url_for("task_detail", task_id=task_id))

    save_path = os.path.join(UPLOAD_DIR, f"{session['user']}_{task_id}_{dt.datetime.now().timestamp()}.{ext}")
    file.save(save_path)

    result = evaluate(task_id, save_path)

    USERS[session["user"]].setdefault("submissions", []).append({
        "task_id": task_id,
        "filepath": save_path,
        "result": result,
        "timestamp": dt.datetime.now(),
    })

    save_submissions()

    return redirect(url_for("task_detail", task_id=task_id))

@app.route("/admin")
@login_required
def admin():
    user = USERS.get(session["user"])
    if not user or not user.get("is_admin"):
        return "Доступ запрещён", 403

    board = []
    for username, data in USERS.items():
        details = {}
        for sub in data.get("submissions", []):
            task_id = sub["task_id"]
            passed = sub["result"]["passed"]
            total = sub["result"]["total"]
            score = int(passed == total)
            if task_id not in details or score > details[task_id]:
                details[task_id] = score
        board.append({
            "user": username,
            "details": details,
            "total": sum(details.values()),
        })

    return render_template("admin.html", board=board, tasks=TASKS.keys(), USERS=USERS)

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user or not USERS.get(user, {}).get("is_admin"):
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@app.route("/uploads/<path:filename>")
@login_required
def download_file(filename):
    user = USERS.get(session["user"])
    if not user or not user.get("is_admin"):
        return "Доступ запрещён", 403
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

_application = app

def application(environ, start_response):
    environ['SCRIPT_NAME'] = "/"
    return _application(environ, start_response)

if __name__ == "__main__":
    app.run(debug=True)
