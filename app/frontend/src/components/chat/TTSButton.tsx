import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Volume2, Square, Loader2 } from 'lucide-react';
import { generateSpeech } from '@/services/ttsApi';
import { useTTSStore } from '@/store/ttsStore';
import { useAudioPlayback } from '@/hooks/useAudioPlayback';
import { handleError } from '@/lib/errorHandling';
import { ERROR_TEMPLATES } from '@/lib/errorTemplates';

interface TTSButtonProps {
  readonly text: string;
  readonly disabled?: boolean;
}

/**
 * FIXED: Audio state managed locally with custom hook instead of global Zustand store
 */
export function TTSButton({ text, disabled }: Readonly<TTSButtonProps>) {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const { voice, speed } = useTTSStore();
  const { play, stop } = useAudioPlayback();

  const handleClick = async () => {
    if (isPlaying) {
      stop();
      setIsPlaying(false);
      return;
    }

    if (!text.trim()) return;

    setIsLoading(true);

    try {
      const blob = await generateSpeech(text, voice, speed);
      setIsPlaying(true);
      
      await play(blob);
      
      setIsPlaying(false);
    } catch (err) {
      handleError(err, ...ERROR_TEMPLATES.TTS_GENERATE(text, voice, speed));
      setIsPlaying(false);
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
