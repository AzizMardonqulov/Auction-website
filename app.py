from flask import Flask, request, render_template, redirect, session, flash, make_response
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "this_is_secret_key"

UPLOAD_FOLDER = "static/produck"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db_connection():
    """Yangi SQLite ulanishini ochish."""
    con = sqlite3.connect("auksion.db", timeout=10, check_same_thread=False)
    con.row_factory = sqlite3.Row  
    return con


@app.route("/addcar", methods=["GET", "POST"])
def addcar():
    con = get_db_connection()
    cursor = con.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mahsulotlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT NOT NULL,
            narx REAL NOT NULL,
            tavsif TEXT,
            rasm TEXT
        )
    """)
    con.commit()
    if request.method == "GET":
        return render_template("enterCar.html")

    carname = request.form.get("carName")
    carprice = request.form.get("carPrice")
    carabout = request.form.get("carAbout")
    data = request.form.get("data")
    file = request.files.get("image")

    img_url = "/static/produck/default.jpg"
    if file and file.filename:
        filename = file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        img_url = f"/{file_path}"


    cursor.execute(
        "INSERT INTO mahsulotlar (nomi, narx, tavsif, rasm) VALUES (?, ?, ?, ?)",
        (carname, carprice, carabout, img_url),
    )
    con.commit()
    con.close()

    return redirect("/")


@app.route("/", methods=["GET", "POST"])
def home():
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM mahsulotlar")
    produkts = cursor.fetchall()
    con.close()
    userr = session.get("user_id", "Log In")
    if "user_id" in session:
        return render_template("index.html", produkts=produkts, log=userr)
    
    return redirect("/login")    



@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        flash("Siz allaqachon logindan o'tgansiz")
        return redirect("/")

    if request.method == "GET":
        return render_template("login.html")

    foydalanuvchilar = request.form.get("email")
    password = request.form.get("password")

    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute(
        "SELECT * FROM foydalanuvchilar WHERE foydalanuvchi_nomi = ? AND parol = ?",
        (foydalanuvchilar, password),
    )
    row = cursor.fetchone()
    con.close()

    if row:
        session["user_id"] = foydalanuvchilar
        return redirect("/")
    else:
        flash("No'to'gri foydalanuvchi nomi yoki parol")
        return render_template("unfound.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    foydalanuvchi_nomi = request.form.get("email")
    parol = request.form.get("password")

    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO foydalanuvchilar (foydalanuvchi_nomi, parol) VALUES (?, ?)",
        (foydalanuvchi_nomi, parol),
    )
    con.commit()
    con.close()

    return redirect("/")


@app.route("/log-out")
def logout():
    session.pop("user_id", None)
    flash("Siz tizimdan chiqdingiz")
    return redirect("/")


@app.route("/tarif/<int:id>")
def tarif(id):
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM mahsulotlar WHERE id = ?", (id,))
    produkt = cursor.fetchone()  

    if produkt:
        produkt_narx = produkt[2]
        if produkt_narx is None:
            produkt_narx = 0  
        else:
            produkt_narx = int(produkt_narx) 
    else:
        produkt_narx = 0 

    con.close()

    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM takliflar WHERE id = ?", (id,))
    tariflar = cursor.fetchall()
    con.close()

    return render_template("tarif.html", produkts=[produkt], tariflar=tariflar)




@app.route("/page/<int:id>", methods=["POST", "GET"])
def taklifend(id):
    id = int(id)
    if request.method == "GET":
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT * FROM mahsulotlar WHERE id = ?", (id,))
        row = cursor.fetchone()
        con.close()

        if row is None:
            return render_template("page.html", eror="Mahsulot topilmadi!")

        return render_template("page.html", produkts=[row])

    userr = session.get("user_id", "Log In")
    if not userr:
        return redirect("/login")

    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM mahsulotlar WHERE id = ?", (id,))
    row = cursor.fetchone()
    kir_narx = request.form.get("pur")

    if row is None:
        con.close()
        return render_template("page.html", eror="Mahsulot topilmadi!")

    idIn = row[0]
    foy_nomi = userr
    max_nomi = row[1]
    purce = row[2]  #
    if purce is None:
        con.close()
        return render_template("page.html", produkts=[row], eror="Iltimos, qiymat kiriting!")

    try:
        purce = int(purce)
        if purce <= 0:
            con.close()
            return render_template("page.html", produkts=[row], eror="Ko'proq pul kiriting!")
    except ValueError:
        con.close()
        return render_template("page.html", produkts=[row], eror="Narx faqat raqam bo‘lishi kerak!")
    if int(kir_narx) <= int(purce) :
        con.close()
        return render_template("page.html", produkts=[row], eror="Ko'proq pul kiriting!")
    cursor.execute(
        "INSERT INTO takliflar( id ,foydalanuvchi_nomi, max_nomi, kir_narx) VALUES (?,?, ?, ?)",
        (idIn ,foy_nomi, max_nomi, kir_narx),
    )

    con.commit()
    con.close()
    return render_template( "accept.html")


@app.route("/search", methods =["GET", "POST"])
def search():
    query =""
    results =[]

    if request.method =="POST":
        query = request.form.get("q", "").strip().lower()
        
    else:
        query = request.args.get("q", "").strip().lower()

    if query:

        con =sqlite3.connect("auksion.db")
        cursor =con.cursor()

        cursor.execute("SELECT * FROM mahsulotlar WHERE LOWER(nomi) LIKE ?", ('%' + query +'%',))
        results =cursor.fetchall()
        cursor.close()
        con.close()
    return render_template("search.html", products=results, query=query)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render uchun to'g'ri port
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)