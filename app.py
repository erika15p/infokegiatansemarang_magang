from flask import Flask, render_template, request, redirect, session
from flask import jsonify, redirect
from db import get_db
from kalender_api import tambah_event as kegiatan
from kalender_api import ambil_event_kalender
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "infokegiatan-secret"

UPLOAD_FOLDER = "static/file_uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def index():
    keyword = request.args.get("q")

    db = get_db()
    cur = db.cursor(dictionary=True)

    if keyword:
        cur.execute(
            "SELECT * FROM kegiatan WHERE nama_kegiatan LIKE %s",
            ("%" + keyword + "%",)
        )
    else:
        cur.execute("SELECT * FROM kegiatan")

    data = cur.fetchall()
    return render_template("index.html", data=data, keyword=keyword)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s AND role='admin'",
            (username, password)
        )
        admin = cur.fetchone()

        if admin:
            session["admin"] = admin["id_user"]
            return redirect("/admin")
        else:
            return render_template("login.html", error="Username atau password salah")

    return render_template("login.html")

@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM kegiatan")
    data = cur.fetchall()
    return render_template("admin.html", data=data)

@app.route("/tambah", methods=["POST"])
def tambah():
    if "admin" not in session:
        return redirect("/login")

    nama = request.form.get("nama")
    tanggal = request.form.get("tanggal")
    waktu = request.form.get("waktu")
    lokasi = request.form.get("lokasi")
    deskripsi = request.form.get("deskripsi")

    file = request.files.get("gambar")
    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    event_id = kegiatan(nama, deskripsi, tanggal, lokasi)
    
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO kegiatan (nama_kegiatan, tanggal, waktu, lokasi, deskripsi, calendar_event_id, gambar) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (nama, tanggal, waktu, lokasi, deskripsi, event_id, filename)
    )
    db.commit()

    return redirect("/admin")

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    if "admin" not in session:
        return redirect("/login")

    nama = request.form.get("nama")
    tanggal = request.form.get("tanggal")
    lokasi = request.form.get("lokasi")
    waktu = request.form.get("waktu")
    deskripsi = request.form.get("deskripsi")
    file = request.files.get("gambar")

    db = get_db()
    cur = db.cursor()

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur.execute("""
            UPDATE kegiatan
            SET nama_kegiatan=%s, tanggal=%s, waktu=%s, lokasi=%s, deskripsi=%s, gambar=%s
            WHERE id_kegiatan=%s
        """, (nama, tanggal, waktu, lokasi, deskripsi, filename, id))
    else:
        cur.execute("""
            UPDATE kegiatan
            SET nama_kegiatan=%s, tanggal=%s, waktu=%s, lokasi=%s, deskripsi=%s
            WHERE id_kegiatan=%s
        """, (nama, tanggal, waktu, lokasi, deskripsi, id))

    db.commit()
    return redirect("/admin")

@app.route("/hapus/<int:id>", methods=["POST"])
def hapus(id):
    if "admin" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM kegiatan WHERE id_kegiatan=%s", (id,))
    db.commit()

    return redirect("/admin")

@app.route("/kalender")
def kalender():
    return render_template("kalender.html")

@app.route("/api/kegiatan")
def api_kegiatan():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT id_kegiatan, nama_kegiatan, tanggal, waktu, lokasi, deskripsi
        FROM kegiatan
    """)

    data = cur.fetchall()

    events = []
    for k in data:
        events.append({
            "id": k["id_kegiatan"],
            "title": k["nama_kegiatan"],
            "start": str(k["tanggal"]),
            "time": k["waktu"],
            "extendedProps": {
                "location": k["lokasi"],
                "description": k["deskripsi"]
            },
            "url": f"/kegiatan/{k['id_kegiatan']}"
        })

    return jsonify(events)

@app.route("/api/kegiatan/<int:id>")
def get_kegiatan(id):
    if "admin" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM kegiatan WHERE id_kegiatan=%s", (id,))
    data = cur.fetchone()

    if not data:
        return jsonify({"error": "Data tidak ditemukan"}), 404

    return jsonify(data)

@app.route("/api/list_kegiatan")
def list_kegiatan():
    keyword = request.args.get("keyword", "")

    db = get_db()
    cur = db.cursor(dictionary=True)

    if keyword:
        cur.execute("""
            SELECT * FROM kegiatan
            WHERE nama_kegiatan LIKE %s
            OR deskripsi LIKE %s
            OR lokasi LIKE %s
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    else:
        cur.execute("SELECT * FROM kegiatan")

    data = cur.fetchall()
    return jsonify(data)

@app.route("/kegiatan/<int:id>")
def detail_kegiatan(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT * FROM kegiatan WHERE id_kegiatan=%s", (id,))
    kegiatan = cur.fetchone()

    if not kegiatan:
        return "Kegiatan tidak ditemukan"

    return render_template("detail_kegiatan.html", kegiatan=kegiatan)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

def sinkron_kalender_ke_db():
    events = ambil_event_kalender()
    db = get_db()
    cur = db.cursor(dictionary=True)

    for e in events:
        event_id = e['id']
        nama = e.get('summary', '')
        deskripsi = e.get('description', '')
        lokasi = e.get('location', '')
        tanggal = e['start'].get('date')
        waktu = e['start'].get('time', '')

        cur.execute(
            "SELECT id FROM kegiatan WHERE calendar_event_id=%s",
            (event_id,)
        )

        if not cur.fetchone():
            cur.execute(
                """INSERT INTO kegiatan
                (nama_kegiatan, tanggal, waktu, lokasi, deskripsi, calendar_event_id)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (nama, tanggal, waktu, lokasi, deskripsi, event_id)
            )
            db.commit()

if __name__ == "__main__":
    app.run(debug=True)
