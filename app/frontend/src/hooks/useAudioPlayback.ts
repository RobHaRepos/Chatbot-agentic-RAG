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
      audio.onended = () => {
        URL.revokeObjectURL(url);
        audioRef.current = null;
        resolve();
      };

      audio.onerror = () => {
        URL.revokeObjectURL(url);
        audioRef.current = null;
        reject(new Error('Audio playback failed'));
      };

      audioRef.current = audio;
      audio.play().catch(reject);
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
