from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB_NAME = "careconnect.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            location TEXT,
            points INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            skills TEXT NOT NULL,
            availability TEXT NOT NULL,
            description TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            needed_skills TEXT NOT NULL,
            urgency TEXT NOT NULL,
            description TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def login_required():
    return "user_id" in session


def calculate_match_score(offer, help_request):
    score = 0

    offer_skills = [s.strip().lower() for s in offer["skills"].split(",")]
    request_skills = [s.strip().lower() for s in help_request["needed_skills"].split(",")]

    matched_skills = set(offer_skills).intersection(set(request_skills))

    if matched_skills:
        score += len(matched_skills) * 25

    if offer["category"].lower() == help_request["category"].lower():
        score += 30

    if help_request["urgency"].lower() == "high":
        score += 10

    if offer["availability"].lower() in ["weekend", "flexible"]:
        score += 10

    return min(score, 100), list(matched_skills)


@app.route("/")
def index():
    conn = get_db()

    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_offers = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    total_requests = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_users=total_users,
        total_offers=total_offers,
        total_requests=total_requests
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        location = request.form["location"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            conn.execute(
                """
                INSERT INTO users (name, email, password, location, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    password,
                    location,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            conn.commit()
            conn.close()

            flash("Account created successfully. Please login.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    offers = conn.execute(
        "SELECT * FROM offers WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    requests_list = conn.execute(
        "SELECT * FROM requests WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    badge = "Starter"

    if user["points"] >= 50:
        badge = "Community Helper"

    if user["points"] >= 100:
        badge = "Impact Maker"

    return render_template(
        "dashboard.html",
        user=user,
        offers=offers,
        requests=requests_list,
        badge=badge
    )


@app.route("/add-offer", methods=["GET", "POST"])
def add_offer():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        conn = get_db()

        conn.execute(
            """
            INSERT INTO offers 
            (user_id, title, category, skills, availability, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                request.form["title"],
                request.form["category"],
                request.form["skills"],
                request.form["availability"],
                request.form["description"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.execute(
            "UPDATE users SET points = points + 10 WHERE id = ?",
            (session["user_id"],)
        )

        conn.commit()
        conn.close()

        flash("Offer added successfully. You earned 10 points.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_offer.html")


@app.route("/add-request", methods=["GET", "POST"])
def add_request():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        conn = get_db()

        conn.execute(
            """
            INSERT INTO requests
            (user_id, title, category, needed_skills, urgency, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                request.form["title"],
                request.form["category"],
                request.form["needed_skills"],
                request.form["urgency"],
                request.form["description"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

        flash("Help request added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_request.html")


@app.route("/matches")
def matches():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()

    offers = conn.execute(
        """
        SELECT offers.*, users.name, users.location
        FROM offers
        JOIN users ON offers.user_id = users.id
        ORDER BY offers.id DESC
        """
    ).fetchall()

    requests_list = conn.execute(
        """
        SELECT requests.*, users.name, users.location
        FROM requests
        JOIN users ON requests.user_id = users.id
        ORDER BY requests.id DESC
        """
    ).fetchall()

    conn.close()

    match_results = []

    for help_request in requests_list:
        for offer in offers:
            if offer["user_id"] != help_request["user_id"]:
                score, matched_skills = calculate_match_score(offer, help_request)

                if score >= 30:
                    match_results.append({
                        "request": help_request,
                        "offer": offer,
                        "score": score,
                        "matched_skills": matched_skills
                    })

    match_results = sorted(
        match_results,
        key=lambda x: x["score"],
        reverse=True
    )

    return render_template("matches.html", match_results=match_results)


# Important for deployment:
# This initializes the SQLite database when the app is loaded by Render/Gunicorn.
init_db()


if __name__ == "__main__":
    app.run(debug=True)
