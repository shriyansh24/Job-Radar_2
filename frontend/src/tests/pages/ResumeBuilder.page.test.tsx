import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../support/renderWithProviders";

const resumeMocks = vi.hoisted(() => ({
  listVersions: vi.fn(),
  listTemplates: vi.fn(),
  preview: vi.fn(),
  exportVersion: vi.fn(),
  upload: vi.fn(),
  tailor: vi.fn(),
  council: vi.fn(),
}));

const jobsMocks = vi.hoisted(() => ({
  list: vi.fn(),
}));

vi.mock("../../api/resume", () => ({
  resumeApi: resumeMocks,
}));

vi.mock("../../api/jobs", () => ({
  jobsApi: jobsMocks,
}));

vi.mock("react-dropzone", () => ({
  useDropzone: () => ({
    getRootProps: () => ({}),
    getInputProps: () => ({}),
    isDragActive: false,
  }),
}));

import ResumeBuilder from "../../pages/ResumeBuilder";

describe("ResumeBuilder page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => "blob:resume-preview"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
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
    resumeMocks.listTemplates.mockResolvedValue({
      data: [
        {
          id: "professional",
          name: "Professional",
          description: "Balanced layout for general applications.",
        },
        {
          id: "modern",
          name: "Modern",
          description: "Sharper typography for design-forward roles.",
        },
      ],
    });
    resumeMocks.preview.mockResolvedValue({
      data: {
        template_id: "professional",
        html: "<section><h1>Jane Doe</h1><p>Built a shared UI platform</p></section>",
      },
    });
    resumeMocks.exportVersion.mockResolvedValue({
      data: new Blob(["%PDF"], { type: "application/pdf" }),
      headers: {
        "content-disposition": 'attachment; filename="resume-2026-professional.pdf"',
      },
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

  it("opens the version preview modal with parsed text", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ResumeBuilder />);

    await user.click(await screen.findByRole("button", { name: /Versions/i }));
    await user.click(await screen.findByText("resume-2026.pdf"));

    expect(await screen.findByRole("heading", { name: "resume-2026.pdf" })).toBeInTheDocument();
    expect(screen.getByText("Parsed text")).toBeInTheDocument();
    expect(screen.getByText("Professional")).toBeInTheDocument();
    expect(screen.getByText(/Balanced layout for general applications/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Export PDF/i })).toBeInTheDocument();
    expect(await screen.findByText("Jane Doe")).toBeInTheDocument();
    expect(await screen.findByText("Built a shared UI platform")).toBeInTheDocument();
    expect(resumeMocks.preview).toHaveBeenCalledWith("resume-1", "professional");
  });

  it("exports the selected rendered template from the preview modal", async () => {
    const user = userEvent.setup();

    renderWithProviders(<ResumeBuilder />);

    await user.click(await screen.findByRole("button", { name: /Versions/i }));
    await user.click(await screen.findByText("resume-2026.pdf"));
    await user.click(await screen.findByRole("button", { name: /Export PDF/i }));

    expect(resumeMocks.exportVersion).toHaveBeenCalledWith("resume-1", "professional");
  });

  it("renders council evaluation output for the selected resume", async () => {
    const user = userEvent.setup();
    resumeMocks.council.mockResolvedValue({
      data: {
        overall_score: 8.5,
        consensus: "Strong fit",
        evaluations: [
          {
            model: "gpt-5",
            score: 9,
            feedback: "Strong match for frontend platform work.",
            strengths: ["UI systems"],
            weaknesses: ["No GraphQL"],
          },
          {
            model: "claude",
            score: 8,
            feedback: "Good alignment with staff-level scope.",
            strengths: ["Architecture"],
            weaknesses: [],
          },
        ],
      },
    });

    renderWithProviders(<ResumeBuilder />);

    await user.click(await screen.findByRole("button", { name: /^Council$/i }));
    await user.selectOptions(screen.getByRole("combobox", { name: /resume version/i }), "resume-1");
    await user.selectOptions(screen.getByRole("combobox", { name: /target job/i }), "job-1");
    await user.click(screen.getByRole("button", { name: /^Run council$/i }));

    expect(await screen.findByText("Average score")).toBeInTheDocument();
    expect(screen.getByText("8.5")).toBeInTheDocument();
    expect(screen.getByText("Strong match for frontend platform work.")).toBeInTheDocument();
    expect(screen.getByText("Good alignment with staff-level scope.")).toBeInTheDocument();
  });
});
