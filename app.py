from flask import Flask, request, render_template, redirect, url_for
import sqlite3, os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return sqlite3.connect("database.db")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    uid = request.form["uid"]
    screenshot = request.files["screenshot"]

    filename = f"{uid}_{screenshot.filename}"
    screenshot.save(os.path.join(UPLOAD_FOLDER, filename))

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
    cur.execute(
        "INSERT INTO players VALUES (NULL, ?, ?, ?, ?)",
        (name, uid, filename, "Pending")
    )
    db.commit()
    db.close()

    return "Registration submitted successfully. Wait for admin approval."

@app.route("/admin")
def admin():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM players")
    players = cur.fetchall()
    db.close()
    return render_template("admin.html", players=players)

@app.route("/approve/<int:id>")
def approve(id):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE players SET status='Approved' WHERE id=?", (id,))
    db.commit()
    db.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run()
