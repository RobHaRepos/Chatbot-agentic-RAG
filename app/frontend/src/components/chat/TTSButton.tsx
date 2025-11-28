import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Volume2, Square, Loader2 } from 'lucide-react';
import { generateSpeech } from '@/services/ttsApi';
import { useChatStore } from '@/store/chatStore';
import { useTTSStore } from '@/store/ttsStore';

interface TTSButtonProps {
  readonly text: string;
  readonly disabled?: boolean;
}

export function TTSButton({ text, disabled }: Readonly<TTSButtonProps>) {
  const [isLoading, setIsLoading] = useState(false);
  const { activeAudio, setActiveAudio, stopActiveAudio } = useChatStore();
  const { voice, speed } = useTTSStore();
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  const isPlaying = activeAudio === currentAudio && currentAudio !== null;

  const handleClick = async () => {
    if (isPlaying) {
      stopActiveAudio();
      setCurrentAudio(null);
      return;
    }

    if (!text.trim()) return;

    setIsLoading(true);
    stopActiveAudio();

    try {
      const blob = await generateSpeech(text, voice, speed);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);

      audio.onended = () => {
        URL.revokeObjectURL(url);
        setActiveAudio(null);
        setCurrentAudio(null);
      };

      audio.onerror = (e) => {
        console.error('Audio playback error', e);
        setActiveAudio(null);
        setCurrentAudio(null);
      };

      setCurrentAudio(audio);
      setActiveAudio(audio);
      await audio.play();
    } catch (err) {
      console.error('TTS error:', err);
      alert('Failed to generate speech. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  let icon;
  let ariaLabel;
  if (isLoading) {
    icon = <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />;
    ariaLabel = 'Loading speech';
  } else if (isPlaying) {
    icon = <Square className="h-4 w-4" aria-hidden="true" />;
    ariaLabel = 'Stop speaking';
  } else {
    icon = <Volume2 className="h-4 w-4" aria-hidden="true" />;
    ariaLabel = 'Read message aloud';
  }

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={handleClick}
      disabled={disabled || isLoading || !text.trim()}
      className="shrink-0"
      aria-label={ariaLabel}
      aria-busy={isLoading}
    >
      {icon}
    </Button>
  );
}
