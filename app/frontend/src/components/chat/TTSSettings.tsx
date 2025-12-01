import { useTTSStore } from '@/store/ttsStore';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/radix-select';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { DEFAULT_VOICES, getValidVoiceId, DEFAULT_VOICE_ID, DEFAULT_SPEED, VoiceOption } from '@/types/tts';
import { Settings2, RotateCcw } from 'lucide-react';
import { IconLabel } from '@/components/ui/icon-label';
import { useEffect } from 'react';

// Group voices by accent + gender at module scope (constant calculation)
const groupedVoices: Record<string, VoiceOption[]> = (() => {
  const groups: Record<string, VoiceOption[]> = {};
  for (const v of DEFAULT_VOICES) {
    const groupKey = `${v.accent} ${v.gender === 'female' ? 'Female' : 'Male'}`;
    if (!groups[groupKey]) groups[groupKey] = [];
    groups[groupKey].push(v);
  }
  return groups;
})();

export function TTSSettings() {
  const { voice, speed, setVoice, setSpeed, resetToDefaults } = useTTSStore();

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
        <IconLabel icon={<Settings2 className="h-4 w-4" aria-hidden="true" />} gap="sm" className="text-sm font-medium text-muted-foreground">
          <span>Voice Settings</span>
        </IconLabel>
        {!isDefault && (
          <Button
            variant="ghost"
            size="sm"
            onClick={resetToDefaults}
            className="text-xs h-7"
            aria-label="Reset to default settings"
          >
            <IconLabel icon={<RotateCcw className="h-3 w-3" aria-hidden="true" />} gap="xs">
              Reset
            </IconLabel>
          </Button>
        )}
      </div>

      <div className="space-y-4">
        {/* Voice Selection */}
        <div className="space-y-2">
          <span id="voice-label" className="text-sm font-medium">
            Voice
          </span>
          <Select value={voice} onValueChange={setVoice}>
            <SelectTrigger aria-labelledby="voice-label">
              <SelectValue placeholder="Select a voice" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(groupedVoices).map(([groupName, voices]) => (
                <SelectGroup key={groupName}>
                  <SelectLabel>{groupName}</SelectLabel>
                  {voices.map((v) => (
                    <SelectItem key={v.id} value={v.id}>
                      {v.name} ({v.gender === 'female' ? '♀' : '♂'})
                    </SelectItem>
                  ))}
                </SelectGroup>
              ))}
            </SelectContent>
          </Select>
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
