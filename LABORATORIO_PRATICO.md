# 🧪 Laboratório Prático: Microsserviços E-commerce
## Guia Completo de Aprendizagem Autoguiada

---

## 📋 **Pré-requisitos e Preparação**

### ✅ **Checklist Inicial**
- [ ] Docker e Docker Compose instalados
- [ ] Python 3.10+ instalado
- [ ] Git configurado
- [ ] Terminal/CMD disponível
- [ ] Editor de código (VS Code recomendado)

### 🎯 **Objetivos do Laboratório**
Ao final deste laboratório, você será capaz de:
- Executar uma arquitetura de microsserviços completa
- Entender comunicação entre serviços
- Identificar benefícios e desafios dos microsserviços
- Implementar padrões fundamentais (API Gateway, Database per Service)
- Diagnosticar e resolver problemas em sistemas distribuídos

---

## 🚀 **ETAPA 1: Configuração Inicial (15 minutos)**

### 1.1 Preparando o Ambiente
```bash
# 1. Clone o repositório (se ainda não fez)
git clone https://github.com/AleTavares/microservices-lab-engsoft.git
cd microservices-lab-engsoft

# 2. Instale as dependências Python
./install-dependencies.sh

# 3. Verifique se tudo está funcionando
python3 --version
docker --version
docker-compose --version
```

### 1.2 Primeira Execução
```bash
# Inicie todos os serviços com Docker
docker-compose up --build
```

**🔍 O que observar:**
- [ ] 7 containers sendo criados (3 bancos + 4 serviços)
- [ ] Mensagens de "Database initialized successfully"
- [ ] Todos os serviços rodando sem erros

### 1.3 Verificação de Saúde
```bash
# Em outro terminal, teste o health check
curl http://localhost:3000/api/health/all | jq '.'
```

**✅ Resultado esperado:**
```json
{
  "gateway": "healthy",
  "services": [
    {"name": "user-service", "status": "healthy"},
    {"name": "product-service", "status": "healthy"},
    {"name": "order-service", "status": "healthy"}
  ]
}
```

---

## 🔍 **ETAPA 2: Explorando a Arquitetura (20 minutos)**

### 2.1 Entendendo o Database per Service

**🎯 Objetivo:** Compreender como cada serviço tem seu próprio banco de dados.

```bash
# Conecte-se ao banco do User Service
./connect-db.sh user
```

**No PostgreSQL, execute:**
```sql
-- Veja a estrutura da tabela
\d users

-- Consulte os dados
SELECT * FROM users;

-- Saia do banco
\q
```

**🔄 Repita para os outros serviços:**
```bash
./connect-db.sh product
./connect-db.sh order
```

**📝 Anote suas observações:**
- Quantas tabelas cada banco possui?
- Que dados estão armazenados em cada um?
- Como isso difere de um banco monolítico?

### 2.2 Testando Comunicação Entre Serviços

**🎯 Objetivo:** Ver como os serviços se comunicam via HTTP.

```bash
# 1. Crie um usuário
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Maria Silva", "email": "maria@email.com"}'

# 2. Crie um produto
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Smartphone", "price": 1200.00, "stock": 15}'

# 3. Crie um pedido (observe a comunicação entre serviços)
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId": 1, "productId": 1, "quantity": 2}'
```

**🔍 Observe os logs:**
```bash
# Em outro terminal, veja os logs em tempo real
docker-compose logs -f order-service
```

**📝 Questões para reflexão:**
1. Quantas chamadas HTTP o Order Service fez?
2. O que aconteceria se o User Service estivesse offline?
3. Como você melhoraria a resiliência?

### 2.3 API Gateway em Ação

**🎯 Objetivo:** Entender o papel do API Gateway.

```bash
# Acesso via Gateway (recomendado)
curl http://localhost:3000/api/users

# Acesso direto ao serviço (bypass do gateway)
curl http://localhost:3001/users
```

**📊 Compare as respostas:**
- As respostas são idênticas?
- Que benefícios o Gateway oferece?
- Como o rate limiting funciona?

---

## 🛠️ **ETAPA 3: Implementações Práticas (45 minutos)**

### 3.1 Adicionando um Novo Endpoint

**🎯 Objetivo:** Implementar comunicação entre User Service e Order Service.

**📝 Tarefa:** Adicione um endpoint para listar pedidos de um usuário específico.

```python
# Edite: user-service/app.py
# Adicione após os outros endpoints:

@app.route('/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    try:
        # 1. Verificar se usuário existe
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # 2. Buscar pedidos do usuário no Order Service
        import requests
        ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:3003')
        
        orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=5)
        all_orders = orders_response.json()
        
        # 3. Filtrar pedidos do usuário
        user_orders = [order for order in all_orders if order.get('user_id') == user_id]
        
        return jsonify({
            "user": dict(user),
            "orders": user_orders,
            "total_orders": len(user_orders)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**🧪 Teste sua implementação:**
```bash
# Reinicie o User Service
docker-compose restart user-service

# Teste o novo endpoint
curl http://localhost:3001/users/1/orders | jq '.'
```

### 3.2 Implementando Circuit Breaker

**🎯 Objetivo:** Adicionar resiliência ao sistema.

```python
# Edite: order-service/app.py
# Adicione no início do arquivo:

import time

# Circuit Breaker simples
circuit_breaker = {
    "failures": 0,
    "threshold": 3,
    "timeout": 30,  # segundos
    "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
    "last_failure": 0
}

def call_service_with_circuit_breaker(url, fallback_data=None):
    current_time = time.time()
    
    # Verificar se circuit breaker está aberto
    if (circuit_breaker["state"] == "OPEN" and 
        current_time - circuit_breaker["last_failure"] < circuit_breaker["timeout"]):
        print("🚫 Circuit breaker OPEN - usando fallback")
        return fallback_data or {"error": "Service temporarily unavailable"}
    
    # Tentar half-open se timeout passou
    if circuit_breaker["state"] == "OPEN":
        circuit_breaker["state"] = "HALF_OPEN"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        # Sucesso - resetar circuit breaker
        circuit_breaker["failures"] = 0
        circuit_breaker["state"] = "CLOSED"
        return response.json()
        
    except requests.exceptions.RequestException as e:
        circuit_breaker["failures"] += 1
        circuit_breaker["last_failure"] = current_time
        
        if circuit_breaker["failures"] >= circuit_breaker["threshold"]:
            circuit_breaker["state"] = "OPEN"
            print(f"⚠️ Circuit breaker OPENED after {circuit_breaker['failures']} failures")
        
        print(f"❌ Service call failed ({circuit_breaker['failures']}/{circuit_breaker['threshold']}): {e}")
        return fallback_data or {"error": "Service call failed"}

# Substitua as chamadas requests.get() por call_service_with_circuit_breaker()
```

**🧪 Teste o Circuit Breaker:**
```bash
# 1. Pare o User Service
docker-compose stop user-service

# 2. Tente criar pedidos múltiplas vezes
for i in {1..5}; do
  curl -X POST http://localhost:3000/api/orders \
    -H "Content-Type: application/json" \
    -d '{"userId": 1, "productId": 1, "quantity": 1}'
  echo "Tentativa $i"
done

# 3. Observe os logs
docker-compose logs order-service
```

### 3.3 Adicionando Métricas de Monitoramento

**🎯 Objetivo:** Implementar observabilidade básica.

```python
# Crie: shared/metrics.py
from datetime import datetime
import time

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "errors_total": 0,
            "response_times": [],
            "endpoints": {}
        }
    
    def record_request(self, endpoint, duration, status_code):
        self.metrics["requests_total"] += 1
        self.metrics["response_times"].append(duration)
        
        if status_code >= 400:
            self.metrics["errors_total"] += 1
        
        # Métricas por endpoint
        if endpoint not in self.metrics["endpoints"]:
            self.metrics["endpoints"][endpoint] = {"count": 0, "avg_time": 0}
        
        ep_metrics = self.metrics["endpoints"][endpoint]
        ep_metrics["count"] += 1
        ep_metrics["avg_time"] = (ep_metrics["avg_time"] + duration) / 2
    
    def get_metrics(self):
        avg_response_time = (
            sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            if self.metrics["response_times"] else 0
        )
        
        error_rate = (
            (self.metrics["errors_total"] / self.metrics["requests_total"]) * 100
            if self.metrics["requests_total"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "avg_response_time_ms": round(avg_response_time, 2),
            "error_rate_percent": round(error_rate, 2),
            "uptime_seconds": int(time.time() - self.start_time)
        }

# Adicione em cada serviço:
metrics_collector = MetricsCollector()
metrics_collector.start_time = time.time()

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = (time.time() - request.start_time) * 1000  # ms
    metrics_collector.record_request(request.endpoint, duration, response.status_code)
    return response

@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify(metrics_collector.get_metrics())
```

---

## 🔥 **ETAPA 4: Cenários de Falha (25 minutos)**

### 4.1 Teste de Resiliência - Falha em Cascata

**🎯 Objetivo:** Observar como falhas se propagam em microsserviços.

```bash
# 1. Gere carga normal
for i in {1..10}; do
  curl -s http://localhost:3000/api/orders \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"userId": 1, "productId": 1, "quantity": 1}' &
done

# 2. Durante a carga, pare o Product Service
docker-compose stop product-service

# 3. Continue tentando criar pedidos
for i in {1..5}; do
  curl -X POST http://localhost:3000/api/orders \
    -H "Content-Type: application/json" \
    -d '{"userId": 1, "productId": 1, "quantity": 1}'
  echo "Tentativa pós-falha $i"
done

# 4. Reinicie o serviço
docker-compose start product-service
```

**📝 Análise:**
- Como o sistema se comportou durante a falha?
- Quanto tempo levou para se recuperar?
- Que melhorias você implementaria?

### 4.2 Teste de Carga - Identificando Gargalos

**🎯 Objetivo:** Encontrar limitações de performance.

```bash
# Script de carga (salve como load_test.sh)
#!/bin/bash
echo "🚀 Iniciando teste de carga..."

# Função para fazer requisições
make_requests() {
  for i in {1..100}; do
    curl -s http://localhost:3000/api/products > /dev/null
  done
}

# Execute múltiplas instâncias em paralelo
for i in {1..5}; do
  make_requests &
done

wait
echo "✅ Teste de carga concluído"
```

```bash
# Execute o teste
chmod +x load_test.sh
time ./load_test.sh

# Verifique as métricas
curl http://localhost:3002/metrics | jq '.'
```

---

## 📊 **ETAPA 5: Análise e Otimização (20 minutos)**

### 5.1 Coletando Métricas do Sistema

```bash
# Crie um script de monitoramento
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "📊 Métricas dos Microsserviços"
echo "=============================="

services=("user-service:3001" "product-service:3002" "order-service:3003")

for service in "${services[@]}"; do
  name=$(echo $service | cut -d: -f1)
  port=$(echo $service | cut -d: -f2)
  
  echo ""
  echo "🔹 $name:"
  curl -s http://localhost:$port/metrics | jq '{
    requests_total,
    errors_total,
    avg_response_time_ms,
    error_rate_percent
  }'
done
EOF

chmod +x monitor.sh
./monitor.sh
```

### 5.2 Análise de Performance

**📝 Questões para investigar:**

1. **Latência:**
   - Qual serviço tem maior tempo de resposta?
   - Como a comunicação entre serviços afeta a latência total?

2. **Throughput:**
   - Quantas requisições por segundo cada serviço suporta?
   - Onde estão os gargalos?

3. **Confiabilidade:**
   - Qual a taxa de erro de cada serviço?
   - Como melhorar a resiliência?

### 5.3 Propostas de Melhoria

**🎯 Baseado na sua análise, implemente uma das melhorias:**

**Opção A: Cache Simples**
```python
# Adicione cache em memória no Product Service
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_product_cached(product_id, cache_time):
    # cache_time muda a cada minuto, invalidando o cache
    return get_product_from_db(product_id)

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    cache_time = int(time.time() // 60)  # Cache por 1 minuto
    return get_product_cached(product_id, cache_time)
```

**Opção B: Retry com Backoff**
```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Retry {attempt + 1}/{max_retries} in {wait_time:.2f}s")
            time.sleep(wait_time)
```

---

## 🎓 **ETAPA 6: Reflexão e Próximos Passos (15 minutos)**

### 6.1 Autoavaliação

**✅ Checklist de Aprendizagem:**
- [ ] Executei com sucesso uma arquitetura de microsserviços
- [ ] Entendi como funciona o Database per Service
- [ ] Observei comunicação síncrona entre serviços
- [ ] Implementei um novo endpoint com comunicação inter-serviços
- [ ] Testei cenários de falha e resiliência
- [ ] Coletei e analisei métricas de performance
- [ ] Identifiquei gargalos e propus melhorias

### 6.2 Questões de Reflexão

**📝 Responda em suas próprias palavras:**

1. **Arquitetura:**
   - Quais são as principais diferenças entre monolito e microsserviços?
   - Quando você recomendaria microsserviços vs. monolito?

2. **Operações:**
   - Que desafios operacionais você identificou?
   - Como você resolveria o problema de debugging distribuído?

3. **Dados:**
   - Como você implementaria relatórios que precisam de dados de múltiplos serviços?
   - Que estratégias usaria para manter consistência de dados?

### 6.3 Próximos Desafios

**🚀 Para continuar aprendendo:**

**Nível Intermediário:**
- [ ] Implementar autenticação JWT
- [ ] Adicionar cache distribuído (Redis)
- [ ] Configurar load balancer (Nginx)
- [ ] Implementar health checks avançados

**Nível Avançado:**
- [ ] Event-driven architecture com message queues
- [ ] Service mesh (Istio)
- [ ] Distributed tracing (Jaeger)
- [ ] CI/CD pipeline para microsserviços

---

## 🎉 **Parabéns!**

Você completou com sucesso o laboratório de microsserviços! 

**📈 O que você aprendeu:**
- Arquitetura de microsserviços na prática
- Padrões fundamentais (API Gateway, Database per Service)
- Comunicação entre serviços
- Resiliência e tratamento de falhas
- Monitoramento e observabilidade
- Análise de performance

**🔄 Continue praticando:**
- Experimente com diferentes cenários de falha
- Implemente as melhorias sugeridas
- Explore ferramentas mais avançadas
- Aplique os conceitos em projetos reais

**Desenvolvido para Engenharia de Software** 🎓