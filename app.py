from models.user import create_user, get_user_by_email
from flask import Flask, render_template, request
from flask import redirect, url_for, session
from flask import session, redirect
import sqlite3


app = Flask(__name__)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

DATABASE = "database.db"


def get_db_connection():
    """
    Creates and returns a database connection.
    """
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection




@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/student/payment", methods=["GET", "POST"])
def student_payment():
    if "user_id" not in session or session["role"] != "student":
        return redirect("/login")

    if request.method == "POST":
        amount = request.form["amount"]
        proof = request.form["proof"]
        student_id = session["user_id"]

        connection = get_db_connection()
        cursor = connection.cursor()

        # Save payment
        cursor.execute(
            "INSERT INTO payments (student_id, amount, proof) VALUES (?, ?, ?)",
            (student_id, amount, proof)
        )

        # Generate queue number
        cursor.execute("SELECT MAX(queue_number) FROM queue")
        last_queue = cursor.fetchone()[0]

        if last_queue is None:
            queue_number = 1
        else:
            queue_number = last_queue + 1

        # Save queue number
        cursor.execute(
            "INSERT INTO queue (student_id, queue_number) VALUES (?, ?)",
            (student_id, queue_number)
        )

        connection.commit()
        connection.close()

        return f"Payment successful! Your queue number is {queue_number}"

    return render_template("student_payment.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    # Access control
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT 
        payments.id AS payment_id,
        users.name,
        payments.amount,
        payments.proof,
        payments.status,
        IFNULL(queue.queue_number, '-') AS queue_number
    FROM payments
    JOIN users ON payments.student_id = users.id
    LEFT JOIN queue ON queue.student_id = users.id
""")


    payments = cursor.fetchall()
    connection.close()

    return render_template("admin_dashboard.html", payments=payments)

@app.route("/admin/approve/<int:payment_id>")
def approve_payment(payment_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE payments SET status = 'approved' WHERE id = ?",
        (payment_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/admin/dashboard")


@app.route("/admin/reject/<int:payment_id>")
def reject_payment(payment_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE payments SET status = 'rejected' WHERE id = ?",
        (payment_id,)
    )

    connection.commit()
    connection.close()

    return redirect("/admin/dashboard")

@app.route("/student/status")
def student_status():
    if "user_id" not in session or session["role"] != "student":
        return redirect("/login")

    student_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT payments.status,
               queue.queue_number
        FROM payments
        LEFT JOIN queue ON queue.student_id = payments.student_id
        WHERE payments.student_id = ?
        ORDER BY payments.id DESC
        LIMIT 1
    """, (student_id,))

    result = cursor.fetchone()
    connection.close()

    return render_template("student_status.html", result=result)


def create_tables():
    """
    Creates database tables if they do not exist.
    """
    connection = get_db_connection()
    cursor = connection.cursor()

    # Users table (students & admins)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
""")


    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            proof TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    # Queue table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            queue_number INTEGER NOT NULL
        )
    """)

    connection.commit()
    connection.close()
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        create_user(name, email, password, role)
        return redirect("/login")

    return render_template("register.html")

from flask import redirect, session

app.secret_key = "rqms_secret_key"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()
        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin/dashboard")
            else:
                return redirect("/student/dashboard")

        return "Invalid login"

    return render_template("login.html")

@app.route("/student/dashboard")
def student_dashboard():
    return render_template("student_dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)

