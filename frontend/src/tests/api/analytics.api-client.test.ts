import { beforeEach, describe, expect, it, vi } from "vitest";

const apiClientMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
}));

vi.mock("../../api/client", () => ({
  default: apiClientMock,
}));

import { analyticsApi } from "../../api/analytics";

describe("analyticsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClientMock.get.mockResolvedValue({ data: null });
  });

  it("calls the expected analytics endpoints with the correct params", () => {
    analyticsApi.overview();
    analyticsApi.daily(30);
    analyticsApi.sources();
    analyticsApi.skills(10);
    analyticsApi.funnel();

    expect(apiClientMock.get).toHaveBeenNthCalledWith(
      1,
      "/analytics/overview"
    );
    expect(apiClientMock.get).toHaveBeenNthCalledWith(2, "/analytics/daily", {
      params: { days: 30 },
    });
    expect(apiClientMock.get).toHaveBeenNthCalledWith(
      3,
      "/analytics/sources"
    );
    expect(apiClientMock.get).toHaveBeenNthCalledWith(4, "/analytics/skills", {
      params: { limit: 10 },
    });
    expect(apiClientMock.get).toHaveBeenNthCalledWith(5, "/analytics/funnel");
  });
});
