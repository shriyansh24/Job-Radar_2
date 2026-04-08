import { beforeEach, describe, expect, it } from "vitest";
import { useScraperStore } from "../../store/useScraperStore";
import type { ScraperEvent } from "../../store/useScraperStore";

beforeEach(() => {
  useScraperStore.setState({ isRunning: false, events: [] });
});

const makeEvent = (type = "info", data = "test message"): ScraperEvent => ({
  type,
  data,
  timestamp: new Date().toISOString(),
});

describe("useScraperStore – initial state", () => {
  it("starts with isRunning=false", () => {
    expect(useScraperStore.getState().isRunning).toBe(false);
  });

  it("starts with empty events", () => {
    expect(useScraperStore.getState().events).toEqual([]);
  });
});

describe("useScraperStore – setRunning", () => {
  it("sets isRunning to true", () => {
    useScraperStore.getState().setRunning(true);
    expect(useScraperStore.getState().isRunning).toBe(true);
  });

  it("sets isRunning to false", () => {
    useScraperStore.setState({ isRunning: true });
    useScraperStore.getState().setRunning(false);
    expect(useScraperStore.getState().isRunning).toBe(false);
  });
});

describe("useScraperStore – addEvent", () => {
  it("adds an event to the events array", () => {
    const event = makeEvent("job_found", "python engineer");
    useScraperStore.getState().addEvent(event);
    expect(useScraperStore.getState().events).toHaveLength(1);
    expect(useScraperStore.getState().events[0]).toEqual(event);
  });

  it("appends events in order", () => {
    const e1 = makeEvent("info", "first");
    const e2 = makeEvent("info", "second");
    const e3 = makeEvent("error", "third");
    useScraperStore.getState().addEvent(e1);
    useScraperStore.getState().addEvent(e2);
    useScraperStore.getState().addEvent(e3);

    const { events } = useScraperStore.getState();
    expect(events).toHaveLength(3);
    expect(events[0].data).toBe("first");
    expect(events[1].data).toBe("second");
    expect(events[2].data).toBe("third");
  });
});

describe("useScraperStore – clearEvents", () => {
  it("removes all events", () => {
    useScraperStore.getState().addEvent(makeEvent());
    useScraperStore.getState().addEvent(makeEvent());
    useScraperStore.getState().clearEvents();
    expect(useScraperStore.getState().events).toEqual([]);
  });

  it("does not affect isRunning state", () => {
    useScraperStore.setState({ isRunning: true });
    useScraperStore.getState().clearEvents();
    expect(useScraperStore.getState().isRunning).toBe(true);
  });
});
