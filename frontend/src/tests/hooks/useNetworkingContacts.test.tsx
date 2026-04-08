import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, act, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNetworkingContacts } from "../../hooks/useNetworkingContacts";
import { createTestQueryClient } from "../support/renderWithProviders";

// Mock the networking API
vi.mock("../../api/networking", () => ({
  networkingApi: {
    listContacts: vi.fn(),
    createContact: vi.fn(),
    updateContact: vi.fn(),
    deleteContact: vi.fn(),
    findConnections: vi.fn(),
  },
}));

// Mock the toast service
vi.mock("../../components/ui/toastService", () => ({
  toast: vi.fn(),
}));

import * as networkingModule from "../../api/networking";
import * as toastModule from "../../components/ui/toastService";

const mockNetworkingApi = vi.mocked(networkingModule.networkingApi);
const mockToast = vi.mocked(toastModule.toast);

const MOCK_CONTACTS = [
  {
    id: "c1",
    name: "Alice Smith",
    company: "TechCorp",
    role: "Engineer",
    relationship_strength: 4,
    linkedin_url: null,
    email: "alice@techcorp.com",
    last_contacted: null,
    notes: null,
    created_at: null,
  },
  {
    id: "c2",
    name: "Bob Jones",
    company: "Startup",
    role: "PM",
    relationship_strength: 3,
    linkedin_url: null,
    email: "bob@startup.com",
    last_contacted: null,
    notes: null,
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
  mockNetworkingApi.listContacts.mockResolvedValue({ data: [] } as never);
});

describe("useNetworkingContacts – contact list", () => {
  it("returns empty contacts initially", async () => {
    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loadingContacts).toBe(false);
    });

    expect(result.current.contacts).toEqual([]);
  });

  it("returns contacts from API", async () => {
    mockNetworkingApi.listContacts.mockResolvedValue({ data: MOCK_CONTACTS } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.contacts).toHaveLength(2);
    });

    expect(result.current.contacts[0].name).toBe("Alice Smith");
  });

  it("filters contacts by search query", async () => {
    mockNetworkingApi.listContacts.mockResolvedValue({ data: MOCK_CONTACTS } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.contacts).toHaveLength(2));

    act(() => {
      result.current.setSearchValue("alice");
    });

    // deferredSearch - may need a small tick
    await waitFor(() => {
      expect(result.current.filteredContacts).toHaveLength(1);
      expect(result.current.filteredContacts[0].name).toBe("Alice Smith");
    });
  });

  it("returns all contacts when search is empty", async () => {
    mockNetworkingApi.listContacts.mockResolvedValue({ data: MOCK_CONTACTS } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.contacts).toHaveLength(2));

    expect(result.current.filteredContacts).toHaveLength(2);
  });
});

describe("useNetworkingContacts – selectContact", () => {
  it("populates form when a contact is selected", async () => {
    mockNetworkingApi.listContacts.mockResolvedValue({ data: MOCK_CONTACTS } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.contacts).toHaveLength(2));

    act(() => {
      result.current.setSelectedContactId("c1");
    });

    await waitFor(() => {
      expect(result.current.form.name).toBe("Alice Smith");
      expect(result.current.form.company).toBe("TechCorp");
    });
  });

  it("selectedContact returns the matching contact", async () => {
    mockNetworkingApi.listContacts.mockResolvedValue({ data: MOCK_CONTACTS } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.contacts).toHaveLength(2));

    act(() => {
      result.current.setSelectedContactId("c2");
    });

    expect(result.current.selectedContact?.name).toBe("Bob Jones");
  });
});

describe("useNetworkingContacts – createContact mutation", () => {
  it("creates contact and shows success toast", async () => {
    const newContact = { ...MOCK_CONTACTS[0], id: "c-new" };
    mockNetworkingApi.listContacts.mockResolvedValue({ data: [] } as never);
    mockNetworkingApi.createContact.mockResolvedValue({ data: newContact } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.loadingContacts).toBe(false));

    act(() => {
      result.current.setForm({
        name: "Alice Smith",
        company: "TechCorp",
        role: "Engineer",
        relationship_strength: 4,
        linkedin_url: null,
        email: null,
        notes: null,
      });
    });

    act(() => {
      result.current.saveContact();
    });

    await waitFor(() => {
      expect(mockNetworkingApi.createContact).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith("success", "Contact added");
    });
  });

  it("shows error toast if name is empty", async () => {
    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.loadingContacts).toBe(false));

    act(() => {
      result.current.saveContact();
    });

    expect(mockToast).toHaveBeenCalledWith("error", "Name is required");
    expect(mockNetworkingApi.createContact).not.toHaveBeenCalled();
  });
});

describe("useNetworkingContacts – resetForm", () => {
  it("clears selectedContactId and resets form fields", async () => {
    mockNetworkingApi.listContacts.mockResolvedValue({ data: MOCK_CONTACTS } as never);

    const { result } = renderHook(() => useNetworkingContacts(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.contacts).toHaveLength(2));

    act(() => {
      result.current.setSelectedContactId("c1");
    });

    await waitFor(() => expect(result.current.form.name).toBe("Alice Smith"));

    act(() => {
      result.current.resetForm();
    });

    expect(result.current.selectedContactId).toBeNull();
    expect(result.current.form.name).toBe("");
  });
});
