# 🎯 Exercícios Práticos - Laboratório de Microsserviços

## Parte 1: Executando o Sistema (15 min)

### 1.1 Inicialização
```bash
# Opção 1: Scripts automatizados
./start-services.sh

# Opção 2: Docker Compose
docker-compose up --build

# Opção 3: Manual (4 terminais)
cd user-service && pip3 install -r requirements.txt && python3 app.py
cd product-service && pip3 install -r requirements.txt && python3 app.py
cd order-service && pip3 install -r requirements.txt && python3 app.py
cd api-gateway && pip3 install -r requirements.txt && python3 app.py
```

### 1.2 Verificação
- Acesse: http://localhost:3000/api/health/all
- Execute: `./test-api.sh`

## Parte 2: Explorando os Conceitos (20 min)

### 2.1 Database per Service
**Questão:** Onde estão armazenados os dados de cada serviço?
- [ ] User Service: `users` array em memória
- [ ] Product Service: `products` array em memória  
- [ ] Order Service: `orders` array em memória

**Experimento:** 
1. Crie um usuário via API Gateway
2. Tente acessar diretamente o User Service (porta 3001)
3. Compare as respostas

### 2.2 Comunicação Síncrona
**Analise o código:** `order-service/app.py` linha ~45
```python
# Como o Order Service se comunica com outros serviços?
user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}", timeout=5)
product_response = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
```

**Questões:**
- O que acontece se o User Service estiver offline?
- Como isso demonstra acoplamento temporal?

### 2.3 API Gateway Pattern
**Experimento:**
```bash
# Via API Gateway
curl http://localhost:3000/api/users

# Diretamente no serviço
curl http://localhost:3001/users
```

**Questões:**
- Qual a diferença nas URLs?
- Que benefícios o Gateway oferece?

## Parte 3: Modificações Práticas (30 min)

### 3.1 Adicionar Novo Endpoint
**Tarefa:** Adicione um endpoint `GET /users/<int:user_id>/orders` no User Service

**Dicas:**
```python
@app.route('/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    # Chamar Order Service para buscar pedidos do usuário
    # URL: ORDER_SERVICE_URL + '/orders'
    # Filtrar por userId
    pass
```

### 3.2 Implementar Circuit Breaker Simples
**Tarefa:** No Order Service, adicione tratamento para quando serviços estão offline

```python
def call_service_with_fallback(url, fallback_data):
    try:
        response = requests.get(url, timeout=2)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Serviço indisponível, usando fallback: {url}")
        return fallback_data
```

### 3.3 Adicionar Logging Distribuído
**Tarefa:** Adicione um `requestId` que seja propagado entre serviços

```python
# No API Gateway
import uuid

@app.before_request
def add_request_id():
    request.request_id = f"req_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    print(f"[{request.request_id}] {request.method} {request.path}")
```

## Parte 4: Cenários de Falha (20 min)

### 4.1 Teste de Resiliência
```bash
# 1. Pare o Product Service
kill $(lsof -ti:3002)

# 2. Tente criar um pedido
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId": 1, "productId": 1, "quantity": 1}'

# 3. Observe o comportamento
```

**Questões:**
- O que aconteceu?
- Como melhorar a resiliência?

### 4.2 Teste de Escalabilidade
```bash
# Simular carga no Product Service
for i in {1..50}; do
  curl -s http://localhost:3000/api/products > /dev/null &
done
```

**Questões:**
- Como escalar apenas o Product Service?
- Que métricas observar?

## Parte 5: Melhorias Avançadas (25 min)

### 5.1 Implementar Comunicação Assíncrona
**Tarefa:** Simule um sistema de eventos simples

```python
# events.py - Sistema de eventos simples
from datetime import datetime
import time

events = []

def publish_event(event_type, data):
    event = {
        "id": int(time.time() * 1000),
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    events.append(event)
    print(f"📢 Evento publicado: {event_type}")

def get_events(event_type):
    return [e for e in events if e["type"] == event_type]
```

### 5.2 Adicionar Monitoramento
**Tarefa:** Implemente métricas básicas

```python
# metrics.py
metrics = {
    "requests": 0,
    "errors": 0,
    "response_time": []
}

def record_request(duration, error=False):
    metrics["requests"] += 1
    if error:
        metrics["errors"] += 1
    metrics["response_time"].append(duration)

@app.route('/metrics', methods=['GET'])
def get_metrics():
    avg_time = sum(metrics["response_time"]) / len(metrics["response_time"]) if metrics["response_time"] else 0
    return jsonify({
        **metrics,
        "avg_response_time": avg_time
    })
```

### 5.3 Implementar Service Discovery
**Tarefa:** Crie um registro simples de serviços

```python
# registry.py
import time

services = {}

def register_service(name, url):
    services[name] = {
        "url": url,
        "last_seen": int(time.time() * 1000)
    }

def discover_service(name):
    service = services.get(name)
    return service["url"] if service else None
```

## Parte 6: Reflexão e Discussão (10 min)

### Questões para Discussão:

1. **Complexidade vs. Benefícios:**
   - Quando a complexidade dos microsserviços compensa?
   - Que problemas você identificou neste laboratório?

2. **Decisões Arquiteturais:**
   - Por que usar HTTP em vez de gRPC?
   - Quando usar comunicação síncrona vs. assíncrona?

3. **Operações:**
   - Como fazer deploy de 4 serviços independentes?
   - Como debugar um problema que atravessa múltiplos serviços?

4. **Dados:**
   - Como fazer relatórios que precisam de dados de múltiplos serviços?
   - Como garantir consistência de dados?

### Próximos Passos:
- [ ] Implementar autenticação JWT
- [ ] Adicionar cache (Redis)
- [ ] Configurar load balancer (Nginx)
- [ ] Implementar health checks avançados
- [ ] Adicionar testes automatizados
- [ ] Configurar CI/CD pipeline

## 🎉 Parabéns!
Você completou o laboratório de microsserviços e experimentou na prática os principais conceitos da arquitetura distribuída!