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

import { jobsApi } from "../../api/jobs";

describe("jobsApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiClientMock.get.mockResolvedValue({ data: null });
    apiClientMock.post.mockResolvedValue({ data: null });
    apiClientMock.patch.mockResolvedValue({ data: null });
    apiClientMock.delete.mockResolvedValue({ data: null });
  });

  it("routes list, get, update, and delete requests through the job endpoints", () => {
    jobsApi.list({ q: "python", page: 2, page_size: 25 });
    jobsApi.get("job-123");
    jobsApi.update("job-123", { is_starred: true, status: "applied" });
    jobsApi.delete("job-123");

    expect(apiClientMock.get).toHaveBeenNthCalledWith(1, "/jobs", {
      params: { q: "python", page: 2, page_size: 25 },
    });
    expect(apiClientMock.get).toHaveBeenNthCalledWith(2, "/jobs/job-123");
    expect(apiClientMock.patch).toHaveBeenCalledWith("/jobs/job-123", {
      is_starred: true,
      status: "applied",
    });
    expect(apiClientMock.delete).toHaveBeenCalledWith("/jobs/job-123");
  });

  it("sends semantic search and export payloads with the expected options", () => {
    jobsApi.semanticSearch("remote staff engineer", 5);
    jobsApi.export("csv", { source: "linkedin", is_starred: true });

    expect(apiClientMock.post).toHaveBeenNthCalledWith(
      1,
      "/jobs/search/semantic",
      { query: "remote staff engineer", limit: 5 }
    );
    expect(apiClientMock.post).toHaveBeenNthCalledWith(
      2,
      "/jobs/export",
      {
        format: "csv",
        filters: { source: "linkedin", is_starred: true },
      },
      { responseType: "blob" }
    );
  });
});
