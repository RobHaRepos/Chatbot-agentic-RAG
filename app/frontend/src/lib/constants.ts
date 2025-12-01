/**
 * Application-wide constants
 * CRITICAL: All magic numbers must be defined here, not scattered in code
 */

// ======= Retrieval Constants =======
/**
 * Default number of chunks to retrieve in similarity search
 */
export const DEFAULT_RETRIEVAL_K = 5;

/**
 * Minimum value for k parameter
 */
export const MIN_RETRIEVAL_K = 1;

/**
 * Maximum value for k parameter
 */
export const MAX_RETRIEVAL_K = 20;

// ======= React Query Cache Constants =======
/**
 * How long data is considered fresh (in milliseconds)
 * During this time, no refetch will occur
 */
export const QUERY_STALE_TIME = 30 * 1000; // 30 seconds

/**
 * How long unused data stays in cache (in milliseconds)
 */
export const QUERY_CACHE_TIME = 5 * 60 * 1000; // 5 minutes

// ======= Toast Constants =======
/**
 * Maximum number of toasts shown simultaneously
 */
export const MAX_TOASTS = 3;

/**
 * Duration before toast auto-dismisses (in milliseconds)
 */
export const TOAST_DURATION = 5000;

// ======= Form Validation Constants =======
/**
 * Minimum length for store name
 */
export const MIN_STORE_NAME_LENGTH = 1;

/**
 * Maximum length for store name
 */
export const MAX_STORE_NAME_LENGTH = 100;

/**
 * Maximum length for store description
 */
export const MAX_STORE_DESCRIPTION_LENGTH = 500;
