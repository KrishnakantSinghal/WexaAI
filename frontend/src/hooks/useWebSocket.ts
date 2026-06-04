"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/store/authStore";

type WsStatus = "connecting" | "connected" | "disconnected" | "error";

interface UseWebSocketOptions {
  path: string;
  onMessage?: (data: unknown) => void;
  enabled?: boolean;
}

export function useWebSocket({ path, onMessage, enabled = true }: UseWebSocketOptions) {
  const [status, setStatus] = useState<WsStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const token = useAuthStore((s) => s.accessToken);
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

  const connect = useCallback(() => {
    if (!enabled || !token) return;

    const url = `${WS_URL}${path}?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => setStatus("connected");

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch {
        // ignore non-JSON
      }
    };

    ws.onerror = () => setStatus("error");

    ws.onclose = () => {
      setStatus("disconnected");
      // Auto-reconnect after 3s
      reconnectTimeout.current = setTimeout(connect, 3000);
    };
  }, [path, token, enabled, WS_URL, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === "string" ? data : JSON.stringify(data));
    }
  }, []);

  return { status, send };
}
