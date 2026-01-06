from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_cors import CORS
import sqlite3, os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return sqlite3.connect("database.db")

def ensure_table():
    """Ensure the players table exists before every database operation"""
    db = get_db()
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        uid TEXT,
        screenshot TEXT,
        status TEXT
    )
    """)
    db.commit()
    db.close()

@app.route("/uploads/<filename>")
def uploads(filename):
    """Serve uploaded files from the uploads folder"""
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route("/register", methods=["POST"])
def register():
    ensure_table()
    name = request.form["name"]
    uid = request.form["uid"]
    screenshot = request.files["screenshot"]
    
    filename = f"{uid}_{screenshot.filename}"
    screenshot.save(os.path.join(UPLOAD_FOLDER, filename))
    
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO players VALUES (NULL, ?, ?, ?, ?)",
        (name, uid, filename, "Pending")
    )
    db.commit()
    db.close()
    return "Registration submitted successfully. Wait for admin approval."

@app.route("/admin")
def admin():
    ensure_table()
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM players")
    players = cur.fetchall()
    db.close()
    return render_template("admin.html", players=players)

@app.route("/approve/<int:id>")
def approve(id):
    ensure_table()
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE players SET status='Approved' WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect(url_for("admin"))

@app.route("/status", methods=["GET", "POST"])
def status():
    ensure_table()
    if request.method == "POST":
        name = request.form["name"]
        uid = request.form["uid"]
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT status FROM players WHERE name=? AND uid=?", (name, uid))
        result = cur.fetchone()
        db.close()
        if result:
            return f"<h1>Status: {result[0]}</h1>"
        else:
            return "<h1>Registration not found</h1>"
    return render_template("status.html")

if __name__ == "__main__":
    app.run(debug=False)
