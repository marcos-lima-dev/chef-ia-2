from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import orders

app = FastAPI(
    title="Chefe IA",
    version="1.0.0",
    debug=settings.debug,
)

app.include_router(orders.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.environment}
