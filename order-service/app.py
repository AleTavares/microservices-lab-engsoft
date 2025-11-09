from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('PORT', 3003))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://orderservice:orderpass123@localhost:5434/orderdb')

# URLs dos outros serviços
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:3001')
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:3002')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    user_name VARCHAR(255) NOT NULL,
                    product_id INTEGER NOT NULL,
                    product_name VARCHAR(255) NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    total_price DECIMAL(10,2) NOT NULL,
                    status VARCHAR(50) DEFAULT 'confirmed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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
        "service": "order-service",
        "status": "healthy",
        "port": PORT
    })

@app.route('/orders', methods=['GET'])
def get_orders():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([dict(order) for order in orders])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
        order = cur.fetchone()
        cur.close()
        conn.close()
        
        if not order:
            return jsonify({"error": "Pedido não encontrado"}), 404
        return jsonify(dict(order))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    if not data or not data.get('userId') or not data.get('productId') or not data.get('quantity'):
        return jsonify({"error": "UserId, productId e quantity são obrigatórios"}), 400
    
    user_id = data['userId']
    product_id = data['productId']
    quantity = data['quantity']
    
    try:
        # 1. Verificar se usuário existe
        user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}", timeout=5)
        if user_response.status_code == 404:
            return jsonify({"error": "Usuário não encontrado"}), 404
        user = user_response.json()
        
        # 2. Verificar se produto existe e tem estoque
        product_response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
        if product_response.status_code == 404:
            return jsonify({"error": "Produto não encontrado"}), 404
        product = product_response.json()
        
        if product['stock'] < quantity:
            return jsonify({"error": "Estoque insuficiente"}), 400
        
        # 3. Atualizar estoque do produto
        stock_response = requests.put(
            f"{PRODUCT_SERVICE_URL}/products/{product_id}/stock",
            json={"quantity": quantity},
            timeout=5
        )
        
        if stock_response.status_code != 200:
            return jsonify({"error": "Erro ao atualizar estoque"}), 500
        
        # 4. Criar pedido no banco de dados
        conn = get_db_connection()
        cur = conn.cursor()
        
        total_price = float(product['price']) * quantity
        
        cur.execute(
            """INSERT INTO orders (user_id, user_name, product_id, product_name, quantity, unit_price, total_price, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
               RETURNING *""",
            (user['id'], user['name'], product['id'], product['name'], 
             quantity, float(product['price']), total_price, 'confirmed')
        )
        
        order = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify(dict(order)), 201
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar pedido: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500
    except Exception as e:
        print(f"Erro no banco de dados: {str(e)}")
        return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    print(f"🚀 Order Service rodando na porta {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)