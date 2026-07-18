import asyncio
import json
import httpx
import websockets

ORDER_URL = "http://localhost:8000/api/v1/orders/"
WS_URL = "ws://localhost:8000/ws/orders"

async def main():
    # 1. Cria pedido
    print("📝 Criando pedido...")
    async with httpx.AsyncClient(timeout=60.0) as client:  # 🔥 timeout maior
        resp = await client.post(ORDER_URL, json={"message": "Quero uma salada leve com tomate"})
        data = resp.json()
        order_id = data["order_id"]
        print(f"✅ Pedido criado: {order_id}")

        intentions = data.get("intentions", [])
        print(f"📋 Intenções: {[i['value'] for i in intentions]}")

    # 2. Conecta WebSocket
    print(f"🔌 Conectando WebSocket...")
    ws = await websockets.connect(f"{WS_URL}/{order_id}")
    print("✅ Conectado! Aguardando mensagens...\n")

    # 3. Confirma os chips (após 1s para garantir conexão)
    async def confirm():
        await asyncio.sleep(1)
        chips = [{"id": f"intent_{i}", "label": intent["value"], "active": True} 
                 for i, intent in enumerate(intentions)]
        print(f"📤 Confirmando: {[c['label'] for c in chips]}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{ORDER_URL}{order_id}/confirm", json={"chips": chips})
            print(f"✅ Confirmação enviada (status {resp.status_code})")

    asyncio.create_task(confirm())

    # 4. Escuta mensagens
    try:
        async for msg in ws:
            print(f"📩 {msg}")
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Conexão encerrada")

if __name__ == "__main__":
    asyncio.run(main())
