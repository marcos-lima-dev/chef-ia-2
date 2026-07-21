cat > README.md << 'EOF'
# 🍳 Chefe IA 2

**Motor de orquestração multiagente** para processar pedidos culinários em linguagem natural, coordenar especialistas de IA e entregar uma proposta validada com total transparência.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.46-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 Sobre o Projeto

O **Chefe IA** é um sistema de workflow onde agentes especializados colaboram para transformar um pedido em uma receita validada. O cliente é parte ativa do processo, confirmando intenções e tomando decisões quando necessário.

### 🔑 Funcionalidades

- ✅ **Resolução de entidades culinárias** – transforma "caracol" em "escargot" e rejeita "martelo".
- ✅ **Catálogo de ingredientes** – base própria com dados da Wikidata e Open Food Facts.
- ✅ **Confirmação por chips** – cliente valida a interpretação antes da execução.
- ✅ **Geração de receitas** – chef cria uma proposta personalizada.
- ✅ **Análise nutricional** – especialista avalia calorias, macros e adequação.
- ✅ **Coordenação de especialistas** – Maestro decide quem consultar com base nas intenções.
- ✅ **Transparência total** – cada etapa é registrada e exibida em tempo real via WebSocket.
- ✅ **Persistência em PostgreSQL** – dados sobrevivem a reinícios.
- ✅ **API REST + WebSocket** – para integração e streaming.
- ✅ **Frontend moderno** – Next.js, Tailwind, Framer Motion.

---

## 🧠 Arquitetura
Usuário
│
▼
API (FastAPI)
│
▼
Intent Analyzer (extrai tokens)
│
▼
Ingredient Specialist (resolve entidades)
│ ├── Catálogo (PostgreSQL)
│ ├── Fuzzy (RapidFuzz)
│ └── Fallback LLM (classifica alimentos)
│
▼
Frontend (chips + revisão)
│
▼
Chef (gera receita)
│
▼
Maestro (coordena especialistas)
│
▼
Especialistas (Nutritionist, Ingredients, Cost, Time, etc.)
│
▼
Editor (formata resposta)
│
▼
Entrega (HTTP + WebSocket)

text

**Agentes principais:**

| Agente | Responsabilidade |
|--------|------------------|
| **Intent Analyzer** | Extrai intenções (objetivos, ingredientes, restrições). |
| **Ingredient Specialist** | Resolve entidades culinárias (4 estados: resolved, suggested, unknown, rejected). |
| **Chef** | Cria a receita. |
| **Maestro** | Decide quais especialistas consultar. |
| **Nutritionist** | Avalia calorias, proteínas, carboidratos, gorduras. |
| **Ingredients** | Compatibilidade, substituições, conflitos. |
| **Editor** | Formata resposta final com análises. |

---

## 📊 Estados da Resolução de Ingredientes

| Estado | Significado | Ação no frontend |
|--------|-------------|------------------|
| `resolved` | Entidade encontrada com alta confiança | Vai direto para o Chef. |
| `suggested` | Entidade inferida com alguma incerteza | Exibe sugestão (ex: "caracol → escargot"). |
| `unknown` | Nenhuma entidade encontrada | Pergunta ao usuário se é um alimento. |
| `rejected` | Não pertence ao domínio culinário | Bloqueia e não envia para o Chef. |

---

## 🗂️ Estrutura do Projeto
chefe-ia-2/
├── app/
│ ├── agents/ # Agentes IA (Analista, Chef, Maestro, Especialistas)
│ ├── api/ # Rotas REST e WebSocket
│ ├── core/ # Configurações, LLM Provider, exceções
│ ├── domain/ # Modelos de domínio, enums, máquina de estados
│ ├── infrastructure/ # Banco de dados (SQLAlchemy, modelos do catálogo)
│ ├── services/ # WorkflowManager, IngredientSpecialist, EventPublisher
│ └── workflow/ # LangGraph (grafo, nós, runner)
├── scripts/ # ETL para importar Wikidata e Open Food Facts
├── alembic/ # Migrações do banco
├── frontend/ # Next.js (React) com Tailwind e Framer Motion
├── .env
├── requirements.txt
└── README.md

text

---

## ⚙️ Como Executar

### Pré-requisitos

- Python 3.13+
- PostgreSQL 15 (ou SQLite para testes)
- Chave da OpenAI (para agentes e fallback)

### 1. Clonar o repositório

```bash
git clone https://github.com/marcos-lima-dev/chef-ia-2.git
cd chef-ia-2
2. Criar ambiente virtual e instalar dependências
bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
3. Configurar variáveis de ambiente
Crie um arquivo .env na raiz:

env
# OpenAI
OPENAI_API_KEY=sk-...

# Banco de Dados (PostgreSQL)
DATABASE_URL=postgresql://chefe:chefe123@localhost:5432/chefe_ia
4. Iniciar o PostgreSQL com Docker
bash
docker run -d --name chefe_db \
  -e POSTGRES_USER=chefe \
  -e POSTGRES_PASSWORD=chefe123 \
  -e POSTGRES_DB=chefe_ia \
  -p 5432:5432 \
  postgres:15
5. Rodar as migrações
bash
alembic upgrade head
6. Importar o catálogo de ingredientes (Wikidata + Open Food Facts)
bash
python -m scripts.run_etl
7. Iniciar o backend
bash
uvicorn app.main:app --reload
8. Iniciar o frontend (em outro terminal)
bash
cd frontend
npm install
npm run dev
Acesse:

API: http://localhost:8000

Swagger: http://localhost:8000/docs

Frontend: http://localhost:3000

🧪 Exemplo de Uso (com curl)
1. Criar um pedido
bash
ORDER_ID=$(curl -s -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Quero uma salada leve com tomate e caracol"}' \
  | grep -o '"order_id":"[^"]*"' | cut -d'"' -f4)

echo "Order ID: $ORDER_ID"
2. Conectar ao WebSocket (em outro terminal)
bash
wscat -c ws://localhost:8000/ws/orders/$ORDER_ID
3. Confirmar os chips (após a revisão, via frontend ou HTTP)
bash
curl -X POST http://localhost:8000/api/v1/orders/$ORDER_ID/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "chips": [
      {"id": "intent_0", "label": "tomate", "active": true},
      {"id": "intent_1", "label": "escargot", "active": true}
    ]
  }'
4. Obter o resultado
bash
curl http://localhost:8000/api/v1/orders/$ORDER_ID/result | jq '.'
📊 Status do Projeto
Fase	Componente	Status
1	Estrutura + FastAPI + LangGraph	✅
2	Modelos de Domínio + Máquina de Estados	✅
3	WorkflowManager + Eventos	✅
4	WorkflowRunner (grafo mínimo)	✅
5	Agentes com OpenAI (Analista, Chef, Editor)	✅
6	Maestro + Nutricionista + Ingredientes	✅
7	API REST completa	✅
8	Persistência (PostgreSQL)	✅
9	Ingredient Specialist + Catálogo (ETL)	✅
10	WebSocket (streaming)	✅
11	Frontend (Next.js + Tailwind + Framer Motion)	✅
12	Tela de revisão de ingredientes	✅
13	Observabilidade	⏳ Em breve
14	Deploy	⏳ Em breve
📄 Licença
MIT

📫 Contato
Autor: Marcos Lima

GitHub: marcos-lima-dev

Projeto: Chefe IA 2