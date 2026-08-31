"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { TouchButton } from "./TouchButton";

interface AudioPromptProps {
  text: string;
  audioSrc?: string;
  language?: string;
  autoPlay?: boolean;
  onPlay?: () => void;
}

export function AudioPrompt({
  text,
  audioSrc,
  language = "hi",
  autoPlay = false,
  onPlay,
}: AudioPromptProps) {
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(0.8);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const handlePlay = useCallback(() => {
    if (audioSrc && audioRef.current) {
      audioRef.current.volume = volume;
      audioRef.current.play();
      setPlaying(true);
      onPlay?.();
      return;
    }

    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === "hi" ? "hi-IN" : "en-US";
      utterance.volume = volume;
      utterance.rate = 0.85;
      utterance.onend = () => setPlaying(false);
      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
      setPlaying(true);
      onPlay?.();
    }
  }, [audioSrc, language, onPlay, text, volume]);

  useEffect(() => {
    if (autoPlay) queueMicrotask(handlePlay);
    return () => {
      window.speechSynthesis?.cancel();
    };
  }, [autoPlay, handlePlay]);

  const handleStop = () => {
    if (audioSrc && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    window.speechSynthesis?.cancel();
    setPlaying(false);
  };

  return (
    <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-2xl">
      {audioSrc && (
        <audio ref={audioRef} src={audioSrc} onEnded={() => setPlaying(false)} />
      )}

      <TouchButton
        variant="primary"
        size="medium"
        onClick={playing ? handleStop : handlePlay}
        aria-label={playing ? "Stop audio" : "Play question audio"}
      >
        {playing ? "⏹" : "🔊"}
      </TouchButton>

      <div className="flex-1">
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={volume}
          onChange={(e) => setVolume(parseFloat(e.target.value))}
          aria-label="Volume"
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      <TouchButton
        variant="secondary"
        size="small"
        onClick={handlePlay}
        aria-label="Replay audio"
      >
        ↻
      </TouchButton>
    </div>
  );
}
