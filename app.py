from flask import Flask, render_template, request, redirect, session
from db import get_db

app = Flask(__name__)
app.secret_key = "infokegiatan-secret"

@app.route("/")
def index():
    keyword = request.args.get("q")  # ambil kata kunci pencarian

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
    deskripsi = request.form.get("deskripsi")
    tanggal = request.form.get("tanggal")
    lokasi = request.form.get("lokasi")

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO kegiatan (nama_kegiatan, deskripsi, tanggal, lokasi) VALUES (%s, %s, %s, %s)",
        (nama, deskripsi, tanggal, lokasi)
    )
    db.commit()

    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
