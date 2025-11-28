/**
 * Get API base URL from meta tag or environment variable
 */
export const getApiBaseUrl = (): string => {
  const meta = document.querySelector('meta[name="api-base"]');
  const apiBase = meta?.getAttribute('content') || '/run';
  return apiBase;
};

/**
 * Get TTS URL based on API base URL
 */
export const getTTSUrl = (): string => {
  const apiBase = getApiBaseUrl();
  
  if (apiBase.endsWith('/run')) {
    return apiBase.replace(/\/run$/, '/tts');
  } else if (apiBase.endsWith('/')) {
    return apiBase + 'tts';
  } else {
    return '/tts';
  }
};

/**
 * Generate unique ID using cryptographically secure random values
 */
export const generateId = (): string => {
  return crypto.randomUUID();
};

/**
 * Format date to readable string
 */
export const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};
