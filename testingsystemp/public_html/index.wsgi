import os
import sys
import copy

sys.path.append('/path/to/env/lib/python3.10/site-packages/')
sys.path.insert(0, '/path/to/testingsystemp/public_html/')

import json
import threading
import datetime as dt
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, abort
from werkzeug.utils import secure_filename

import testlib
from users import USERS as DEFAULT_USERS
from testlib import evaluate

app = Flask(__name__)
app.secret_key = "super-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"py", "cpp"}

TASK_DESCRIPTIONS = {
    "compress_string": {
        "description": """Напишите программу, которая при вводе любого набора символов будет их сжимать.""",
        "languages": ["py"],
    },
    "date_format_converter": {
        "description": """Напишите функцию, которая конвертирует дату в формате ДД/ММ/ГГГГ в ГГГГММДД.""",
        "languages": ["py"],
    },
    "math_expression": {
        "description": """Запрограммируйте математическое выражение (а + b - f / a) + f * а * а - (a + b).""",
        "languages": ["cpp"],
    },
    "pow_manual": {
        "description": """Возведите число x в степень n, не используя pow.""",
        "languages": ["cpp"],
    },
    "permute_n": {
        "description": """Напишите алгоритм, выдающий без повторений все перестановки N чисел (на python/cpp). Категория: олимпиадное программирование.""",
    },
}

SUBMISSIONS_FILE = os.path.join(BASE_DIR, "submissions.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")
lock = threading.Lock()
USERS = copy.deepcopy(DEFAULT_USERS)
TASKS = {}

def build_default_tasks():
    defaults = {}
    task_ids = set(TASK_DESCRIPTIONS.keys()) | set(testlib.TASKS.keys())
    for task_id in task_ids:
        test_task = testlib.TASKS.get(task_id, {})
        description_task = TASK_DESCRIPTIONS.get(task_id, {})
        defaults[task_id] = {
            "description": description_task.get("description", ""),
            "languages": list(test_task.get("languages", description_task.get("languages", []))),
            "tests": list(test_task.get("tests", [])),
        }
    return defaults

def sync_testlib_tasks():
    testlib.TASKS = {
        task_id: {
            "languages": list(task.get("languages", [])),
            "tests": list(task.get("tests", [])),
        }
        for task_id, task in TASKS.items()
    }

def load_tasks():
    global TASKS
    defaults = build_default_tasks()
    if not os.path.exists(TASKS_FILE):
        TASKS = defaults
        sync_testlib_tasks()
        return
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            loaded = {}
            for task_id, task in data.items():
                if not isinstance(task, dict):
                    continue
                description = task.get("description", "")
                languages = [lang.strip().lower() for lang in task.get("languages", []) if isinstance(lang, str) and lang.strip()]
                tests = []
                for test in task.get("tests", []):
                    if not isinstance(test, dict):
                        continue
                    inp = str(test.get("input", ""))
                    out = str(test.get("output", ""))
                    tests.append({"input": inp, "output": out})
                loaded[task_id] = {
                    "description": str(description),
                    "languages": list(dict.fromkeys(languages)),
                    "tests": tests,
                }
            TASKS = loaded or defaults
    except Exception as e:
        print(f"[LOAD_TASKS] Ошибка при загрузке: {e}")
        TASKS = defaults
    sync_testlib_tasks()

def save_tasks():
    with lock:
        try:
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(TASKS, f, ensure_ascii=False, indent=2)
            print(f"[SAVE_TASKS] Данные о задачах сохранены в {TASKS_FILE}")
        except Exception as e:
            print(f"[SAVE_TASKS] Ошибка при сохранении: {e}")

def load_users():
    global USERS
    if not os.path.exists(USERS_FILE):
        USERS = copy.deepcopy(DEFAULT_USERS)
        return
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded = {}
        for username, user_data in data.items():
            if not isinstance(user_data, dict):
                continue
            loaded[username] = {
                "password": str(user_data.get("password", "")),
                "is_admin": bool(user_data.get("is_admin", False)),
                "submissions": [],
            }
        USERS = loaded or copy.deepcopy(DEFAULT_USERS)
        print(f"[LOAD_USERS] Загружено пользователей из {USERS_FILE}")
    except Exception as e:
        print(f"[LOAD_USERS] Ошибка при загрузке: {e}")
        USERS = copy.deepcopy(DEFAULT_USERS)

def save_users():
    with lock:
        data = {
            username: {
                "password": user_data.get("password", ""),
                "is_admin": bool(user_data.get("is_admin", False)),
            }
            for username, user_data in USERS.items()
        }
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[SAVE_USERS] Данные о пользователях сохранены в {USERS_FILE}")
        except Exception as e:
            print(f"[SAVE_USERS] Ошибка при сохранении: {e}")

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

load_users()
load_tasks()
load_submissions()

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Пожалуйста, войдите в систему.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user or not USERS.get(user, {}).get("is_admin"):
            abort(403)
        return f(*args, **kwargs)
    return wrapper

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

    current_user = USERS.get(session["user"])
    is_admin_user = bool(current_user and current_user.get("is_admin"))
    submissions = [
        s for s in current_user.get("submissions", []) if s["task_id"] == task_id
    ]

    return render_template(
        "task.html",
        task=task,
        task_id=task_id,
        USERS=USERS,
        submissions=submissions,
        is_admin_user=is_admin_user,
        example_limit=2,
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
@admin_required
def admin():
    return render_template("admin.html", USERS=USERS)

@app.route("/admin/results")
@login_required
@admin_required
def admin_results():
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

    return render_template("admin_results.html", board=board, tasks=TASKS.keys(), USERS=USERS)

def parse_languages(raw_languages: str):
    parts = [part.strip().lower() for part in raw_languages.replace(",", " ").split()]
    return list(dict.fromkeys([part for part in parts if part]))

def parse_tests(raw_tests: str):
    tests = []
    for line in raw_tests.splitlines():
        line = line.strip()
        if not line:
            continue
        if "|||" not in line:
            raise ValueError("Неверный формат тестов. Используйте input|||output в каждой строке.")
        inp, out = line.split("|||", 1)
        tests.append({
            "input": inp.replace("\\n", "\n"),
            "output": out.replace("\\n", "\n"),
        })
    return tests

def tests_to_text(tests):
    rows = []
    for case in tests or []:
        if isinstance(case, dict):
            inp = str(case.get("input", ""))
            out = str(case.get("output", ""))
        elif isinstance(case, (list, tuple)) and len(case) >= 2:
            inp = str(case[0])
            out = str(case[1])
        else:
            continue
        rows.append(
            "{}|||{}".format(
                inp.replace("\n", "\\n"),
                out.replace("\n", "\\n"),
            )
        )
    return "\n".join(rows)

@app.route("/admin/tasks")
@login_required
@admin_required
def admin_tasks():
    return render_template("admin_tasks.html", tasks=TASKS, USERS=USERS, tests_to_text=tests_to_text)

@app.route("/admin/tasks/create", methods=["POST"])
@login_required
@admin_required
def create_task():
    task_id = request.form.get("task_id", "").strip()
    description = request.form.get("description", "").strip()
    languages = parse_languages(request.form.get("languages", ""))
    raw_tests = request.form.get("tests", "")

    if not task_id:
        flash("ID задачи обязателен.")
        return redirect(url_for("admin_tasks"))
    if task_id in TASKS:
        flash("Задача с таким ID уже существует.")
        return redirect(url_for("admin_tasks"))
    if not languages:
        flash("Укажите хотя бы один язык.")
        return redirect(url_for("admin_tasks"))

    try:
        tests = parse_tests(raw_tests)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("admin_tasks"))

    TASKS[task_id] = {
        "description": description,
        "languages": languages,
        "tests": tests,
    }
    sync_testlib_tasks()
    save_tasks()
    flash("Задача создана.")
    return redirect(url_for("admin_tasks"))

@app.route("/admin/tasks/<task_id>/update", methods=["POST"])
@login_required
@admin_required
def update_task(task_id):
    task = TASKS.get(task_id)
    if not task:
        flash("Задача не найдена.")
        return redirect(url_for("admin_tasks"))

    description = request.form.get("description", "").strip()
    languages = parse_languages(request.form.get("languages", ""))
    raw_tests = request.form.get("tests", "")

    if not languages:
        flash("Укажите хотя бы один язык.")
        return redirect(url_for("admin_tasks"))

    try:
        tests = parse_tests(raw_tests)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("admin_tasks"))

    task["description"] = description
    task["languages"] = languages
    task["tests"] = tests
    sync_testlib_tasks()
    save_tasks()
    flash("Задача обновлена.")
    return redirect(url_for("admin_tasks"))

@app.route("/admin/tasks/<task_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_task(task_id):
    if task_id not in TASKS:
        flash("Задача не найдена.")
        return redirect(url_for("admin_tasks"))
    del TASKS[task_id]
    sync_testlib_tasks()
    save_tasks()
    flash("Задача удалена.")
    return redirect(url_for("admin_tasks"))

@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    return render_template("admin_users.html", USERS=USERS)

@app.route("/admin/users/create", methods=["POST"])
@login_required
@admin_required
def create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    is_admin = request.form.get("is_admin") == "on"

    if not username or not password:
        flash("Логин и пароль обязательны.")
        return redirect(url_for("admin_users"))
    if username in USERS:
        flash("Пользователь уже существует.")
        return redirect(url_for("admin_users"))

    USERS[username] = {
        "password": password,
        "is_admin": is_admin,
        "submissions": [],
    }
    save_users()
    save_submissions()
    flash("Пользователь создан.")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<username>/update", methods=["POST"])
@login_required
@admin_required
def update_user(username):
    user = USERS.get(username)
    if not user:
        flash("Пользователь не найден.")
        return redirect(url_for("admin_users"))

    password = request.form.get("password", "").strip()
    is_admin = request.form.get("is_admin") == "on"
    if password:
        user["password"] = password
    user["is_admin"] = is_admin
    save_users()
    flash("Пользователь обновлён.")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<username>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(username):
    current = session.get("user")
    if username == current:
        flash("Нельзя удалить текущего пользователя.")
        return redirect(url_for("admin_users"))
    if username not in USERS:
        flash("Пользователь не найден.")
        return redirect(url_for("admin_users"))

    del USERS[username]
    save_users()
    save_submissions()
    flash("Пользователь удалён.")
    return redirect(url_for("admin_users"))

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
