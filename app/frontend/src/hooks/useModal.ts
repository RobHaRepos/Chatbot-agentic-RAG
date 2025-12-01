import { useState, useCallback } from 'react';

/**
 * Reusable modal state management hook
 * CRITICAL: Eliminates duplicate useState boilerplate across 3 pages
 * 
 * Usage:
 * const createModal = useModal();
 * <CreateStoreModal open={createModal.isOpen} onOpenChange={createModal.setOpen} />
 * <Button onClick={createModal.open}>Create</Button>
 */
export function useModal(initialState = false) {
  const [isOpen, setIsOpen] = useState(initialState);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

  return {
    isOpen,
    open,
    close,
    toggle,
    setOpen: setIsOpen,
  };
}
