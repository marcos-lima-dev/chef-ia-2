from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.api.websocket.manager import ConnectionManager
from app.services.order_orchestrator_persistent import OrderOrchestratorPersistent
from app.infrastructure.database.base import get_db
from sqlalchemy.orm import Session
import asyncio

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    order_id: str,
):
    """
    Endpoint WebSocket para acompanhar um pedido em tempo real.

    O cliente se conecta e recebe eventos de progresso, chips, decisões e resultado.
    """
    await manager.connect(websocket, order_id)

    # Opcional: enviar o estado atual do pedido ao conectar
    # (pode ser implementado depois)

    try:
        # Mantém a conexão aberta ouvindo mensagens do cliente (para futuros comandos)
        while True:
            # Aguarda mensagens do cliente (pode ser usado para confirmação via WS)
            # Por enquanto, apenas mantém a conexão viva
            data = await websocket.receive_text()
            # Se quiser processar confirmações via WS, pode implementar aqui
            # Exemplo: se data for {"action": "confirm", "chips": [...]}
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, order_id)
