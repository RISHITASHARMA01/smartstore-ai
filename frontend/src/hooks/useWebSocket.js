import { useEffect, useRef, useCallback } from 'react'

const WS_BASE = (import.meta.env.VITE_WS_URL || 'ws://localhost:8000')

export function useWebSocket(onMessage) {
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(`${WS_BASE}/ws`)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage(data)
        } catch (e) {
          console.error('WebSocket message parse error:', e)
        }
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 3s...')
        reconnectTimeout.current = setTimeout(connect, 3000)
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        ws.current.close()
      }
    } catch (e) {
      console.error('WebSocket connection failed:', e)
    }
  }, [onMessage])

  useEffect(() => {
    connect()
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
      if (ws.current) ws.current.close()
    }
  }, [connect])

  return ws
}
