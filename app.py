from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_cors import CORS
import psycopg2
from urllib.parse import urlparse
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    """Connect to PostgreSQL database using DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise Exception("DATABASE_URL environment variable not set")
    
    # Parse DATABASE_URL (format: postgresql://user:password@host:port/dbname)
    parsed = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password,
        port=parsed.port or 5432
    )
    return conn

def ensure_table():
    """Ensure the players table exists before every database operation"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY,
        name TEXT,
        uid TEXT,
        screenshot TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/uploads/<filename>")
def uploads(filename):
    """Serve uploaded files from the uploads folder"""
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route("/register", methods=["POST"])
def register():
    try:
        ensure_table()
        name = request.form["name"]
        uid = request.form["uid"]
        screenshot = request.files["screenshot"]
        
        filename = f"{uid}_{screenshot.filename}"
        screenshot.save(os.path.join(UPLOAD_FOLDER, filename))
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO players (name, uid, screenshot, status) VALUES (%s, %s, %s, %s)",
            (name, uid, filename, "Pending")
        )
        conn.commit()
        cur.close()
        conn.close()
        return "Registration submitted successfully. Wait for admin approval."
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/admin")
def admin():
    try:
        ensure_table()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, uid, screenshot, status FROM players ORDER BY created_at DESC")
        players = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("admin.html", players=players)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/approve/<int:id>")
def approve(id):
    try:
        ensure_table()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE players SET status=%s WHERE id=%s", ("Approved", id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("admin"))
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/status", methods=["GET", "POST"])
def status():
    try:
        ensure_table()
        if request.method == "POST":
            name = request.form["name"]
            uid = request.form["uid"]
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT status FROM players WHERE name=%s AND uid=%s", (name, uid))
            result = cur.fetchone()
            cur.close()
            conn.close()
            if result:
                return f"<h1>Status: {result[0]}</h1>"
            else:
                return "<h1>Registration not found</h1>"
        return render_template("status.html")
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=False)
