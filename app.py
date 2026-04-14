"""
calw_test - Simple Login Website
A minimal Flask-based login and registration system.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import functools
import re

app = Flask(__name__)
app.secret_key = "calw_test_secret_key_2026"

# Simple user database (in-memory for demo)
USERS = {
    "admin": {"password": "admin123", "name": "管理员"},
    "user1": {"password": "user123", "name": "测试用户"},
}


def login_required(f):
    """Login required decorator."""

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def validate_registration(username, password, confirm_password, name):
    """
    Validate registration input.
    Returns (is_valid, error_message).
    """
    if not username or not password or not confirm_password or not name:
        return False, "所有字段都是必填的"

    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度必须在 3-20 个字符之间"

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"

    if len(password) < 6:
        return False, "密码长度不能少于 6 个字符"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', password):
        return False, "密码只能包含字母、数字和下划线"

    if password != confirm_password:
        return False, "两次输入的密码不一致"

    if len(name) > 50:
        return False, "昵称长度不能超过 50 个字符"
    
    if not re.match(r'^[a-zA-Z]+$', name[1]):
        return False, "昵称必须以字母开头"

    if username in USERS:
        return False, "用户名已存在"

    return True, ""


@app.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = USERS.get(username)

        if user and user["password"] == password:
            session["username"] = username
            session["name"] = user["name"]
            flash(f'欢迎回来，{user["name"]}！', "success")
            return redirect(url_for("dashboard"))
        else:
            flash("用户名或密码错误", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        name = request.form.get("name", "").strip()

        is_valid, error = validate_registration(username, password, confirm_password, name)

        if is_valid:
            USERS[username] = {"password": password, "name": name}
            flash(f'注册成功！欢迎 {name}，请登录。', "success")
            return redirect(url_for("login"))
        else:
            flash(error, "danger")

    return render_template("register.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page (requires login)."""
    return render_template(
        "dashboard.html", username=session["username"], name=session["name"]
    )


@app.route("/logout")
def logout():
    """Logout."""
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
