import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, act, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNetworkingReferrals } from "../../hooks/useNetworkingReferrals";
import { createTestQueryClient } from "../support/renderWithProviders";

// Mock the networking API
vi.mock("../../api/networking", () => ({
  networkingApi: {
    listReferralRequests: vi.fn(),
    suggestReferrals: vi.fn(),
    generateOutreach: vi.fn(),
    createReferralRequest: vi.fn(),
  },
}));

// Mock the jobs API
vi.mock("../../api/jobs", () => ({
  jobsApi: {
    list: vi.fn(),
  },
}));

// Mock toast
vi.mock("../../components/ui/toastService", () => ({
  toast: vi.fn(),
}));

import * as networkingModule from "../../api/networking";
import * as jobsModule from "../../api/jobs";
import * as toastModule from "../../components/ui/toastService";

const mockNetworkingApi = vi.mocked(networkingModule.networkingApi);
const mockJobsApi = vi.mocked(jobsModule.jobsApi);
const mockToast = vi.mocked(toastModule.toast);

const MOCK_JOBS = {
  items: [
    { id: "job-1", title: "Backend Engineer", company_name: "TechCo" },
    { id: "job-2", title: "Frontend Engineer", company_name: "StartupX" },
  ],
  total: 2,
};

const MOCK_CONTACTS = [
  {
    id: "c1",
    name: "Alice Smith",
    company: "TechCo",
    role: "Engineer",
    relationship_strength: 4,
    linkedin_url: null,
    email: null,
    last_contacted: null,
    notes: null,
    created_at: null,
  },
];

const MOCK_REFERRAL_REQUESTS = [
  {
    id: "rr-1",
    contact_id: "c1",
    job_id: "job-1",
    status: "draft",
    message_template: "Hi Alice!",
    sent_at: null,
    created_at: null,
  },
];

function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: PropsWithChildren) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  mockNetworkingApi.listReferralRequests.mockResolvedValue({ data: [] } as never);
  mockJobsApi.list.mockResolvedValue({ data: MOCK_JOBS } as never);
});

describe("useNetworkingReferrals – initialization", () => {
  it("loads recent jobs on mount", async () => {
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.recentJobs).toBeDefined();
    });

    expect(result.current.recentJobs?.items).toHaveLength(2);
  });

  it("auto-selects first job from recent jobs", async () => {
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.selectedJobId).toBe("job-1");
    });
  });

  it("builds jobOptions from recent jobs", async () => {
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.jobOptions).toHaveLength(2);
    });

    expect(result.current.jobOptions[0]).toEqual({
      value: "job-1",
      label: "Backend Engineer - TechCo",
    });
  });
});

describe("useNetworkingReferrals – referral queue", () => {
  it("returns empty referral queue when no requests", async () => {
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.recentJobs).toBeDefined());

    expect(result.current.referralQueueItems).toEqual([]);
  });

  it("maps referral requests with contact names", async () => {
    mockNetworkingApi.listReferralRequests.mockResolvedValue({ data: MOCK_REFERRAL_REQUESTS } as never);

    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.referralQueueItems).toHaveLength(1);
    });

    expect(result.current.referralQueueItems[0].contactName).toBe("Alice Smith");
    expect(result.current.referralQueueItems[0].status).toBe("draft");
  });

  it("shows Unknown contact when contact is not in list", async () => {
    mockNetworkingApi.listReferralRequests.mockResolvedValue({ data: MOCK_REFERRAL_REQUESTS } as never);

    // Pass empty contacts
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: [] }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.referralQueueItems).toHaveLength(1);
    });

    expect(result.current.referralQueueItems[0].contactName).toBe("Unknown contact");
  });
});

describe("useNetworkingReferrals – mutations", () => {
  it("suggestionsMutation calls suggestReferrals API", async () => {
    const suggestions = [
      {
        contact: MOCK_CONTACTS[0],
        relevance_reason: "Works at TechCo",
        suggested_message: "Hi Alice, could you refer me?",
      },
    ];
    mockNetworkingApi.suggestReferrals = vi.fn().mockResolvedValue({ data: suggestions } as never);

    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.recentJobs).toBeDefined());

    act(() => {
      result.current.suggestionsMutation.mutate("job-1");
    });

    await waitFor(() => {
      expect(mockNetworkingApi.suggestReferrals).toHaveBeenCalledWith("job-1");
    });

    await waitFor(() => {
      expect(result.current.suggestions).toHaveLength(1);
    });
  });

  it("outreachMutation sets generatedMessage on success", async () => {
    mockNetworkingApi.generateOutreach = vi.fn().mockResolvedValue({
      data: { message: "Dear Alice, please refer me..." },
    } as never);

    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.recentJobs).toBeDefined());

    act(() => {
      result.current.outreachMutation.mutate({ contactId: "c1", jobId: "job-1" });
    });

    await waitFor(() => {
      expect(result.current.generatedMessage).toBe("Dear Alice, please refer me...");
    });
  });

  it("createReferralRequest shows success toast", async () => {
    mockNetworkingApi.createReferralRequest = vi.fn().mockResolvedValue({ data: {} } as never);

    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.recentJobs).toBeDefined());

    act(() => {
      result.current.createReferralRequestMutation.mutate({
        contactId: "c1",
        jobId: "job-1",
        message: "Hi!",
      });
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith("success", "Referral request draft created");
    });
  });
});

describe("useNetworkingReferrals – manual state setters", () => {
  it("setSelectedJobId updates selectedJobId", async () => {
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.recentJobs).toBeDefined());

    act(() => {
      result.current.setSelectedJobId("job-2");
    });

    expect(result.current.selectedJobId).toBe("job-2");
  });

  it("setGeneratedMessage updates generatedMessage", async () => {
    const { result } = renderHook(() => useNetworkingReferrals({ contacts: MOCK_CONTACTS }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.recentJobs).toBeDefined());

    act(() => {
      result.current.setGeneratedMessage("Custom message");
    });

    expect(result.current.generatedMessage).toBe("Custom message");
  });
});
