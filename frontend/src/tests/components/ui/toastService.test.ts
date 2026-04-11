import { describe, expect, it, vi, beforeEach } from "vitest";
import { toast, registerToastHandler } from "../../../components/ui/toastService";

beforeEach(() => {
  // Unregister any handler from previous test
  registerToastHandler(null);
});

describe("toastService", () => {
  it("toast does nothing when no handler is registered", () => {
    // Should not throw even without a registered handler
    expect(() => toast("success", "Hello")).not.toThrow();
  });

  it("calls registered handler with success type and message", () => {
    const handler = vi.fn();
    registerToastHandler(handler);
    toast("success", "Operation complete");
    expect(handler).toHaveBeenCalledWith("success", "Operation complete");
  });

  it("calls registered handler with error type and message", () => {
    const handler = vi.fn();
    registerToastHandler(handler);
    toast("error", "Something went wrong");
    expect(handler).toHaveBeenCalledWith("error", "Something went wrong");
  });

  it("calls registered handler with warning type", () => {
    const handler = vi.fn();
    registerToastHandler(handler);
    toast("warning", "Check your input");
    expect(handler).toHaveBeenCalledWith("warning", "Check your input");
  });

  it("calls registered handler with info type", () => {
    const handler = vi.fn();
    registerToastHandler(handler);
    toast("info", "Just so you know");
    expect(handler).toHaveBeenCalledWith("info", "Just so you know");
  });

  it("stops calling handler after unregistering (null)", () => {
    const handler = vi.fn();
    registerToastHandler(handler);
    registerToastHandler(null);
    toast("success", "Should not be called");
    expect(handler).not.toHaveBeenCalled();
  });

  it("replaces previous handler when a new handler is registered", () => {
    const oldHandler = vi.fn();
    const newHandler = vi.fn();
    registerToastHandler(oldHandler);
    registerToastHandler(newHandler);
    toast("success", "Latest handler");
    expect(oldHandler).not.toHaveBeenCalled();
    expect(newHandler).toHaveBeenCalledWith("success", "Latest handler");
  });
});
