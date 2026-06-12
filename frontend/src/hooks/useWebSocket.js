import { useEffect, useRef } from 'react'

const WS_BASE = import.meta.env.VITE_WS_URL || (() => {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}`
})()

export function useWebSocket(onMessage) {
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)
  const onMessageRef = useRef(onMessage)

  // Keep the callback ref current so message handler always calls the latest version
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    function connect() {
      const token = localStorage.getItem('access_token')
      if (!token) return
      try {
        ws.current = new WebSocket(`${WS_BASE}/ws?token=${encodeURIComponent(token)}`)

        ws.current.onopen = () => console.log('WebSocket connected')

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            onMessageRef.current(data)
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
          ws.current?.close()
        }
      } catch (e) {
        console.error('WebSocket connection failed:', e)
      }
    }

    connect()
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
      if (ws.current) ws.current.close()
    }
  }, []) // connect is defined inside the effect — no stale-closure risk

  return ws
}
