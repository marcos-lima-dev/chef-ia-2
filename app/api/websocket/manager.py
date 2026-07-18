from typing import Dict, Set, List
from fastapi import WebSocket
import json


class ConnectionManager:
    """Gerencia conexões WebSocket ativas."""

    def __init__(self):
        # Mapeia order_id -> conjunto de websockets ativos
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, order_id: str):
        """Aceita uma nova conexão e a associa a um pedido."""
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = set()
        self.active_connections[order_id].add(websocket)

    def disconnect(self, websocket: WebSocket, order_id: str):
        """Remove uma conexão."""
        if order_id in self.active_connections:
            self.active_connections[order_id].discard(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]

    async def send_message(self, order_id: str, message: dict):
        """Envia uma mensagem JSON para todos os clientes conectados a um pedido."""
        if order_id not in self.active_connections:
            return
        data = json.dumps(message, default=str)
        for connection in self.active_connections[order_id]:
            try:
                await connection.send_text(data)
            except Exception:
                # Se falhar, remove a conexão (será tratada no disconnect)
                pass

    async def send_progress(self, order_id: str, step: str, status: str, data: dict = None):
        """Envia um evento de progresso padronizado."""
        await self.send_message(order_id, {
            "type": "progress",
            "step": step,
            "status": status,
            "data": data or {},
        })

    async def send_chips(self, order_id: str, chips: List[dict]):
        """Envia os chips para confirmação."""
        await self.send_message(order_id, {
            "type": "chips_ready",
            "chips": chips,
        })

    async def send_decision_request(self, order_id: str, question: str, options: List[str]):
        """Solicita uma decisão do cliente."""
        await self.send_message(order_id, {
            "type": "decision_required",
            "question": question,
            "options": options,
        })

    async def send_result(self, order_id: str, result: dict):
        """Envia o resultado final."""
        await self.send_message(order_id, {
            "type": "result_ready",
            "result": result,
        })

# Instância global (singleton) do gerenciador
manager = ConnectionManager()