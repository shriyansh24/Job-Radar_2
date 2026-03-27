import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useSSE } from "../../hooks/useSSE";

class MockEventSource {
  static instances: MockEventSource[] = [];

  readonly url: string;
  readonly withCredentials: boolean;
  readonly close = vi.fn();
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string, options?: EventSourceInit) {
    this.url = url;
    this.withCredentials = options?.withCredentials ?? false;
    MockEventSource.instances.push(this);
  }
}

describe("useSSE", () => {
  beforeEach(() => {
    MockEventSource.instances = [];
    vi.stubGlobal("EventSource", MockEventSource as unknown as typeof EventSource);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("creates an EventSource, forwards the latest handlers, and closes on cleanup", () => {
    const firstHandler = vi.fn();
    const secondHandler = vi.fn();
    const errorHandler = vi.fn();

    const { result, rerender, unmount } = renderHook(
      ({
        url,
        onEvent,
      }: {
        url: string | null;
        onEvent: (event: MessageEvent) => void;
      }) => useSSE(url, onEvent, errorHandler),
      {
        initialProps: { url: "/api/v1/scraper/stream", onEvent: firstHandler },
      }
    );

    const eventSource = MockEventSource.instances[0];

    expect(MockEventSource.instances).toHaveLength(1);
    expect(eventSource.url).toBe("/api/v1/scraper/stream");
    expect(eventSource.withCredentials).toBe(true);
    expect(result.current.current).toBe(eventSource as unknown as EventSource);

    const firstEvent = new MessageEvent("message", { data: "first" });
    eventSource.onmessage?.(firstEvent);
    expect(firstHandler).toHaveBeenCalledWith(firstEvent);

    rerender({ url: "/api/v1/scraper/stream", onEvent: secondHandler });

    const secondEvent = new MessageEvent("message", { data: "second" });
    eventSource.onmessage?.(secondEvent);
    expect(firstHandler).toHaveBeenCalledTimes(1);
    expect(secondHandler).toHaveBeenCalledWith(secondEvent);

    const errorEvent = new Event("error");
    eventSource.onerror?.(errorEvent);
    expect(errorHandler).toHaveBeenCalledWith(errorEvent);
    expect(eventSource.close).toHaveBeenCalledTimes(1);

    unmount();
    expect(eventSource.close).toHaveBeenCalledTimes(2);
    expect(result.current.current).toBeNull();
  });

  it("does not create an EventSource when no url is provided", () => {
    const { result } = renderHook(() => useSSE(null, vi.fn()));

    expect(MockEventSource.instances).toHaveLength(0);
    expect(result.current.current).toBeNull();
  });
});
