import { renderHook, act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useDebounce } from "../../hooks/useDebounce";

describe("useDebounce", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns the latest value only after the debounce delay", () => {
    vi.useFakeTimers();

    const { result, rerender } = renderHook(
      ({ value, delay }: { value: string; delay: number }) =>
        useDebounce(value, delay),
      {
        initialProps: { value: "alpha", delay: 300 },
      }
    );

    expect(result.current).toBe("alpha");

    rerender({ value: "beta", delay: 300 });

    act(() => {
      vi.advanceTimersByTime(299);
    });
    expect(result.current).toBe("alpha");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe("beta");
  });

  it("cancels the pending timeout when the input changes again", () => {
    vi.useFakeTimers();

    const { result, rerender } = renderHook(
      ({ value }: { value: string }) => useDebounce(value, 250),
      {
        initialProps: { value: "first" },
      }
    );

    rerender({ value: "second" });

    act(() => {
      vi.advanceTimersByTime(200);
    });

    rerender({ value: "third" });

    act(() => {
      vi.advanceTimersByTime(249);
    });
    expect(result.current).toBe("first");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe("third");
  });
});
