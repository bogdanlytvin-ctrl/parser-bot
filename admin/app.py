import os, sys, time, secrets, functools
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, redirect, url_for, session, flash
import database as db

app = Flask(__name__)
app.secret_key = os.getenv("ADMIN_SECRET_KEY", "change-me")

ADMIN_USER     = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

_attempts: dict[str, list[float]] = {}
_counter = 0


def _rate_limited(ip: str) -> bool:
    global _counter
    now = time.time()
    _counter += 1
    if _counter > 300:
        stale = [k for k, v in _attempts.items() if not any(t for t in v if now-t < 60)]
        for k in stale: del _attempts[k]
        _counter = 0
    a = [t for t in _attempts.get(ip, []) if now-t < 60]
    _attempts[ip] = a
    if len(a) >= 5: return True
    _attempts[ip].append(now)
    return False


def login_required(f):
    @functools.wraps(f)
    def d(*a, **kw):
        if not session.get("ok"): return redirect(url_for("login"))
        return f(*a, **kw)
    return d


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        t = secrets.token_hex(32)
        session["csrf"] = t
        return render_template("login.html", csrf_token=t)
    ip = request.remote_addr or "x"
    if _rate_limited(ip):
        flash("Забагато спроб.")
        return render_template("login.html", csrf_token=session.get("csrf","")), 429
    ft = request.form.get("csrf_token","")
    st = session.pop("csrf","")
    if not st or not secrets.compare_digest(ft, st):
        flash("Недійсний запит.")
        t = secrets.token_hex(32); session["csrf"] = t
        return render_template("login.html", csrf_token=t), 403
    u = secrets.compare_digest(request.form.get("username",""), ADMIN_USER)
    p = secrets.compare_digest(request.form.get("password",""), ADMIN_PASSWORD)
    if u and p:
        session["ok"] = True
        return redirect(url_for("dashboard"))
    flash("Невірний логін або пароль")
    t = secrets.token_hex(32); session["csrf"] = t
    return render_template("login.html", csrf_token=t)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    stats = db.get_stats()
    with db.get_conn() as conn:
        recent_tasks = conn.execute("""
            SELECT t.*, u.first_name, u.username,
                   (SELECT COUNT(*) FROM results r WHERE r.task_id=t.id) as results_count
            FROM tasks t JOIN users u ON u.id=t.user_id
            ORDER BY t.created_at DESC LIMIT 10
        """).fetchall()
        recent_results = conn.execute("""
            SELECT r.*, t.name as task_name, t.source_type
            FROM results r JOIN tasks t ON t.id=r.task_id
            ORDER BY r.sent_at DESC LIMIT 15
        """).fetchall()
    return render_template("dashboard.html",
                           stats=stats, recent_tasks=recent_tasks,
                           recent_results=recent_results)


@app.route("/tasks")
@login_required
def tasks():
    page = max(1, request.args.get("page", 1, type=int))
    per  = 25; offset = (page-1)*per
    with db.get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        rows  = conn.execute("""
            SELECT t.*, u.first_name, u.username,
                   (SELECT COUNT(*) FROM results r WHERE r.task_id=t.id) as results_count
            FROM tasks t JOIN users u ON u.id=t.user_id
            ORDER BY t.created_at DESC LIMIT ? OFFSET ?
        """, (per, offset)).fetchall()
    return render_template("tasks.html", tasks=rows, page=page, total=total, per_page=per)


@app.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id):
    with db.get_conn() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not task:
            flash("Задача не знайдена"); return redirect(url_for("tasks"))
        results = conn.execute(
            "SELECT * FROM results WHERE task_id=? ORDER BY sent_at DESC LIMIT 30",
            (task_id,)
        ).fetchall()
    return render_template("task_detail.html", task=task, results=results)


@app.route("/users")
@login_required
def users():
    page = max(1, request.args.get("page", 1, type=int))
    per  = 25; offset = (page-1)*per
    with db.get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        rows  = conn.execute("""
            SELECT u.*,
                   (SELECT COUNT(*) FROM tasks t WHERE t.user_id=u.id) as tasks_count,
                   (SELECT COUNT(*) FROM tasks t WHERE t.user_id=u.id AND t.is_active=1) as active_count
            FROM users u ORDER BY u.created_at DESC LIMIT ? OFFSET ?
        """, (per, offset)).fetchall()
    return render_template("users.html", users=rows, page=page, total=total, per_page=per)


if __name__ == "__main__":
    db.init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("ADMIN_PORT", 5000)), debug=False)
