import { useEffect, useRef } from 'react'
import { connectWebSocket } from '@/services/websocket'
import { useRecipeStore } from '@/store/recipeStore'

export function useWebSocket(orderId: string | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const updateTimeline = useRecipeStore((s) => s.updateTimeline)
  const setStatus = useRecipeStore((s) => s.setStatus)
  const setResult = useRecipeStore((s) => s.setResult)

  useEffect(() => {
    if (!orderId) return

    wsRef.current = connectWebSocket(orderId, (data) => {
      if (data.type === 'progress') {
        const statusMap: Record<string, 'pending' | 'running' | 'done'> = {
          started: 'running',
          completed: 'done',
        }
        const status = statusMap[data.status] || 'pending'
        updateTimeline({
          id: data.step,
          label: data.step.charAt(0).toUpperCase() + data.step.slice(1),
          status,
        })
      } else if (data.type === 'result_ready') {
        setResult(data.result)
        setStatus('done')
      } else if (data.type === 'chips_ready') {
        // já tratado na Fase 1
      }
    })

    return () => {
      wsRef.current?.close()
    }
  }, [orderId, updateTimeline, setStatus, setResult])
}