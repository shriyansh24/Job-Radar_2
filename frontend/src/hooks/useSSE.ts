import { useEffect, useRef } from 'react';

export function useSSE(
  url: string | null,
  onEvent: (event: MessageEvent) => void,
  onError?: (event: Event) => void
) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);
  const onErrorRef = useRef(onError);

  onEventRef.current = onEvent;
  onErrorRef.current = onError;

  useEffect(() => {
    if (!url) return;

    const es = new EventSource(url, { withCredentials: true });
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      onEventRef.current(event);
    };

    es.onerror = (event) => {
      onErrorRef.current?.(event);
      es.close();
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [url]);

  return eventSourceRef;
}
