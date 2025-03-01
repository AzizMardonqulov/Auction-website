from flask import Flask, request, render_template, url_for, jsonify, redirect, send_from_directory  , session , flash , make_response
import os
import sqlite3

app = Flask(__name__)
app.secret_key ="this_is_secret_key"


UPLOAD_FOLDER = "static/produck"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# @app.route("/")
# def login():
#     return render_template("index.html")

@app.get("/addcar")
def addcar():
    # carname = request.form.get("carName")
    # carprice = request.form.get("carPrice")
    # carabout = request.form.get("carAbout")

    return render_template("enterCar.html")


@app.post("/addcar" )
def data() :
    carname = request.form.get("carName")
    carprice = request.form.get("carPrice")
    carabout = request.form.get("carAbout")
    data = request.form.get("data")
    file = request.files.get("image") 

    if file and file.filename:
        filename = file.filename
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)    
        img_url = f"/{file_path}" 
    else:
        img_url = "/static/produck/default.jpg"


    con = sqlite3.connect("auksion.db")
    cursor = con.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mahsulotlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT NOT NULL,
            narx REAL NOT NULL,
            tavsif TEXT,
            rasm TEXT
        )""")

    con.commit()

    cursor.execute("INSERT INTO mahsulotlar (nomi, narx, tavsif, data , rasm) VALUES (?, ?, ? , ? , ?)", 
                       (carname, carprice, carabout , data , img_url ))
    con.commit()
    return redirect("/")

@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" in session:
        userr =session.get("user_id")
        con = sqlite3.connect("auksion.db")
        cursor = con.cursor()
    
        cursor.execute("SELECT * FROM mahsulotlar")
        produkts = cursor.fetchall() 
        return render_template("index.html", log=userr , produkts = produkts)
        # return render_template("index.html")
    elif "user_id" not in session:
        con = sqlite3.connect("auksion.db")
        cursor = con.cursor()
        
        cursor.execute("SELECT * FROM mahsulotlar")
        produkts = cursor.fetchall() 

        cursor.close()
        con.close()  
        return render_template("index.html", produkts = produkts , log = "Log In" )
    con = sqlite3.connect("auksion.db")
    cursor = con.cursor()
    
    cursor.execute("SELECT * FROM mahsulotlar")
    produkts = cursor.fetchall() 

    cursor.close()
    con.close()  
    userr =session.get("user_id")
    return render_template("index.html", produkts=produkts , log= "Log In")

@app.route("/page")
def page():
    con = sqlite3.connect("auksion.db")
    cursor = con.cursor()
    
    cursor.execute("SELECT * FROM mahsulotlar")
    produkts = cursor.fetchall() 
    return render_template("page.html" , produkts = produkts)

@app.route("/login", methods =["GET", "POST"])
def login():
    if "user_id" in session:
        userr =session.get("user_id")
        con = sqlite3.connect("auksion.db")
        cursor = con.cursor()
    
        cursor.execute("SELECT * FROM mahsulotlar")
        produkts = cursor.fetchall()  
        flash("siz allaqachon logindan o'tgansiz")
        con.close()
        return render_template("index.html", log = userr , produkts = produkts)

    con = sqlite3.connect("auksion.db")
    cursor = con.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foydalanuvchilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            foydalanuvchi_nomi TEXT NOT NULL UNIQUE,
            parol TEXT NOT NULL
     )
    """)
    cursor.execute("SELECT * FROM foydalanuvchilar")
    
    con.commit()   


    if request.method =="GET":
        return render_template("login.html")
    
    elif request.method =="POST":
        foydalanuvchilar =request.form.get("email")
        password = request.form.get("password")
        if 'seen' not in request.cookies:
            session["user_id"] =foydalanuvchilar
            session["password"] = password
            response = make_response(render_template("index.html" , log="Log In"))
            response.set_cookie('seen', "1")
            return response

     
        cursor.execute("SELECT * FROM foydalanuvchilar WHERE foydalanuvchi_nomi =? AND parol=?",(foydalanuvchilar, password))

        row =cursor.fetchone()

        con.close()
        if row:

            session["user_id"] = foydalanuvchilar
            return redirect("/")
        # if "user_id" in session:
        #     flash("siz allaqchon registratsiyadan o'tgansiz")
        # elif "user_id" not in session:
        #     return make_response("Ilitmos birinchi registratisyadan o'ting")

            # return(f"User found: ID={row[0]}, Username={row[1]}, Password={row[2]}")

        else:
            flash("No'to'gri foydalanuvchi nomi yoki parol")
            return render_template("unfound.html")
    # return render_template("register.html")


@app.route("/log-out")
def logout():
    session.pop("user_id", None)
    session.pop("foydalan", None)
    flash("siz tizimdan chiqdingiz")
    return redirect("/")


@app.route("/user")
def user():
      if "foydalanuvchi" in session:
            return redirect("/")
      else:
            return redirect("register.html")


@app.route("/register", methods =["GET", "POST"])
def register():
    if request.method =="GET":
        return render_template("register.html")
    elif request.method =="POST":
    
        foydalanuvchi_nomi =request.form.get("email")
        parol = request.form.get("password")
        con = sqlite3.connect("auksion.db")
        cursor =con.cursor()
        cursor.execute("INSERT INTO foydalanuvchilar(foydalanuvchi_nomi, parol) VALUES(?,?)", (foydalanuvchi_nomi, parol))

    return render_template("index.html")

@app.route("/tarif/<id>")
def taklif(id):
    con = sqlite3.connect("auksion.db")
    cursor = con.cursor()
    cursor.execute(f"SELECT * FROM mahsulotlar WHERE id = {id}")
    produkts = cursor.fetchall() 
    return render_template("tarif.html" , produkts = produkts)

@app.route("/page/<id>", methods=["POST", "GET"])
def taklifend(id):
    foy_nomi =request.form.get("email", "")
    con = sqlite3.connect("auksion.db")
    cursor = con.cursor()
    cursor.execute("SELECT * FROM mahsulotlar WHERE id = ?", (id,))

    row = cursor.fetchone()
    narx = row[2]
    max_nomi = row[1]




    cursor.execute("INSERT INTO takliflar(fodalanuvchi_nomi,mahsulot_nomi , narx ) VALUES(?,?,?)", (foy_nomi, max_nomi , narx))
    if row: 
        purce = request.form.get("pur")

        if not purce: 
            eror = "Iltimos, qiymat kiriting!"
            return render_template("page.html", produkts=[row], eror=eror)

        try:
            purce = int(purce) 
            row_price = int(row[2])

            if purce <= row_price:
                eror = "Ko'proq pul kiriting, mablag‘ kam!"
                return render_template("page.html", produkts=[row], eror=eror)

            return render_template("accept.html",  foy_nomi = foy_nomi , max_nomi = max_nomi , narx = narx)

        except ValueError:
            eror = "Narx faqat raqam bo'lishi kerak!"
            return render_template("page.html", produkts=[row], eror=eror)

    cursor.close()
    con.close()
    return render_template("page.html", produkts=[])




if __name__ == "__main__":
    app.run(debug=True)
