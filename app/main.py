from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import orders
from app.api.websocket import routes as websocket_routes

app = FastAPI(
    title="Chefe IA",
    version="1.0.0",
    debug=settings.debug,
)

# 🔥 Configuração CORS (necessário para WebSocket e requisições do frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja para domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(websocket_routes.router)  # 🔥 ESSA LINHA É CRUCIAL

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.environment}
