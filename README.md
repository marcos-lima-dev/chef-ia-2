# 🍳 Chefe IA 2 - Multi Agents!

**Motor de orquestração multiagente** para processar pedidos culinários em linguagem natural, coordenar especialistas de IA e entregar uma proposta validada com total transparência.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.46-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 Sobre o Projeto

O **Chefe IA** não é um chatbot comum. Ele é um sistema de workflow onde agentes especializados colaboram para transformar um pedido em uma receita validada nutricionalmente. O cliente é parte ativa do processo, confirmando intenções e tomando decisões quando necessário.

### 🔑 Funcionalidades

- ✅ **Interpretação inteligente** – extrai objetivos, ingredientes e restrições do pedido.
- ✅ **Confirmação por chips** – cliente valida a interpretação antes da execução.
- ✅ **Geração de receitas** – chef cria uma proposta personalizada.
- ✅ **Análise nutricional** – especialista avalia calorias, macros e adequação.
- ✅ **Coordenação de especialistas** – Maestro decide quem consultar com base nas intenções.
- ✅ **Transparência total** – cada etapa é registrada e exibida.
- ✅ **Persistência em PostgreSQL** – dados sobrevivem a reinícios.
- ✅ **API REST** – fácil integração com frontends.

---

## 🧠 Arquitetura
Cliente → API (FastAPI) → Gerenciador de Fluxo → LangGraph → Agentes (Analista, Chef, Maestro, Nutricionista, Editor) → PostgreSQL

text

**Agentes principais:**

| Agente              | Responsabilidade                                 |
|---------------------|--------------------------------------------------|
| **Analista**        | Extrai intenções (objetivos, ingredientes, restrições) |
| **Chef**            | Cria a receita                                   |
| **Maestro**         | Decide quais especialistas consultar             |
| **Nutricionista**   | Avalia calorias, proteínas, carboidratos, gorduras |
| **Editor**          | Formata resposta final com análises              |

**Máquina de estados:**
RECEBIDO → INTERPRETADO → AGUARDANDO_CONFIRMACAO → EM_ELABORACAO → EM_ANALISE → DECISAO → FINALIZANDO → FINALIZADO

text

---

## 🚀 Tecnologias

- **Backend:** Python 3.13, FastAPI, Pydantic
- **Workflow:** LangGraph (com interrupção/retomada)
- **LLM:** OpenAI (ChatOpenAI) via LangChain
- **Banco:** PostgreSQL + SQLAlchemy + Alembic
- **Cache/Filas:** Redis (futuro)
- **Container:** Docker, Docker Compose

---

## 📁 Estrutura do Projeto
chefe-ia/
├── app/
│ ├── api/ # Rotas e schemas da API
│ ├── agents/ # Agentes (Analista, Chef, Maestro, Especialistas)
│ ├── core/ # Configurações, exceções, provedor LLM
│ ├── domain/ # Modelos de domínio, enums, máquina de estados
│ ├── infrastructure/ # Banco de dados (SQLAlchemy, repositórios)
│ ├── services/ # WorkflowManager, EventPublisher, ChipBuilder
│ └── workflow/ # LangGraph (grafo, nós, runner)
├── alembic/ # Migrações do banco
├── tests/ # Testes unitários e de integração
├── .env # Variáveis de ambiente
├── requirements.txt
├── docker-compose.yml
└── README.md

text

---

## ⚙️ Como Executar

### Pré-requisitos

- Python 3.13+
- PostgreSQL 15 (ou SQLite para testes)
- Chave da OpenAI (para agentes reais)

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
4. Iniciar o PostgreSQL com Docker (ou usar SQLite)
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
6. Iniciar o servidor
bash
uvicorn app.main:app --reload
Acesse a API em: http://localhost:8000
Documentação Swagger: http://localhost:8000/docs

🧪 Exemplo de Uso (com curl)
1. Criar um pedido
bash
ORDER_ID=$(curl -s -X POST http://localhost:8000/api/v1/orders/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Quero uma salada leve com tomate e alface, sem glúten"}' \
  | grep -o '"order_id":"[^"]*"' | cut -d'"' -f4)

echo "Order ID: $ORDER_ID"
2. Confirmar os chips
bash
curl -X POST http://localhost:8000/api/v1/orders/$ORDER_ID/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "chips": [
      {"id": "intent_0", "label": "leve", "active": true},
      {"id": "intent_1", "label": "tomate", "active": true},
      {"id": "intent_2", "label": "alface", "active": true},
      {"id": "intent_3", "label": "sem glúten", "active": true}
    ]
  }' | jq '.'
3. Obter o resultado final
bash
curl http://localhost:8000/api/v1/orders/$ORDER_ID/result | jq '.'
📊 Status do Projeto
Fase	Componente	Status
1	Estrutura + FastAPI + LangGraph	✅
2	Modelos de Domínio + Máquina de Estados	✅
3	WorkflowManager + Eventos	✅
4	WorkflowRunner (grafo mínimo)	✅
5	Agentes com OpenAI (Analista, Chef, Editor)	✅
6	Maestro + Nutricionista	✅
7	API REST completa	✅
8	Persistência (PostgreSQL)	✅
9	WebSocket (streaming)	⏳ Em breve
10	Frontend (React)	⏳ Em breve
11	Observabilidade	⏳ Em breve
12	Escalabilidade	⏳ Em breve
📄 Licença
Este projeto está sob a licença MIT. Consulte o arquivo LICENSE para mais informações.

✨ Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

📫 Contato
Autor: Marcos Lima

GitHub: marcos-lima-dev

Projeto: Chefe IA 2 Multi Agents!

🍽️ Bom apetite e boa codificação!
