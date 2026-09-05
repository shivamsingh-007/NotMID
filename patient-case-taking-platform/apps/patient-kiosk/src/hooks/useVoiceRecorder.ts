"use client";

import { useState, useRef, useCallback, useSyncExternalStore } from "react";

const subscribeToRecorderSupport = () => () => undefined;
const getServerRecorderSupport = () => false;
const getRecorderSupport = () =>
  typeof navigator !== "undefined" &&
  Boolean(
    navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === "function"
  );

interface UseVoiceRecorderOptions {
  language?: string;
  sampleRate?: number;
  chunkSize?: number;
  deviceId?: string;
}

interface UseVoiceRecorderReturn {
  isRecording: boolean;
  isSupported: boolean;
  stream: MediaStream | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob>;
  cancelRecording: () => void;
  error: string | null;
}

export function useVoiceRecorder(
  options: UseVoiceRecorderOptions = {}
): UseVoiceRecorderReturn {
  const { sampleRate = 16000, chunkSize = 100, deviceId } = options;
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const isSupported = useSyncExternalStore(
    subscribeToRecorderSupport,
    getRecorderSupport,
    getServerRecorderSupport
  );

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = useCallback(async () => {
    if (!isSupported) {
      setError("Microphone access is not supported in this browser");
      return;
    }

    try {
      setError(null);
      chunksRef.current = [];

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
        },
      });

      setStream(mediaStream);

      const preferredType = "audio/webm;codecs=opus";
      const mediaRecorder = MediaRecorder.isTypeSupported(preferredType)
        ? new MediaRecorder(mediaStream, { mimeType: preferredType })
        : new MediaRecorder(mediaStream);

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(chunkSize);
      setIsRecording(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to start recording";
      setError(message);
      throw new Error(message);
    }
  }, [isSupported, sampleRate, chunkSize, deviceId]);

  const stopRecording = useCallback(async (): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        reject(new Error("No active recording"));
        return;
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "application/octet-stream",
        });
        chunksRef.current = [];
        setIsRecording(false);

        stream?.getTracks().forEach((t) => t.stop());
        setStream(null);

        resolve(blob);
      };

      recorder.stop();
    });
  }, [stream]);

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    chunksRef.current = [];
    setIsRecording(false);
    stream?.getTracks().forEach((t) => t.stop());
    setStream(null);
  }, [stream]);

  return {
    isRecording,
    isSupported,
    stream,
    startRecording,
    stopRecording,
    cancelRecording,
    error,
  };
}
