#!/bin/bash

echo "🧪 Testando API Gateway e Microsserviços"
echo "========================================"

BASE_URL="http://localhost:3000/api"

echo ""
echo "1️⃣ Testando Health Check..."
curl -s "$BASE_URL/health/all" | jq '.' || echo "❌ Erro no health check"

echo ""
echo "2️⃣ Criando usuário..."
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "João Silva", "email": "joao@email.com"}')
echo $USER_RESPONSE | jq '.'
USER_ID=$(echo $USER_RESPONSE | jq -r '.id')

echo ""
echo "3️⃣ Criando produto..."
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/products" \
  -H "Content-Type: application/json" \
  -d '{"name": "Notebook Gamer", "price": 3500.00, "stock": 5}')
echo $PRODUCT_RESPONSE | jq '.'
PRODUCT_ID=$(echo $PRODUCT_RESPONSE | jq -r '.id')

echo ""
echo "4️⃣ Listando usuários..."
curl -s "$BASE_URL/users" | jq '.'

echo ""
echo "5️⃣ Listando produtos..."
curl -s "$BASE_URL/products" | jq '.'

echo ""
echo "6️⃣ Criando pedido..."
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders" \
  -H "Content-Type: application/json" \
  -d "{\"userId\": $USER_ID, \"productId\": $PRODUCT_ID, \"quantity\": 2}")
echo $ORDER_RESPONSE | jq '.'

echo ""
echo "7️⃣ Listando pedidos..."
curl -s "$BASE_URL/orders" | jq '.'

echo ""
echo "8️⃣ Verificando estoque atualizado..."
curl -s "$BASE_URL/products/$PRODUCT_ID" | jq '.'

echo ""
echo "✅ Testes concluídos!"