#!/bin/bash

echo "📦 Instalando dependências Python..."
echo "===================================="

# Verificar se pip3 está disponível
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instale Python 3 e pip3 primeiro."
    exit 1
fi

# Instalar dependências globalmente
echo "🔧 Instalando Flask e dependências..."
pip3 install -r requirements.txt

echo ""
echo "✅ Dependências instaladas com sucesso!"
echo ""
echo "🚀 Para iniciar os serviços:"
echo "   ./start-services.sh"