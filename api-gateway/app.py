from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per 15 minutes"]
)

PORT = int(os.environ.get('PORT', 3000))

# URLs dos serviços
USER_SERVICE_URL = os.environ.get('USER_SERVICE_URL', 'http://localhost:3001')
PRODUCT_SERVICE_URL = os.environ.get('PRODUCT_SERVICE_URL', 'http://localhost:3002')
ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:3003')

# Middleware de logging
@app.before_request
def log_request():
    print(f"{datetime.now().isoformat()} - {request.method} {request.path}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "service": "api-gateway",
        "status": "healthy",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health/all', methods=['GET'])
def health_all():
    services = [
        {"name": "user-service", "url": f"{USER_SERVICE_URL}/health"},
        {"name": "product-service", "url": f"{PRODUCT_SERVICE_URL}/health"},
        {"name": "order-service", "url": f"{ORDER_SERVICE_URL}/health"}
    ]
    
    health_checks = []
    for service in services:
        try:
            response = requests.get(service['url'], timeout=5)
            health_checks.append({
                **service,
                "status": "healthy",
                "data": response.json()
            })
        except Exception as e:
            health_checks.append({
                **service,
                "status": "unhealthy",
                "error": str(e)
            })
    
    return jsonify({
        "gateway": "healthy",
        "services": health_checks
    })

# Proxy para User Service
@app.route('/api/users', methods=['GET', 'POST'])
@app.route('/api/users/<int:user_id>', methods=['GET'])
@limiter.limit("100 per 15 minutes")
def proxy_users(user_id=None):
    try:
        if user_id:
            url = f"{USER_SERVICE_URL}/users/{user_id}"
        else:
            url = f"{USER_SERVICE_URL}/users"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=5)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), timeout=5)
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException:
        return jsonify({"error": "User Service indisponível"}), 503

# Proxy para Product Service
@app.route('/api/products', methods=['GET', 'POST'])
@app.route('/api/products/<int:product_id>', methods=['GET'])
@app.route('/api/products/<int:product_id>/stock', methods=['PUT'])
@limiter.limit("100 per 15 minutes")
def proxy_products(product_id=None):
    try:
        if product_id and request.endpoint.endswith('stock'):
            url = f"{PRODUCT_SERVICE_URL}/products/{product_id}/stock"
        elif product_id:
            url = f"{PRODUCT_SERVICE_URL}/products/{product_id}"
        else:
            url = f"{PRODUCT_SERVICE_URL}/products"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=5)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), timeout=5)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), timeout=5)
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException:
        return jsonify({"error": "Product Service indisponível"}), 503

# Proxy para Order Service
@app.route('/api/orders', methods=['GET', 'POST'])
@app.route('/api/orders/<int:order_id>', methods=['GET'])
@limiter.limit("100 per 15 minutes")
def proxy_orders(order_id=None):
    try:
        if order_id:
            url = f"{ORDER_SERVICE_URL}/orders/{order_id}"
        else:
            url = f"{ORDER_SERVICE_URL}/orders"
        
        if request.method == 'GET':
            response = requests.get(url, timeout=5)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), timeout=5)
        
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException:
        return jsonify({"error": "Order Service indisponível"}), 503

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Rota não encontrada"}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({"error": "Muitas requisições. Tente novamente em 15 minutos."}), 429

if __name__ == '__main__':
    print(f"🚀 API Gateway rodando na porta {PORT}")
    print(f"📋 Health check: http://localhost:{PORT}/health")
    print(f"🔍 Health check completo: http://localhost:{PORT}/api/health/all")
    app.run(host='0.0.0.0', port=PORT, debug=False)