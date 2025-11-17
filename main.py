from flask import Flask, request, jsonify
import psycopg  
import os

app = Flask(__name__)

# Подключение к БД (прямо из env-var)
DATABASE_URL = os.environ.get('DATABASE_URL')
conn = None
if DATABASE_URL:
    try:
        conn = psycopg.connect(DATABASE_URL)  # <-- Прямо строка URL для v3
        print("DB connected successfully")  # Для логов Render
    except Exception as e:
        print(f"DB connection failed: {e}")  # Для отладки
        conn = None

# Создание таблицы при старте
if conn:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()

@app.route('/')
def hello():
    return "Hello, Serverless! 🚀\n", 200, {'Content-Type': 'text/plain'}

@app.route('/echo', methods=['POST'])
def echo():
    data = request.get_json()
    return jsonify({
        "status": "received",
        "you_sent": data,
        "length": len(str(data)) if data else 0
    })

@app.route('/save', methods=['POST'])
def save_message():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    data = request.get_json()
    message = data.get('message', '') if data else ''

    cur = conn.cursor()
    cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
    conn.commit()
    cur.close()

    return jsonify({"status": "saved", "message": message})

@app.route('/messages')
def get_messages():
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    cur = conn.cursor()
    cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    cur.close()

    messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
    return jsonify(messages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)