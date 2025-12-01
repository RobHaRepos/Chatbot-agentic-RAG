import { useEffect, useRef } from 'react';

/**
 * Hook to detect clicks outside of ref elements
 * FIXED: Prevents stale closure by storing handler in ref and stabilizing excludeRefs
 * 
 * @param handler - Callback when click outside occurs
 * @param enabled - Whether the listener is active
 * @param excludeRefs - Additional refs to exclude from outside detection
 */
export function useClickOutside<T extends HTMLElement = HTMLElement>(
  handler: () => void,
  enabled: boolean = true,
  excludeRefs: React.RefObject<HTMLElement>[] = []
): React.RefObject<T> {
  const ref = useRef<T>(null);
  const handlerRef = useRef(handler);
  
  // Keep handler ref updated without triggering effect
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (!enabled) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      
      // Check if click is inside main ref
      if (ref.current?.contains(target)) {
        return;
      }
      
      // Check if click is inside any excluded refs
      for (const excludeRef of excludeRefs) {
        if (excludeRef.current?.contains(target)) {
          return;
        }
      }
      
      handlerRef.current();
    };

    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        handlerRef.current();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscKey);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscKey);
    };
    // Only depend on enabled - excludeRefs changes are fine since we read them during event
  }, [enabled, excludeRefs]);

  return ref;
}
