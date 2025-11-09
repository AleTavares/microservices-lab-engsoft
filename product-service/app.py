from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = Flask(__name__)
CORS(app)

PORT = int(os.environ.get('PORT', 3002))
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://productservice:productpass123@localhost:5433/productdb')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    max_retries = 30
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Inserir produtos iniciais se não existirem
            cur.execute("SELECT COUNT(*) FROM products")
            if cur.fetchone()['count'] == 0:
                initial_products = [
                    ('Notebook Dell', 2500.00, 5),
                    ('Mouse Logitech', 150.00, 20)
                ]
                for name, price, stock in initial_products:
                    cur.execute(
                        "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                        (name, price, stock)
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
        "service": "product-service",
        "status": "healthy",
        "port": PORT
    })

@app.route('/products', methods=['GET'])
def get_products():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, stock, created_at FROM products ORDER BY id")
        products = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([dict(product) for product in products])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, stock, created_at FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        cur.close()
        conn.close()
        
        if not product:
            return jsonify({"error": "Produto não encontrado"}), 404
        return jsonify(dict(product))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('price') or data.get('stock') is None:
        return jsonify({"error": "Nome, preço e estoque são obrigatórios"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s) RETURNING id, name, price, stock, created_at",
            (data['name'], float(data['price']), int(data['stock']))
        )
        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify(dict(product)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/products/<int:product_id>/stock', methods=['PUT'])
def update_stock(product_id):
    data = request.get_json()
    quantity = data.get('quantity', 0)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se produto existe e tem estoque suficiente
        cur.execute("SELECT stock FROM products WHERE id = %s", (product_id,))
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            return jsonify({"error": "Produto não encontrado"}), 404
        
        if result['stock'] < quantity:
            cur.close()
            conn.close()
            return jsonify({"error": "Estoque insuficiente"}), 400
        
        # Atualizar estoque
        cur.execute(
            "UPDATE products SET stock = stock - %s WHERE id = %s RETURNING id, name, price, stock, created_at",
            (quantity, product_id)
        )
        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify(dict(product))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"🚀 Product Service rodando na porta {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)