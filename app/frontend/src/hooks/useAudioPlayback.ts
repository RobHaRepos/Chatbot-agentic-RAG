import { useRef, useCallback } from 'react';

/**
 * Hook to manage audio playback with ref-based state
 * FIXED: Removed unnecessary useCallback for stop/isPlaying (premature optimization)
 * 
 * @returns Audio management functions
 */
export function useAudioPlayback() {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // useCallback needed here because play is passed to async handlers
  const play = useCallback(async (audioBlob: Blob): Promise<void> => {
    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const url = URL.createObjectURL(audioBlob);
    const audio = new Audio(url);

    return new Promise((resolve, reject) => {
      let settled = false;

      const cleanupAndResolve = () => {
        if (settled) return;
        settled = true;
        try {
          URL.revokeObjectURL(url);
        } catch {}
        audioRef.current = null;
        resolve();
      };

      const cleanupAndReject = (err: Error) => {
        if (settled) return;
        settled = true;
        try {
          URL.revokeObjectURL(url);
        } catch {}
        audioRef.current = null;
        reject(err);
      };

      audio.onended = cleanupAndResolve;
      audio.onpause = cleanupAndResolve; // resolve also on manual pause/stop
      audio.onerror = () => cleanupAndReject(new Error('Audio playback failed'));

      audioRef.current = audio;
      audio.play().catch(cleanupAndReject);
    });
  }, []);

  // Simple functions don't need useCallback (not passed to memoized components)
  const stop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  };

  const isPlaying = () => {
    return audioRef.current !== null && !audioRef.current.paused;
  };

  return { play, stop, isPlaying };
}
