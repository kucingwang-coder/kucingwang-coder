from flask import Flask, render_template, request, jsonify, session, redirect
from flask_socketio import SocketIO, emit
import requests
import json
import os
from datetime import datetime
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wangweize_ultimate_secret_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# API Configuration
OPENROUTER_API_KEY = "sk-or-v1-0040b89d8bb5a87ece65bbf1dc857f1efb3d7d204ca17f6a3f"
YOUTUBE_API_KEY = "AIzaSyDI7glTa5yA1FWelnefCQIUyIvNNk89ywbo"
TELEGRAM_BOT_TOKEN = "8576561995:AAFj0wx-JYLwNBFo06jikO6T5N7j3tG0taQ"

# Database Files
USERS_FILE = 'users.json'
CHATS_FILE = 'chats.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {'wangweize': {'password': 'admin123', 'role': 'admin'}}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_chats():
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_chats(chats):
    with open(CHATS_FILE, 'w') as f:
        json.dump(chats, f, indent=2)

connected_users = {}

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('index.html', user=session['user'])

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    users = load_users()
    
    if username in users and users[username]['password'] == password:
        session['user'] = username
        session['role'] = users[username].get('role', 'user')
        
        socketio.emit('terminal_log', {
            'message': f'🔐 LOGIN: {username}',
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'success'
        }, broadcast=True)
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/logout')
def logout():
    user = session.get('user', 'Unknown')
    session.clear()
    
    socketio.emit('terminal_log', {
        'message': f'🚪 LOGOUT: {user}',
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': 'warning'
    }, broadcast=True)
    
    return redirect('/')

@app.route('/ai-chat', methods=['POST'])
def ai_chat():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    message = data.get('message', '')
    user = session['user']
    
    socketio.emit('terminal_log', {
        'message': f'💬 CHAT: {user} - {message[:50]}...',
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': 'info'
    }, broadcast=True)
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3.5-sonnet",
                "messages": [{"role": "user", "content": message}]
            }
        )
        
        result = response.json()
        ai_response = result['choices'][0]['message']['content']
        
        chats = load_chats()
        chats.append({
            'user': user,
            'message': message,
            'response': ai_response,
            'time': datetime.now().isoformat()
        })
        save_chats(chats)
        
        return jsonify({'response': ai_response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/youtube-search', methods=['POST'])
def youtube_search():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    query = data.get('query', '')
    
    socketio.emit('terminal_log', {
        'message': f'🎬 YOUTUBE: {session["user"]} - {query}',
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': 'info'
    }, broadcast=True)
    
    try:
        response = requests.get(
            'https://www.googleapis.com/youtube/v3/search',
            params={
                'part': 'snippet',
                'q': query,
                'key': YOUTUBE_API_KEY,
                'maxResults': 5,
                'type': 'video'
            }
        )
        
        results = response.json()
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    prompt = data.get('prompt', '')
    
    socketio.emit('terminal_log', {
        'message': f'🎨 IMAGE: {session["user"]} - {prompt[:50]}...',
        'time': datetime.now().strftime('%H:%M:%S'),
        'type': 'info'
    }, broadcast=True)
    
    return jsonify({'image_url': 'https://via.placeholder.com/512'})

@app.route('/send-telegram', methods=['POST'])
def send_telegram():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    message = data.get('message', '')
    chat_id = data.get('chat_id', '')
    
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': message
            }
        )
        
        return jsonify(response.json())
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    if 'user' in session:
        connected_users[request.sid] = session['user']
        emit('terminal_log', {
            'message': f'✅ CONNECTED: {session["user"]}',
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'success'
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_users:
        user = connected_users[request.sid]
        del connected_users[request.sid]
        emit('terminal_log', {
            'message': f'❌ DISCONNECTED: {user}',
            'time': datetime.now().strftime('%H:%M:%S'),
            'type': 'error'
        }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
