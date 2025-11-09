# 🎓 Respostas dos Exercícios - Guia do Professor

## Parte 2: Explorando os Conceitos

### 2.1 Database per Service
**Resposta:** Cada serviço mantém seus dados isoladamente:
- User Service: Lista `users` em memória (linha 10 do app.py)
- Product Service: Lista `products` em memória (linha 10 do app.py)
- Order Service: Lista `orders` em memória (linha 15 do app.py)

**Benefícios demonstrados:**
- Isolamento de dados
- Flexibilidade tecnológica (cada um poderia usar DB diferente)
- Falhas isoladas

### 2.2 Comunicação Síncrona
**Problemas identificados:**
- Se User Service estiver offline → Order Service falha
- Latência acumulada (3 chamadas HTTP sequenciais)
- Acoplamento temporal (todos devem estar online)

**Melhorias sugeridas:**
- Circuit breaker
- Timeout configurável
- Fallback/cache

### 2.3 API Gateway Pattern
**Diferenças:**
- Gateway: `/api/users` → roteamento + rate limiting + logging
- Direto: `/users` → acesso direto ao serviço

**Benefícios demonstrados:**
- Ponto único de entrada
- Rate limiting (100 req/15min)
- Logging centralizado
- Roteamento inteligente

## Parte 3: Modificações Práticas

### 3.1 Novo Endpoint - Solução Completa
```python
# user-service/app.py
import requests
import os

ORDER_SERVICE_URL = os.environ.get('ORDER_SERVICE_URL', 'http://localhost:3003')

@app.route('/users/<int:user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    # Verificar se usuário existe
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    try:
        # Buscar pedidos do usuário
        orders_response = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=5)
        user_orders = [order for order in orders_response.json() if order["userId"] == user_id]
        
        return jsonify({
            "user": user,
            "orders": user_orders,
            "totalOrders": len(user_orders)
        })
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar pedidos: {str(e)}")
        return jsonify({"error": "Erro ao buscar pedidos do usuário"}), 500
```

### 3.2 Circuit Breaker - Implementação
```python
# order-service/app.py
import time
import threading

circuit_breaker = {
    "failures": 0,
    "threshold": 3,
    "timeout": 30,  # segundos
    "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
    "last_failure": 0
}

def call_service_with_circuit_breaker(url, fallback_data):
    current_time = time.time()
    
    # Verificar se deve abrir o circuit breaker
    if (circuit_breaker["state"] == "OPEN" and 
        current_time - circuit_breaker["last_failure"] < circuit_breaker["timeout"]):
        print("Circuit breaker OPEN, usando fallback")
        return fallback_data
    
    # Tentar half-open se timeout passou
    if circuit_breaker["state"] == "OPEN":
        circuit_breaker["state"] = "HALF_OPEN"
    
    try:
        response = requests.get(url, timeout=5)
        circuit_breaker["failures"] = 0
        circuit_breaker["state"] = "CLOSED"
        return response.json()
    except requests.exceptions.RequestException as e:
        circuit_breaker["failures"] += 1
        circuit_breaker["last_failure"] = current_time
        
        if circuit_breaker["failures"] >= circuit_breaker["threshold"]:
            circuit_breaker["state"] = "OPEN"
        
        print(f"Falha no serviço ({circuit_breaker['failures']}/{circuit_breaker['threshold']})")
        return fallback_data
```

### 3.3 Logging Distribuído - Implementação
```python
# api-gateway/app.py
import uuid
from datetime import datetime
from flask import g

@app.before_request
def add_request_id():
    request_id = f"req_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    g.request_id = request_id
    print(f"[{request_id}] {request.method} {request.path}")
    
    # Adicionar aos headers para propagar
    if hasattr(request, 'headers'):
        request.headers = dict(request.headers)
        request.headers['X-Request-ID'] = request_id

# Nos outros serviços
@app.before_request
def log_request_with_id():
    request_id = request.headers.get('X-Request-ID', 'unknown')
    print(f"[{request_id}] {request.method} {request.path}")
```

## Parte 4: Cenários de Falha

### 4.1 Teste de Resiliência
**Comportamento esperado:**
- Order Service retorna erro 500
- API Gateway pode retornar 503 (Service Unavailable)
- Logs mostram erro de conexão

**Melhorias sugeridas:**
- Implementar retry com backoff
- Cache de dados críticos
- Graceful degradation

### 4.2 Teste de Escalabilidade
**Observações:**
- Todas as requisições vão para uma única instância
- Possível gargalo na porta 3002
- Necessidade de load balancer

**Soluções:**
```bash
# Escalar Product Service
docker-compose up --scale product-service=3

# Ou manualmente
PORT=3004 npm start & # Segunda instância
PORT=3005 npm start & # Terceira instância
```

## Parte 5: Melhorias Avançadas

### 5.1 Sistema de Eventos - Implementação Completa
```javascript
// shared/events.js
class EventBus {
  constructor() {
    this.events = [];
    this.subscribers = new Map();
  }

  publish(eventType, data) {
    const event = {
      id: Date.now() + Math.random(),
      type: eventType,
      data,
      timestamp: new Date().toISOString()
    };
    
    this.events.push(event);
    
    // Notificar subscribers
    const handlers = this.subscribers.get(eventType) || [];
    handlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error(`Erro no handler do evento ${eventType}:`, error);
      }
    });
  }

  subscribe(eventType, handler) {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, []);
    }
    this.subscribers.get(eventType).push(handler);
  }
}

// Uso no Order Service
eventBus.subscribe('order.created', (event) => {
  console.log(`📧 Enviando email para pedido ${event.data.orderId}`);
});

// Publicar evento após criar pedido
eventBus.publish('order.created', { orderId: order.id, userId: order.userId });
```

### 5.2 Monitoramento - Implementação
```javascript
// shared/metrics.js
class MetricsCollector {
  constructor() {
    this.metrics = {
      requests: 0,
      errors: 0,
      responseTimes: [],
      endpoints: new Map()
    };
  }

  recordRequest(endpoint, duration, statusCode) {
    this.metrics.requests++;
    this.metrics.responseTimes.push(duration);
    
    if (statusCode >= 400) {
      this.metrics.errors++;
    }

    // Métricas por endpoint
    if (!this.metrics.endpoints.has(endpoint)) {
      this.metrics.endpoints.set(endpoint, { count: 0, avgTime: 0 });
    }
    
    const endpointMetrics = this.metrics.endpoints.get(endpoint);
    endpointMetrics.count++;
    endpointMetrics.avgTime = (endpointMetrics.avgTime + duration) / 2;
  }

  getMetrics() {
    return {
      ...this.metrics,
      avgResponseTime: this.metrics.responseTimes.reduce((a, b) => a + b, 0) / this.metrics.responseTimes.length || 0,
      errorRate: (this.metrics.errors / this.metrics.requests) * 100 || 0,
      endpoints: Object.fromEntries(this.metrics.endpoints)
    };
  }
}

// Middleware para coletar métricas
const metricsCollector = new MetricsCollector();

app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    metricsCollector.recordRequest(req.path, duration, res.statusCode);
  });
  
  next();
});

app.get('/metrics', (req, res) => {
  res.json(metricsCollector.getMetrics());
});
```

## Discussão - Pontos Importantes

### 1. Complexidade vs. Benefícios
**Quando compensam:**
- Equipes > 8 pessoas
- Necessidade de escalar partes específicas
- Domínios bem definidos
- Maturidade em DevOps

**Problemas identificados:**
- Debugging complexo
- Latência de rede
- Consistência de dados
- Complexidade operacional

### 2. Decisões Arquiteturais
**HTTP vs. gRPC:**
- HTTP: Mais simples, debugging fácil, compatibilidade
- gRPC: Performance, type safety, streaming

**Síncrono vs. Assíncrono:**
- Síncrono: Consultas, validações imediatas
- Assíncrono: Eventos, processamento background, resiliência

### 3. Operações
**Deploy:**
- CI/CD independente por serviço
- Blue-green deployment
- Canary releases

**Debugging:**
- Correlation IDs
- Distributed tracing (Jaeger, Zipkin)
- Centralized logging (ELK Stack)

### 4. Dados
**Relatórios:**
- API de agregação
- Data lake/warehouse
- Event sourcing + CQRS

**Consistência:**
- Eventual consistency
- Saga pattern
- Compensating transactions

## Métricas de Sucesso do Laboratório

### Alunos devem conseguir:
- ✅ Executar todos os 4 serviços
- ✅ Criar usuário, produto e pedido via API
- ✅ Explicar comunicação entre serviços
- ✅ Identificar pontos de falha
- ✅ Propor melhorias arquiteturais

### Conceitos demonstrados:
- ✅ Decomposição por domínio
- ✅ Database per service
- ✅ API Gateway pattern
- ✅ Service-to-service communication
- ✅ Failure isolation
- ✅ Independent deployment