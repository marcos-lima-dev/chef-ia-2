const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function createOrder(message: string) {
  const res = await fetch(`${API_BASE}/orders/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) {
    const text = await res.text()
    console.error('❌ createOrder erro:', text)
    throw new Error(text)
  }
  return res.json()
}

export async function confirmOrder(orderId: string, chips: any[]) {
  const res = await fetch(`${API_BASE}/orders/${orderId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chips }),
  })
  if (!res.ok) {
    const text = await res.text()
    console.error('❌ confirmOrder erro:', text)
    throw new Error(text)
  }
  return res.json()
}

export async function getResult(orderId: string) {
  const res = await fetch(`${API_BASE}/orders/${orderId}/result`)
  if (!res.ok) {
    const text = await res.text()
    console.error('❌ getResult erro:', text)
    throw new Error(text)
  }
  return res.json()
}
