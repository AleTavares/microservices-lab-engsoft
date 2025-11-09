#!/bin/bash

echo "🛑 Parando Microsserviços..."
echo "============================"

# Função para parar um serviço
stop_service() {
    local service_name=$1
    local pid_file="logs/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo "✅ $service_name parado (PID: $pid)"
        else
            echo "⚠️  $service_name já estava parado"
        fi
        rm -f "$pid_file"
    else
        echo "⚠️  PID file não encontrado para $service_name"
    fi
}

# Parar todos os serviços
stop_service "api-gateway"
stop_service "order-service"
stop_service "product-service"
stop_service "user-service"

# Limpar processos Python restantes nas portas específicas
echo ""
echo "🧹 Limpando processos restantes..."

for port in 3000 3001 3002 3003; do
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
        echo "🔥 Processo na porta $port finalizado"
    fi
done

echo ""
echo "✅ Todos os serviços foram parados!"