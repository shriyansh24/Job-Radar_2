import { beforeEach, describe, expect, it } from "vitest";
import { useJobStore } from "../../store/useJobStore";

beforeEach(() => {
  useJobStore.getState().resetFilters();
});

describe("useJobStore – initial state", () => {
  it("starts with null selectedJobId", () => {
    expect(useJobStore.getState().selectedJobId).toBeNull();
  });

  it("starts with default filters", () => {
    const { filters } = useJobStore.getState();
    expect(filters.page).toBe(1);
    expect(filters.page_size).toBe(20);
    expect(filters.sort_by).toBe("scraped_at");
    expect(filters.sort_order).toBe("desc");
  });
});

describe("useJobStore – setSelectedJob", () => {
  it("sets selectedJobId", () => {
    useJobStore.getState().setSelectedJob("job-abc");
    expect(useJobStore.getState().selectedJobId).toBe("job-abc");
  });

  it("clears selectedJobId when null passed", () => {
    useJobStore.getState().setSelectedJob("job-abc");
    useJobStore.getState().setSelectedJob(null);
    expect(useJobStore.getState().selectedJobId).toBeNull();
  });
});

describe("useJobStore – setFilters", () => {
  it("merges new filters with existing ones", () => {
    useJobStore.getState().setFilters({ q: "python" });
    const { filters } = useJobStore.getState();
    expect(filters.q).toBe("python");
    // Other defaults still present
    expect(filters.sort_by).toBe("scraped_at");
  });

  it("resets page to 1 when not explicitly set", () => {
    useJobStore.setState({ filters: { page: 3, page_size: 20, sort_by: "scraped_at", sort_order: "desc" } });
    useJobStore.getState().setFilters({ q: "typescript" });
    expect(useJobStore.getState().filters.page).toBe(1);
  });

  it("preserves explicit page when provided", () => {
    useJobStore.getState().setFilters({ page: 5 });
    expect(useJobStore.getState().filters.page).toBe(5);
  });

  it("can set multiple filter fields at once", () => {
    useJobStore.getState().setFilters({ q: "react", remote_type: "remote", experience_level: "senior" });
    const { filters } = useJobStore.getState();
    expect(filters.q).toBe("react");
    expect(filters.remote_type).toBe("remote");
    expect(filters.experience_level).toBe("senior");
  });
});

describe("useJobStore – resetFilters", () => {
  it("clears applied filters and selectedJobId", () => {
    useJobStore.getState().setFilters({ q: "rust", remote_type: "remote" });
    useJobStore.getState().setSelectedJob("job-xyz");

    useJobStore.getState().resetFilters();

    const state = useJobStore.getState();
    expect(state.selectedJobId).toBeNull();
    expect(state.filters.q).toBeUndefined();
    expect(state.filters.remote_type).toBeUndefined();
    expect(state.filters.page).toBe(1);
    expect(state.filters.sort_by).toBe("scraped_at");
  });
});
