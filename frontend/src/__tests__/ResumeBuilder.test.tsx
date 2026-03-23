import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const resumeMocks = vi.hoisted(() => ({
  listVersions: vi.fn(),
  upload: vi.fn(),
  tailor: vi.fn(),
  council: vi.fn(),
}));

const jobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
}));

vi.mock("../api/resume", () => ({
  resumeApi: resumeMocks,
}));

vi.mock("../api/jobs", () => ({
  jobsApi: jobsMocks,
}));

vi.mock("react-dropzone", () => ({
  useDropzone: () => ({
    getRootProps: () => ({}),
    getInputProps: () => ({}),
    isDragActive: false,
  }),
}));

import ResumeBuilder from "../pages/ResumeBuilder";

describe("ResumeBuilder page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resumeMocks.listVersions.mockResolvedValue({
      data: [
        {
          id: "resume-1",
          filename: "resume-2026.pdf",
          created_at: "2026-03-21T12:00:00Z",
          is_default: true,
          parsed_text: "Senior frontend engineer",
        },
      ],
    });
    resumeMocks.upload.mockResolvedValue({ data: null });
    resumeMocks.tailor.mockResolvedValue({ data: null });
    resumeMocks.council.mockResolvedValue({ data: null });
    jobsMocks.list.mockResolvedValue({
      data: {
        items: [
          {
            id: "job-1",
            title: "Staff Frontend Engineer",
            company_name: "Acme",
          },
        ],
      },
    });
  });

  it("renders the upload surface and shows resume data in the versions tab", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ResumeBuilder />);

    expect(
      await screen.findByRole("heading", { name: /Resume Builder/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/Drag & drop your resume here/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Versions/i }));

    expect(await screen.findByText("resume-2026.pdf")).toBeInTheDocument();
    expect(screen.getByText("Default")).toBeInTheDocument();
  });
});
