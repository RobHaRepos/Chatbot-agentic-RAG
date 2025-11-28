import { useTTSStore } from '@/store/ttsStore';
import { Select, SelectOption } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { DEFAULT_VOICES, getValidVoiceId, DEFAULT_VOICE_ID, DEFAULT_SPEED } from '@/types/tts';
import { Settings2, RotateCcw } from 'lucide-react';
import { useMemo, useEffect } from 'react';

export function TTSSettings() {
  const { voice, speed, setVoice, setSpeed, resetToDefaults } = useTTSStore();

  // Transform voices to select options with grouping
  const voiceOptions: SelectOption[] = useMemo(
    () =>
      DEFAULT_VOICES.map((v) => ({
        value: v.id,
        label: `${v.name} (${v.gender === 'female' ? '♀' : '♂'})`,
        group: `${v.accent} ${v.gender === 'female' ? 'Female' : 'Male'}`,
      })),
    []
  );

  // Validate voice on mount - fallback to default if not available
  useEffect(() => {
    const validVoice = getValidVoiceId(voice, DEFAULT_VOICES);
    if (validVoice !== voice) {
      setVoice(validVoice);
    }
  }, [voice, setVoice]);

  // Check if settings are at default values
  const isDefault = voice === DEFAULT_VOICE_ID && speed === DEFAULT_SPEED;

  return (
    <div className="border border-border rounded-lg bg-card/50 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Settings2 className="h-4 w-4" aria-hidden="true" />
          <span>Voice Settings</span>
        </div>
        {!isDefault && (
          <Button
            variant="ghost"
            size="sm"
            onClick={resetToDefaults}
            className="text-xs h-7"
            aria-label="Reset to default settings"
          >
            <RotateCcw className="h-3 w-3 mr-1" aria-hidden="true" />
            Reset
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {/* Voice Selection */}
        <div className="space-y-2">
          <label htmlFor="voice-select" className="text-sm font-medium">
            Voice
          </label>
          <Select
            id="voice-select"
            value={voice}
            onChange={setVoice}
            options={voiceOptions}
            groupBy={true}
            aria-label="Select voice"
          />
        </div>

        {/* Speed Control */}
        <div className="space-y-2">
          <label htmlFor="speed-slider" className="text-sm font-medium">
            Speed
          </label>
          <Slider
            id="speed-slider"
            value={speed}
            onChange={setSpeed}
            min={0.5}
            max={2}
            step={0.1}
            formatValue={(v) => `${v.toFixed(1)}x`}
            aria-label="Adjust voice speed"
          />
          <p className="text-xs text-muted-foreground">
            0.5x (slow) — 1.0x (normal) — 2.0x (fast)
          </p>
        </div>
      </div>
    </div>
  );
}
