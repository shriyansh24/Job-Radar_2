import { beforeEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("../client", () => ({
  default: apiClientMock,
}));

import { scraperApi } from "../scraper";

describe("scraperApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClientMock.get.mockResolvedValue({ data: null });
    apiClientMock.post.mockResolvedValue({ data: null });
    apiClientMock.patch.mockResolvedValue({ data: null });
    apiClientMock.delete.mockResolvedValue({ data: null });
  });

  it("returns the SSE stream path and loads filtered targets and attempts", () => {
    expect(scraperApi.stream()).toBe("/api/v1/scraper/stream");

    scraperApi.listTargets({ priority_class: "hot", enabled: true, limit: 10 });
    scraperApi.getTarget("target-1");
    scraperApi.listAttempts({ target_id: "target-1", limit: 5 });

    expect(apiClientMock.get).toHaveBeenNthCalledWith(
      1,
      "/scraper/targets",
      {
        params: { priority_class: "hot", enabled: true, limit: 10 },
      }
    );
    expect(apiClientMock.get).toHaveBeenNthCalledWith(
      2,
      "/scraper/targets/target-1"
    );
    expect(apiClientMock.get).toHaveBeenNthCalledWith(
      3,
      "/scraper/attempts",
      {
        params: { target_id: "target-1", limit: 5 },
      }
    );
  });

  it("routes scraper mutations to the expected endpoints", () => {
    scraperApi.importTargets([{ url: "https://acme.example/jobs" }]);
    scraperApi.triggerTarget("target-1");
    scraperApi.updateTarget("target-1", { enabled: false });
    scraperApi.releaseTarget("target-1", { reason: "manual review" });
    scraperApi.triggerBatch({ priority_class: "watchlist", batch_size: 3 });

    expect(apiClientMock.post).toHaveBeenNthCalledWith(
      1,
      "/scraper/targets/import",
      [{ url: "https://acme.example/jobs" }]
    );
    expect(apiClientMock.post).toHaveBeenNthCalledWith(
      2,
      "/scraper/targets/target-1/trigger"
    );
    expect(apiClientMock.patch).toHaveBeenCalledWith(
      "/scraper/targets/target-1",
      { enabled: false }
    );
    expect(apiClientMock.post).toHaveBeenNthCalledWith(
      3,
      "/scraper/targets/target-1/release",
      { reason: "manual review" }
    );
    expect(apiClientMock.post).toHaveBeenNthCalledWith(
      4,
      "/scraper/trigger-batch",
      { priority_class: "watchlist", batch_size: 3 }
    );
  });
});
