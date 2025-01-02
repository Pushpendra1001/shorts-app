from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import cloudinary
import cloudinary.uploader
from bson.objectid import ObjectId
from datetime import datetime


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
        return redirect(url_for("home_page"))  
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
    user = {
        "name": data["name"], 
        "email": data["email"], 
        "password": hashed_password,
        "user_type": data["userType"]
    }
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
        session["user"] = {
            "id": str(user["_id"]), 
            "name": user["name"], 
            "email": user["email"],
            "user_type": user["user_type"]  
        }
        return jsonify({"message": "Login successful", "redirect": "/home"})
    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/videos/search")
def search_videos():
    query = request.args.get("q", "")
    videos = list(db.videos.find({"title": {"$regex": query, "$options": "i"}}))
    
    for video in videos:
        video['_id'] = str(video['_id'])
        
        uploader = db.users.find_one({"_id": ObjectId(video['user_id'])})
        if uploader:
            video['uploader_name'] = uploader['name']
        else:
            video['uploader_name'] = "Unknown"
            
    return jsonify(videos)

@app.route("/profile", methods=["GET"])
def profile():
    if "user" not in session:
        return redirect(url_for("login_page"))
    user = db.users.find_one({"_id": ObjectId(session["user"]["id"])})
    return render_template("profile.html", user=user)

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

@app.route("/api/user/videos")
def get_user_videos():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    user_id = session["user"]["id"]
    videos = list(db.videos.find({"user_id": user_id}))
    
    # Convert ObjectId to string
    for video in videos:
        video['_id'] = str(video['_id'])
        
    return jsonify(videos)

@app.route("/api/videos/<video_id>", methods=["DELETE"])
def delete_video(video_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    video = db.videos.find_one({"_id": ObjectId(video_id)})
    if not video:
        return jsonify({"error": "Video not found"}), 404
        
    
    if video["user_id"] != session["user"]["id"]:
        return jsonify({"error": "Unauthorized to delete this video"}), 403
        
    
    db.videos.delete_one({"_id": ObjectId(video_id)})
    
    return jsonify({"message": "Video deleted successfully"})

@app.route("/api/videos/<video_id>/like", methods=["POST"])
def like_video(video_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    user_id = session["user"]["id"]
    video = db.videos.find_one({"_id": ObjectId(video_id)})
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
        
    likes = video.get("likes", [])
    
    if user_id in likes:
        db.videos.update_one(
            {"_id": ObjectId(video_id)},
            {"$pull": {"likes": user_id}}
        )
    else:
        db.videos.update_one(
            {"_id": ObjectId(video_id)},
            {"$push": {"likes": user_id}}
        )
    
    updated_video = db.videos.find_one({"_id": ObjectId(video_id)})
    return jsonify({"likes": len(updated_video.get("likes", []))})

@app.route("/api/videos/<video_id>/comments", methods=["GET"])
def get_comments(video_id):
    video = db.videos.find_one({"_id": ObjectId(video_id)})
    if not video:
        return jsonify({"error": "Video not found"}), 404
        
    comments = video.get("comments", [])
    
    for comment in comments:
        user = db.users.find_one({"_id": ObjectId(comment["user_id"])})
        if user:
            comment["user_name"] = user["name"]
    
    return jsonify(comments)


@app.route("/api/videos/<video_id>/comment", methods=["POST"])
def add_comment(video_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    content = request.json.get("comment")
    if not content:
        return jsonify({"error": "Comment content required"}), 400
        
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": session["user"]["id"],
        "content": content,
        "created_at": datetime.now().isoformat()  
    }
    
    db.videos.update_one(
        {"_id": ObjectId(video_id)},
        {"$push": {"comments": comment}}
    )
    
    return jsonify({"message": "Comment added successfully"})

@app.route("/home", methods=["GET"])
def home_page():
    videos = list(db.videos.find().sort("_id", -1))
    for video in videos:
        uploader = db.users.find_one({"_id": ObjectId(video['user_id'])})
        if uploader:
            video['uploader_name'] = uploader['name']
        else:
            video['uploader_name'] = "Unknown"
    return render_template("home.html", videos=videos)


if __name__ == "__main__":
    app.run(debug=True)
