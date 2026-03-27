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
    resumeMocks.tailor.mockResolvedValue({
      data: {
        summary: "Tailored for Staff Frontend Engineer",
        reordered_experience: [
          {
            company: "Acme",
            bullets: ["Led frontend platform work"],
          },
        ],
        enhanced_bullets: [
          {
            original: "Built UI",
            enhanced: "Built and scaled a shared UI platform for high-traffic product surfaces",
          },
        ],
        skills_section: ["React", "TypeScript"],
        ats_score_before: 64,
        ats_score_after: 81,
        stage1_output: {
          hard_requirements: ["React"],
          soft_requirements: [],
          key_technologies: ["TypeScript"],
          ats_keywords: ["react", "typescript"],
          culture_signals: [],
          seniority_indicators: [],
          deal_breakers: [],
        },
        stage2_output: {
          matched_requirements: ["React"],
          partial_matches: [],
          missing_requirements: ["Design systems"],
          transferable_skills: [],
          keyword_coverage: {
            present: ["react"],
            missing: ["design systems"],
          },
          strength_areas: ["UI architecture"],
          risk_areas: ["No design systems keyword"],
        },
      },
    });
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
    expect(screen.getByText(/Drag and drop a resume/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Versions/i }));

    expect(await screen.findByText("resume-2026.pdf")).toBeInTheDocument();
    expect(screen.getByText("Default")).toBeInTheDocument();
  });

  it("renders the structured tailoring result from the backend contract", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ResumeBuilder />);

    await user.click(await screen.findByRole("button", { name: /^Tailor$/i }));
    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[0], "resume-1");
    await user.selectOptions(selects[1], "job-1");
    const tailorButtons = screen.getAllByRole("button", { name: /^Tailor$/i });
    await user.click(tailorButtons[tailorButtons.length - 1]);

    expect(await screen.findByText("Tailored resume")).toBeInTheDocument();
    expect(screen.getByText("Tailored for Staff Frontend Engineer")).toBeInTheDocument();
    expect(screen.getByText("81")).toBeInTheDocument();
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.getByText(/Built and scaled a shared UI platform/i)).toBeInTheDocument();
  });
});
