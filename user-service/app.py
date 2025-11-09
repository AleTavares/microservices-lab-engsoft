from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('PORT', 3001))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://userservice:userpass123@localhost:5432/userdb')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Inserir usuário admin se não existir
            cur.execute("SELECT COUNT(*) FROM users WHERE email = %s", ('admin@email.com',))
            if cur.fetchone()['count'] == 0:
                cur.execute(
                    "INSERT INTO users (name, email) VALUES (%s, %s)",
                    ('Admin User', 'admin@email.com')
                )
            
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Database initialized successfully")
            break
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"⏳ Waiting for database... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"❌ Failed to connect to database: {e}")
                raise

init_db()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "service": "user-service",
        "status": "healthy",
        "port": PORT
    })

@app.route('/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, created_at FROM users ORDER BY id")
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([dict(user) for user in users])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, created_at FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        return jsonify(dict(user))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({"error": "Nome e email são obrigatórios"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id, name, email, created_at",
            (data['name'], data['email'])
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify(dict(user)), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "Email já existe"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 User Service rodando na porta {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)