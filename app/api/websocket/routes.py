from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.manager import manager  # 🔥 importa a instância global (NÃO CRIE UMA NOVA!)
import json

router = APIRouter()

@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    order_id: str,
):
    await manager.connect(websocket, order_id)
    print(f">>> [WS] Cliente conectado ao pedido {order_id}")

    try:
        while True:
            # Mantém a conexão aberta
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, order_id)
        print(f">>> [WS] Cliente desconectado do pedido {order_id}")
