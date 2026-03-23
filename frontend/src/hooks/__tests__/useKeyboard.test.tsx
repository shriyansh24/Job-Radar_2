import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useKeyboard } from "../useKeyboard";

function KeyboardHarness({
  bindings,
}: {
  bindings: Parameters<typeof useKeyboard>[0];
}) {
  useKeyboard(bindings);
  return <div>Keyboard Harness</div>;
}

describe("useKeyboard", () => {
  it("matches ctrl bindings on meta key combinations and prevents default", () => {
    const handler = vi.fn();

    render(
      <KeyboardHarness
        bindings={[{ key: "k", ctrl: true, handler }]}
      />
    );

    const event = new KeyboardEvent("keydown", {
      key: "k",
      metaKey: true,
      cancelable: true,
    });

    expect(document.dispatchEvent(event)).toBe(false);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("removes the listener on unmount", () => {
    const handler = vi.fn();
    const { unmount } = render(
      <KeyboardHarness
        bindings={[{ key: "Enter", shift: true, handler }]}
      />
    );

    unmount();

    document.dispatchEvent(
      new KeyboardEvent("keydown", {
        key: "Enter",
        shiftKey: true,
        cancelable: true,
      })
    );

    expect(handler).not.toHaveBeenCalled();
  });
});
