from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import cloudinary
import cloudinary.uploader


app = Flask(__name__)
app.secret_key = 'goku123'
CORS(app)


client = MongoClient('mongodb+srv://alisa:IoARr5dmyERwvu7P@cluster0.kkc6y.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')


cloudinary.config(
    cloud_name="duku3zctg",
    api_key="179741952874928",
    api_secret="Y3BLT3yhO8ZrXUBKIuIrgAvPuB0"
)

db = client.shorts_app




@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("profile"))
    return redirect(url_for("login_page"))


@app.route("/signup", methods=["GET"])
def signup_page():
    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if db.users.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409
    hashed_password = generate_password_hash(data["password"])
    user = {"name": data["name"], "email": data["email"], "password": hashed_password}
    db.users.insert_one(user)
    return jsonify({"message": "Signup successful"}), 201


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = db.users.find_one({"email": data["email"]})
    if user and check_password_hash(user["password"], data["password"]):
        session["user"] = {"id": str(user["_id"]), "name": user["name"], "email": user["email"]}
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/profile", methods=["GET"])
def profile():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("profile.html", user=session["user"])


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login_page"))



@app.route("/upload", methods=["GET"])
def upload_page():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload_video():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    file = request.files.get("file")
    title = request.form.get("title")
    user_id = session["user"]["id"]

    if not file or not title:
        return jsonify({"error": "File and title are required"}), 400

    
    result = cloudinary.uploader.upload(file, resource_type="video")

    
    video = {
        "id": str(uuid.uuid4()),
        "title": title,
        "url": result["secure_url"],
        "user_id": user_id,
        "likes": [],
        "comments": []
    }
    db.videos.insert_one(video)
    return jsonify({"message": "Video uploaded successfully!"}), 201


@app.route("/home", methods=["GET"])
def home_page():
    videos = list(db.videos.find().sort("_id", -1))  
    return render_template("home.html", videos=videos)


if __name__ == "__main__":
    app.run(debug=True)
