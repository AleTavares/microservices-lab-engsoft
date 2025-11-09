# Laboratório Prático: Microsserviços E-commerce

## 🎓 Sobre o Projeto

Este repositório contém um **laboratório prático completo** desenvolvido para a disciplina de **Engenharia de Software**, especificamente para a aula sobre **Arquitetura de Microsserviços**. 

### 📚 Contexto Educacional

O projeto foi criado como material didático para demonstrar na prática os principais conceitos e padrões da arquitetura de microsserviços, permitindo que estudantes:

- **Experimentem** uma arquitetura distribuída real
- **Compreendam** a comunicação entre serviços
- **Observem** os benefícios e desafios dos microsserviços
- **Pratiquem** com tecnologias modernas (Python, Flask, PostgreSQL, Docker)

### 🎯 Objetivos de Aprendizagem

- Contrastar arquiteturas **monolíticas vs. microsserviços**
- Implementar o padrão **Database per Service**
- Demonstrar **comunicação síncrona** entre serviços
- Aplicar o padrão **API Gateway**
- Praticar **containerização** e orquestração
- Entender **isolamento de falhas** e resiliência

### 👨‍🏫 Para Professores

O laboratório inclui:
- **Exercícios práticos** com diferentes níveis de complexidade
- **Guia de respostas** para orientação
- **Scripts automatizados** para facilitar a execução
- **Cenários de falha** para demonstrar resiliência

---

## Arquitetura do Sistema

```
┌─────────────────┐
│     Cliente     │
│   (Browser/     │
│    Mobile)      │
└─────────┬───────┘
          │ HTTP Requests
          ▼
┌─────────────────┐
│   API Gateway   │
│   (Port 3000)   │
│                 │
│ • Rate Limiting │
│ • Routing       │
│ • Logging       │
│ • Health Check  │
└─────────┬───────┘
          │
    ┌─────┼─────┐
    │     │     │
    ▼     ▼     ▼
┌───────┐ ┌───────┐ ┌───────┐
│ User  │ │Product│ │ Order │
│Service│ │Service│ │Service│
│ 3001  │ │ 3002  │ │ 3003  │
└───┬───┘ └───┬───┘ └───┬───┘
    │           │           │
    ▼           ▼           ▼
┌───────┐ ┌───────┐ ┌───────┐
│UserDB │ │ProdDB │ │OrderDB│
│ 5432  │ │ 5433  │ │ 5434  │
│🐘 PG  │ │🐘 PG  │ │🐘 PG  │
└───────┘ └───────┘ └───────┘

┌─────────────────────────────────┐
│        Comunicação              │
├─────────────────────────────────┤
│ Order Service ←→ User Service   │
│ Order Service ←→ Product Service│
│ API Gateway   ←→ All Services   │
└─────────────────────────────────┘
```

## Componentes da Arquitetura

### 🌐 API Gateway (Port 3000)
- **Função:** Ponto único de entrada
- **Responsabilidades:**
  - Roteamento de requisições
  - Rate limiting (100 req/15min)
  - Logging centralizado
  - Health checks agregados
  - Proxy reverso

### 👤 User Service (Port 3001)
- **Domínio:** Gerenciamento de usuários
- **Banco:** PostgreSQL (userdb - Port 5432)
- **Endpoints:**
  - GET /users - Listar usuários
  - POST /users - Criar usuário
  - GET /users/:id - Buscar usuário

### 📦 Product Service (Port 3002)
- **Domínio:** Catálogo e estoque
- **Banco:** PostgreSQL (productdb - Port 5433)
- **Endpoints:**
  - GET /products - Listar produtos
  - POST /products - Criar produto
  - GET /products/:id - Buscar produto
  - PUT /products/:id/stock - Atualizar estoque

### 🛒 Order Service (Port 3003)
- **Domínio:** Processamento de pedidos
- **Banco:** PostgreSQL (orderdb - Port 5434)
- **Comunicação:** HTTP com User e Product Services
- **Endpoints:**
  - GET /orders - Listar pedidos
  - POST /orders - Criar pedido (valida usuário e estoque)
  - GET /orders/:id - Buscar pedido

### 🗄️ Bancos de Dados PostgreSQL
- **user-db:** Port 5432 - Dados de usuários
- **product-db:** Port 5433 - Dados de produtos
- **order-db:** Port 5434 - Dados de pedidos

## Serviços Implementados

### 1. User Service (Port 3001)
- GET /users - Listar usuários
- POST /users - Criar usuário
- GET /users/:id - Buscar usuário

### 2. Product Service (Port 3002)  
- GET /products - Listar produtos
- POST /products - Criar produto
- GET /products/:id - Buscar produto

### 3. Order Service (Port 3003)
- GET /orders - Listar pedidos
- POST /orders - Criar pedido
- GET /orders/:id - Buscar pedido

### 4. API Gateway (Port 3000)
- Roteamento para todos os serviços
- Autenticação básica
- Rate limiting

## 🚀 **Início Rápido**

### 🎯 **Para Estudantes**
```bash
# 1. Clone o repositório
git clone https://github.com/AleTavares/microservices-lab-engsoft.git
cd microservices-lab-engsoft

# 2. Execute o laboratório completo
docker-compose up --build

# 3. Siga o guia autoguiado
# Abra: LABORATORIO_PRATICO.md
```

### 👨🏫 **Para Professores**
```bash
# Preparação da aula
./install-dependencies.sh    # Instalar dependências
docker-compose up --build    # Testar ambiente
./test-api.sh               # Validar funcionamento

# Durante a aula
./start-services.sh         # Iniciar sem Docker (opcional)
./connect-db.sh user        # Demonstrar Database per Service
```

### 🛠️ **Opções de Execução**

**Docker Compose (Recomendado):**
```bash
docker-compose up --build
```

**Scripts Automatizados:**
```bash
./start-services.sh
```

**Execução Manual:**
```bash
# 4 terminais separados
cd user-service && python3 app.py
cd product-service && python3 app.py  
cd order-service && python3 app.py
cd api-gateway && python3 app.py
```

## 🧪 **Validação Rápida**

### ✅ **Health Check**
```bash
# Verificar se todos os serviços estão funcionando
curl http://localhost:3000/api/health/all | jq '.'
```

### 📊 **Teste Automatizado**
```bash
# Script completo de testes
./test-api.sh
```

### 🔧 **Testes Manuais**
```bash
# 1. Criar usuário
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Maria Silva", "email": "maria@email.com"}'

# 2. Criar produto
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Smartphone", "price": 1200.00, "stock": 15}'

# 3. Criar pedido (observe a comunicação entre serviços)
curl -X POST http://localhost:3000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"userId": 1, "productId": 1, "quantity": 2}'
```

### 🐘 **Acessar Bancos PostgreSQL**
```bash
./connect-db.sh user     # Banco de usuários
./connect-db.sh product  # Banco de produtos
./connect-db.sh order    # Banco de pedidos
```

## 🎯 **Conceitos e Padrões Demonstrados**

### 🏢 **Arquitetura**
- ✅ **Decomposição por domínio** - Serviços organizados por capacidade de negócio
- ✅ **API Gateway pattern** - Ponto único de entrada com roteamento
- ✅ **Database per service** - Isolamento completo de dados
- ✅ **Service discovery** - Localização dinâmica de serviços

### 🔗 **Comunicação**
- ✅ **Comunicação síncrona** - HTTP/REST entre serviços
- ✅ **Error handling distribuído** - Tratamento de falhas em cascata
- ✅ **Circuit Breaker** - Resiliência e fallback (implementado no laboratório)
- ✅ **Rate limiting** - Controle de tráfego no gateway

### 🛠️ **Tecnologia**
- ✅ **Python/Flask** - Microsserviços leves e eficientes
- ✅ **PostgreSQL** - Banco relacional com isolamento por serviço
- ✅ **Docker/Docker Compose** - Containerização e orquestração
- ✅ **Volumes persistentes** - Dados mantidos entre restarts

### 📊 **Observabilidade**
- ✅ **Health checks** - Monitoramento de saúde dos serviços
- ✅ **Logging centralizado** - Rastreamento de requisições
- ✅ **Métricas customizadas** - Performance e confiabilidade (laboratório)

---

## 📝 Material Didático

### 🎯 **Para Estudantes - Experiência Autoguiada**

#### **🧪 `LABORATORIO_PRATICO.md` - GUIA PRINCIPAL** ⭐
**Laboratório completo de 140 minutos dividido em 6 etapas:**

1. **⚙️ Configuração (15 min)** - Setup inicial e primeira execução
2. **🔍 Exploração (20 min)** - Database per Service e comunicação
3. **🛠️ Implementação (45 min)** - Código hands-on:
   - Novo endpoint com comunicação inter-serviços
   - Circuit Breaker para resiliência
   - Métricas de monitoramento
4. **🔥 Cenários de Falha (25 min)** - Testes de resiliência e carga
5. **📊 Análise (20 min)** - Coleta de métricas e otimização
6. **🎓 Reflexão (15 min)** - Consolidação e próximos passos

#### **📚 Recursos Complementares:**
- **`EXERCICIOS.md`** - Exercícios práticos estruturados
- **Scripts automatizados** - `./start-services.sh`, `./test-api.sh`, `./connect-db.sh`
- **Documentação técnica** - Explicações detalhadas da arquitetura

### 👨🏫 **Para Professores**
- **`RESPOSTAS_PROFESSOR.md`** - Soluções completas e orientações
- **Cenários de demonstração** - Falhas controladas para ensino
- **Métricas de avaliação** - Checklist de objetivos alcançados
- **Flexibilidade modular** - Etapas podem ser adaptadas conforme tempo

### ⏱️ **Planejamento de Aula**
- **Aula teórica:** 3 horas (conceitos fundamentais)
- **Laboratório autoguiado:** 2h20min (seguindo `LABORATORIO_PRATICO.md`)
- **Discussão e Q&A:** 30 minutos (reflexão e dúvidas)
- **Total sugerido:** 5h50min (pode ser dividido em múltiplas sessões)

---

## 🎆 **Evolução e Próximos Passos**

### 🎯 **Competências Desenvolvidas**
Após completar este laboratório, os estudantes serão capazes de:
- ✅ **Arquitetar** sistemas distribuídos com microsserviços
- ✅ **Implementar** padrões fundamentais (API Gateway, Database per Service)
- ✅ **Diagnosticar** problemas em arquiteturas distribuídas
- ✅ **Avaliar** trade-offs entre monolito e microsserviços
- ✅ **Aplicar** técnicas de resiliência e observabilidade

### 🚀 **Caminhos de Aprofundamento**

**Nível Intermediário:**
- Event-driven architecture com message queues
- Autenticação e autorização distribuída (JWT, OAuth2)
- Cache distribuído (Redis) e CDN
- Load balancing avançado (Nginx, HAProxy)

**Nível Avançado:**
- Padrões CQRS, Event Sourcing e Saga
- Service mesh (Istio, Linkerd)
- Distributed tracing (Jaeger, Zipkin)
- CI/CD para microsserviços com Kubernetes

### 🏆 **Aplicações Práticas**
- Projetos de TCC com arquitetura distribuída
- Estágios em empresas que usam microsserviços
- Contribuições para projetos open source
- Certificações em cloud computing (AWS, Azure, GCP)

---

**🎓 Desenvolvido para Engenharia de Software - Disciplina de Arquitetura de Microsserviços**

*Material didático open source - Contribuições e melhorias são bem-vindas!*