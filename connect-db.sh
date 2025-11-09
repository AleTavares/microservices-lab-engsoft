#!/bin/bash

echo "🐘 Conectar aos Bancos PostgreSQL"
echo "=================================="

if [ "$1" = "" ]; then
    echo "Uso: $0 [user|product|order]"
    echo ""
    echo "Exemplos:"
    echo "  $0 user     - Conectar ao banco de usuários"
    echo "  $0 product  - Conectar ao banco de produtos"
    echo "  $0 order    - Conectar ao banco de pedidos"
    exit 1
fi

case $1 in
    "user")
        echo "🔗 Conectando ao User Database..."
        docker exec -it $(docker ps -q -f name=user-db) psql -U userservice -d userdb
        ;;
    "product")
        echo "🔗 Conectando ao Product Database..."
        docker exec -it $(docker ps -q -f name=product-db) psql -U productservice -d productdb
        ;;
    "order")
        echo "🔗 Conectando ao Order Database..."
        docker exec -it $(docker ps -q -f name=order-db) psql -U orderservice -d orderdb
        ;;
    *)
        echo "❌ Serviço inválido: $1"
        echo "Use: user, product ou order"
        exit 1
        ;;
esac