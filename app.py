"""
calw_test - Simple Login Website
A minimal Flask-based login system.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import functools

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
