import { useEffect, useState, useRef, useCallback } from 'react';
import { useAuth } from './useAuth';

class RealtimeService {
  private ws: WebSocket | null = null;
  private token: string | null = null;
  private orgId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private baseDelay = 1000;
  private intentionalClose = false;
  private listeners: Map<string, Set<(payload: any) => void>> = new Map();

  connect(token: string, orgId: string) {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.token = token;
    this.orgId = orgId;
    this.intentionalClose = false;

    const baseUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/api/v1/realtime/ws";
    const wsUrl = `${baseUrl}?token=${token}&org_id=${orgId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      window.dispatchEvent(new CustomEvent('realtime_connection_change', { detail: { isConnected: true } }));
    };

    this.ws.onclose = () => {
      this.ws = null;
      window.dispatchEvent(new CustomEvent('realtime_connection_change', { detail: { isConnected: false } }));
      
      if (!this.intentionalClose) {
        this.reconnect();
      }
    };

    this.ws.onerror = (e) => {
      console.error("WS Error:", e);
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && data.type) {
          const typeListeners = this.listeners.get(data.type);
          if (typeListeners) {
            typeListeners.forEach(listener => listener(data));
          }
        }
      } catch(e) {}
    };
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    if (!this.token || !this.orgId) return;

    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;
    
    setTimeout(() => {
      if (!this.intentionalClose && this.token && this.orgId) {
        this.connect(this.token, this.orgId);
      }
    }, delay);
  }

  disconnect() {
    this.intentionalClose = true;
    this.token = null;
    this.orgId = null;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(event: string, callback: (payload: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
    return () => {
      const typeListeners = this.listeners.get(event);
      if (typeListeners) {
        typeListeners.delete(callback);
      }
    };
  }
}

const realtimeService = new RealtimeService();

export function useRealtimeConnection(orgId?: string) {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const handleConnectionChange = (e: any) => {
      setIsConnected(e.detail.isConnected);
    };
    
    window.addEventListener('realtime_connection_change', handleConnectionChange);
    return () => window.removeEventListener('realtime_connection_change', handleConnectionChange);
  }, []);

  useEffect(() => {
    if (token && orgId) {
      realtimeService.connect(token, orgId);
    } else {
      realtimeService.disconnect();
    }
    return () => {
      // Don't disconnect on component unmount, let the service handle it globally based on auth state
    };
  }, [token, orgId]);

  return { isConnected };
}

export function useRealtimeEvent(event: string, callback: (payload: any) => void) {
  // Phase 31: keep the latest callback in a ref so the subscription is created
  // once per event type. Previously the effect deps included `callback`, so
  // inline/memoized-but-changing callbacks churned the listener set on every
  // render (duplicate subscribe/unsubscribe cycles).
  const callbackRef = useRef(callback);
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    return realtimeService.subscribe(event, (payload) => callbackRef.current(payload));
  }, [event]);
}
