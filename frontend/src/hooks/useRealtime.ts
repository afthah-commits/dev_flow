import { useEffect, useState, useRef } from 'react';
import { useAuth } from './useAuth';

export function useRealtime(orgId?: string) {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token || !orgId) return;

    const wsUrl = `ws://localhost:8000/api/v1/ws?token=${token}&org_id=${orgId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = (e) => console.error("WS Error:", e);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        window.dispatchEvent(new CustomEvent('realtime_event', { detail: data }));
      } catch(e) {}
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [token, orgId]);

  return { isConnected };
}
