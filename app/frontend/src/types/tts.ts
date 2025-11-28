export interface VoiceOption {
  readonly id: string;
  readonly name: string;
  readonly gender: 'male' | 'female';
  readonly accent?: string;
}

export interface TTSSettings {
  readonly voice: string;
  readonly speed: number;
}

// Default voice ID - fallback when selected voice is not available
export const DEFAULT_VOICE_ID = 'am_onyx';
export const DEFAULT_SPEED = 1;

// Default voice options - can be replaced with API call to database later
export const DEFAULT_VOICES: readonly VoiceOption[] = [
  { id: 'af_heart', name: 'Heart', gender: 'female', accent: 'American' },
  { id: 'af_alloy', name: 'Alloy', gender: 'female', accent: 'American' },
  { id: 'af_aoede', name: 'Aoede', gender: 'female', accent: 'American' },
  { id: 'af_bella', name: 'Bella', gender: 'female', accent: 'American' },
  { id: 'af_jessica', name: 'Jessica', gender: 'female', accent: 'American' },
  { id: 'af_kore', name: 'Kore', gender: 'female', accent: 'American' },
  { id: 'af_nicole', name: 'Nicole', gender: 'female', accent: 'American' },
  { id: 'af_nova', name: 'Nova', gender: 'female', accent: 'American' },
  { id: 'af_river', name: 'River', gender: 'female', accent: 'American' },
  { id: 'af_sarah', name: 'Sarah', gender: 'female', accent: 'American' },
  { id: 'af_sky', name: 'Sky', gender: 'female', accent: 'American' },
  { id: 'am_adam', name: 'Adam', gender: 'male', accent: 'American' },
  { id: 'am_echo', name: 'Echo', gender: 'male', accent: 'American' },
  { id: 'am_eric', name: 'Eric', gender: 'male', accent: 'American' },
  { id: 'am_fenrir', name: 'Fenrir', gender: 'male', accent: 'American' },
  { id: 'am_liam', name: 'Liam', gender: 'male', accent: 'American' },
  { id: 'am_michael', name: 'Michael', gender: 'male', accent: 'American' },
  { id: 'am_onyx', name: 'Onyx', gender: 'male', accent: 'American' },
  { id: 'bf_alice', name: 'Alice', gender: 'female', accent: 'British' },
  { id: 'bf_emma', name: 'Emma', gender: 'female', accent: 'British' },
  { id: 'bf_lily', name: 'Lily', gender: 'female', accent: 'British' },
  { id: 'bm_daniel', name: 'Daniel', gender: 'male', accent: 'British' },
  { id: 'bm_fable', name: 'Fable', gender: 'male', accent: 'British' },
  { id: 'bm_george', name: 'George', gender: 'male', accent: 'British' },
  { id: 'bm_lewis', name: 'Lewis', gender: 'male', accent: 'British' },
] as const;

/**
 * Get a valid voice ID - falls back to default if the given voice is not available
 */
export const getValidVoiceId = (voiceId: string, availableVoices: readonly VoiceOption[] = DEFAULT_VOICES): string => {
  const isValid = availableVoices.some((v) => v.id === voiceId);
  return isValid ? voiceId : DEFAULT_VOICE_ID;
};
