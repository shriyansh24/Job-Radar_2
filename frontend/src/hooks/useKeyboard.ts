import { useEffect } from 'react';

interface KeyBinding {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  handler: () => void;
}

export function useKeyboard(bindings: KeyBinding[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const binding of bindings) {
        const ctrlMatch = binding.ctrl ? (e.ctrlKey || e.metaKey) : true;
        const metaMatch = binding.meta ? e.metaKey : true;
        const shiftMatch = binding.shift ? e.shiftKey : true;

        if (
          e.key === binding.key &&
          ctrlMatch &&
          metaMatch &&
          shiftMatch
        ) {
          e.preventDefault();
          binding.handler();
          return;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [bindings]);
}
