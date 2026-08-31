"use client";

import { useState, useRef, useCallback, useEffect } from "react";

interface UseASROptions {
  language?: string;
  wsUrl?: string;
  context: {
    tenantId: string;
    sessionId: string;
    encounterId: string;
    consentId: string;
    retainAudio: boolean;
    audioRetentionConsent: boolean;
  };
}

interface UseASRReturn {
  transcript: string;
  interimTranscript: string;
  confidence: number | null;
  needsClarification: boolean;
  signalQuality: number | null;
  isListening: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  sendAudio: (chunk: Blob) => void;
  endAudio: () => void;
  reset: () => void;
}

export function useASR(options: UseASROptions): UseASRReturn {
  const {
    language = "hi",
    wsUrl,
    context,
  } = options;

  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [needsClarification, setNeedsClarification] = useState(false);
  const [signalQuality, setSignalQuality] = useState<number | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef<Array<Blob | string>>([]);
  const sendChainRef = useRef(Promise.resolve());

  const queueSend = useCallback((ws: WebSocket, message: Blob | string) => {
    sendChainRef.current = sendChainRef.current.then(async () => {
      if (ws.readyState !== WebSocket.OPEN) return;
      ws.send(typeof message === "string" ? message : await message.arrayBuffer());
    });
  }, []);

  const connect = useCallback(() => {
    try {
      setError(null);
      const defaultUrl = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/asr`;
      const endpoint = wsUrl || process.env.NEXT_PUBLIC_ASR_WS_URL || defaultUrl;
      const query = new URLSearchParams({
        language,
        tenant_id: context.tenantId,
        session_id: context.sessionId,
        encounter_id: context.encounterId,
        consent_id: context.consentId,
        retain_audio: String(context.retainAudio),
        audio_retention_consent: String(context.audioRetentionConsent),
      });
      const ws = new WebSocket(`${endpoint}?${query}`);

      ws.onopen = () => {
        setIsListening(true);
        const queued = pendingRef.current;
        pendingRef.current = [];
        for (const message of queued) queueSend(ws, message);
      };

      ws.onmessage = (event) => {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch {
          setError("Voice service returned an invalid response");
          return;
        }

        if (data.type === "transcript") {
          if (data.is_final) {
            setTranscript(data.text);
            setInterimTranscript("");
          } else {
            setInterimTranscript(data.text);
          }
          setConfidence(typeof data.confidence === "number" ? data.confidence : null);
          setSignalQuality(
            typeof data.signal_quality?.score === "number" ? data.signal_quality.score : null
          );
          setNeedsClarification(Boolean(data.needs_clarification));
        } else if (data.type === "done") {
          setIsListening(false);
          if (data.result?.text) {
            setTranscript(data.result.text);
          }
          setNeedsClarification(Boolean(data.result?.needs_clarification));
        } else if (data.type === "error") {
          setError(data.detail);
          setIsListening(false);
        }
      };

      ws.onerror = () => {
        setError("WebSocket connection failed");
        setIsListening(false);
      };

      ws.onclose = () => {
        setIsListening(false);
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect");
    }
  }, [context, language, queueSend, wsUrl]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    pendingRef.current = [];
    sendChainRef.current = Promise.resolve();
    setIsListening(false);
  }, []);

  const sendAudio = useCallback((chunk: Blob) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      queueSend(wsRef.current, chunk);
    } else if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      pendingRef.current.push(chunk);
    }
  }, [queueSend]);

  const endAudio = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      queueSend(wsRef.current, JSON.stringify({ type: "end" }));
    } else if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      pendingRef.current.push(JSON.stringify({ type: "end" }));
    }
  }, [queueSend]);

  const reset = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
    setConfidence(null);
    setNeedsClarification(false);
    setSignalQuality(null);
    setError(null);
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    transcript,
    interimTranscript,
    confidence,
    needsClarification,
    signalQuality,
    isListening,
    error,
    connect,
    disconnect,
    sendAudio,
    endAudio,
    reset,
  };
}
