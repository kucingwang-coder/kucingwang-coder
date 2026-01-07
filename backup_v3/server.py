from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

USER_DB = "users.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_DB, 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/')
def home():
    return jsonify({
        "status": "Wang Weize AI Server v2.0",
        "owner": "wangweize434@gmail.com",
        "status": "online",
        "features": ["login", "ai-chat", "youtube"]
    })

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    users = load_users()
    
    if data['email'] in users:
        return jsonify({"error": "Email sudah terdaftar"}), 400
    
    users[data['email']] = {
        "password": data['password'],
        "name": data['name']
    }
    
    save_users(users)
    return jsonify({"message": "Registrasi berhasil!"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    users = load_users()
    
    if data['email'] not in users:
        return jsonify({"error": "Email belum terdaftar"}), 400
    
    if users[data['email']]['password'] != data['password']:
        return jsonify({"error": "Password salah"}), 400
    
    return jsonify({
        "message": "Login berhasil!",
        "user": {
            "email": data['email'],
            "name": users[data['email']]['name']
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
