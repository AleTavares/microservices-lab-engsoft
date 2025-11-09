#!/bin/bash

echo "🚀 Iniciando Microsserviços..."
echo "=============================="

# Função para verificar se uma porta está em uso
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Porta $1 já está em uso"
        return 1
    else
        return 0
    fi
}

# Verificar portas
echo "🔍 Verificando portas disponíveis..."
check_port 3000 && check_port 3001 && check_port 3002 && check_port 3003

if [ $? -ne 0 ]; then
    echo "❌ Algumas portas estão ocupadas. Execute: ./stop-services.sh"
    exit 1
fi

echo ""
echo "📦 Verificando dependências..."

# Verificar se Flask está instalado
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask não encontrado. Execute: ./install-dependencies.sh"
    exit 1
fi

echo ""
echo "🚀 Iniciando serviços..."

# Iniciar serviços em background
cd user-service && python3 app.py > ../logs/user-service.log 2>&1 &
USER_PID=$!
echo "✅ User Service iniciado (PID: $USER_PID, Porta: 3001)"

cd ../product-service && python3 app.py > ../logs/product-service.log 2>&1 &
PRODUCT_PID=$!
echo "✅ Product Service iniciado (PID: $PRODUCT_PID, Porta: 3002)"

cd ../order-service && python3 app.py > ../logs/order-service.log 2>&1 &
ORDER_PID=$!
echo "✅ Order Service iniciado (PID: $ORDER_PID, Porta: 3003)"

# Aguardar serviços iniciarem
sleep 3

cd ../api-gateway && python3 app.py > ../logs/api-gateway.log 2>&1 &
GATEWAY_PID=$!
echo "✅ API Gateway iniciado (PID: $GATEWAY_PID, Porta: 3000)"

# Salvar PIDs para poder parar depois
mkdir -p logs
echo "$USER_PID" > logs/user-service.pid
echo "$PRODUCT_PID" > logs/product-service.pid  
echo "$ORDER_PID" > logs/order-service.pid
echo "$GATEWAY_PID" > logs/api-gateway.pid

echo ""
echo "🎉 Todos os serviços foram iniciados!"
echo ""
echo "📋 URLs disponíveis:"
echo "   API Gateway: http://localhost:3000"
echo "   Health Check: http://localhost:3000/api/health/all"
echo "   User Service: http://localhost:3001"
echo "   Product Service: http://localhost:3002"
echo "   Order Service: http://localhost:3003"
echo ""
echo "📝 Logs salvos em: ./logs/"
echo "🛑 Para parar os serviços: ./stop-services.sh"
echo "🧪 Para testar a API: ./test-api.sh"