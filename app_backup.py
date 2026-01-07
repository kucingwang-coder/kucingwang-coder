from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder=".")
CORS(app)

@app.route("/")
def home():
    return open("index.html").read()

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    users = {}
    if os.path.exists("users.json"):
        users = json.load(open("users.json"))
    
    if data["email"] in users:
        return jsonify({"error": "Email sudah terdaftar"}), 400
    
    users[data["email"]] = {"password": data["password"], "name": data["name"]}
    json.dump(users, open("users.json", "w"))
    return jsonify({"message": "Registrasi berhasil!", "user": data["name"]})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not os.path.exists("users.json"):
        return jsonify({"error": "Belum ada user terdaftar"}), 400
    
    users = json.load(open("users.json"))
    if data["email"] not in users or users[data["email"]]["password"] != data["password"]:
        return jsonify({"error": "Email atau password salah"}), 400
    
    return jsonify({"message": "Login berhasil!", "user": users[data["email"]]["name"]})

app.run(host="0.0.0.0", port=5000, debug=True)
