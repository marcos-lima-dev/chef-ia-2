from app.api.websocket.manager import ConnectionManager

# Instância global do gerenciador (singleton)
manager = ConnectionManager()

class WebSocketPublisher:
    """Publica eventos do workflow no WebSocket."""

    @staticmethod
    async def publish_step_started(order_id: str, step: str):
        await manager.send_progress(order_id, step, "started")

    @staticmethod
    async def publish_step_completed(order_id: str, step: str, data: dict = None):
        await manager.send_progress(order_id, step, "completed", data)

    @staticmethod
    async def publish_chips(order_id: str, chips: list):
        await manager.send_chips(order_id, chips)

    @staticmethod
    async def publish_decision(order_id: str, question: str, options: list):
        await manager.send_decision_request(order_id, question, options)

    @staticmethod
    async def publish_result(order_id: str, result: dict):
        await manager.send_result(order_id, result)
