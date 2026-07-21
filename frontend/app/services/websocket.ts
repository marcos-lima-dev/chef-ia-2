export function connectWebSocket(orderId: string, onMessage: (data: any) => void) {
  const ws = new WebSocket(`ws://localhost:8000/ws/orders/${orderId}`)

  ws.onopen = () => console.log('WebSocket conectado')
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch {
      console.warn('Mensagem inválida', event.data)
    }
  }
  ws.onclose = () => console.log('WebSocket desconectado')
  ws.onerror = (error) => console.error('WebSocket erro', error)

  return ws
}