import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { CoverLetterResult } from "../../api/copilot";
import type { ResumeVersion } from "../../api/resume";
import DocumentVault from "../../pages/DocumentVault";

let latestDropHandler: ((accepted: File[]) => void) | undefined;

vi.mock("react-dropzone", () => ({
  useDropzone: (options: { onDrop: (accepted: File[]) => void }) => {
    latestDropHandler = options.onDrop;

    return {
      getRootProps: () => ({}),
      getInputProps: () => ({}),
      isDragActive: false,
    };
  },
}));

beforeEach(() => {
  latestDropHandler = undefined;
  listResumes.mockResolvedValue({ data: [resume] });
  listCoverLetters.mockResolvedValue({ data: [coverLetter] });
  updateResume.mockClear();
  updateCoverLetter.mockClear();
  deleteResume.mockClear();
  deleteCoverLetter.mockClear();
  upload.mockClear();
});

const resume: ResumeVersion = {
  id: "resume-1",
  label: "Current Resume",
  filename: "resume.pdf",
  parsed_text: "Resume text",
  parsed_structured: null,
  is_default: false,
  created_at: "2026-03-21T12:00:00Z",
};

const coverLetter: CoverLetterResult = {
  id: "letter-1",
  job_id: null,
  style: "professional",
  content: "Original cover letter content",
  created_at: "2026-03-21T12:00:00Z",
};

const listResumes = vi.fn(() => Promise.resolve({ data: [resume] }));
const listCoverLetters = vi.fn(() => Promise.resolve({ data: [coverLetter] }));
const updateResume = vi.fn((id: string, label: string) => {
  void id;
  void label;
  return Promise.resolve({ data: resume });
});
const updateCoverLetter = vi.fn((id: string, content: string) => {
  void id;
  void content;
  return Promise.resolve({ data: coverLetter });
});
const deleteResume = vi.fn((id: string) => {
  void id;
  return Promise.resolve({ data: undefined });
});
const deleteCoverLetter = vi.fn((id: string) => {
  void id;
  return Promise.resolve({ data: undefined });
});
const upload = vi.fn((file: File) => {
  void file;
  return Promise.resolve({ data: resume });
});

vi.mock("../../api/resume", () => ({
  resumeApi: {
    upload: (file: File) => upload(file),
  },
}));

vi.mock("../../api/vault", () => ({
  vaultApi: {
    listResumes: () => listResumes(),
    listCoverLetters: () => listCoverLetters(),
    updateResume: (id: string, label: string) => updateResume(id, label),
    updateCoverLetter: (id: string, content: string) => updateCoverLetter(id, content),
    deleteResume: (id: string) => deleteResume(id),
    deleteCoverLetter: (id: string) => deleteCoverLetter(id),
  },
}));

function renderVault() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <DocumentVault />
    </QueryClientProvider>
  );
}

describe("DocumentVault", () => {
  it("opens the preview modal and shows parsed text", async () => {
    const user = userEvent.setup();
    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getByRole("button", { name: "Preview" }));

    expect(screen.getByRole("dialog", { name: "resume.pdf" })).toBeInTheDocument();
    expect(screen.getByText("Resume text")).toBeInTheDocument();
  });

  it("shows a preview fallback when parsed text is unavailable", async () => {
    const user = userEvent.setup();
    listResumes.mockResolvedValueOnce({
      data: [{ ...resume, parsed_text: null }],
    });

    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getByRole("button", { name: "Preview" }));

    expect(screen.getByText("No parsed text available yet.")).toBeInTheDocument();
  });

  it("updates a resume label through the patch flow", async () => {
    const user = userEvent.setup();
    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getAllByRole("button", { name: "Edit" })[0]);
    await user.clear(screen.getByLabelText("Resume label"));
    await user.type(screen.getByLabelText("Resume label"), "Senior Resume");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(updateResume).toHaveBeenCalledWith("resume-1", "Senior Resume");
    });
  });

  it("updates a cover letter body through the patch flow", async () => {
    const user = userEvent.setup();
    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getByRole("button", { name: "Cover Letters" }));
    await screen.findByText("Original cover letter content");
    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.clear(screen.getByLabelText("Cover letter content"));
    await user.type(screen.getByLabelText("Cover letter content"), "Updated cover letter body");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(updateCoverLetter).toHaveBeenCalledWith("letter-1", "Updated cover letter body");
    });
  });

  it("cancels resume edits and restores the original value on reopen", async () => {
    const user = userEvent.setup();
    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getAllByRole("button", { name: "Edit" })[0]);
    await user.clear(screen.getByLabelText("Resume label"));
    await user.type(screen.getByLabelText("Resume label"), "Discarded Label");
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog", { name: "Edit resume label" })).not.toBeInTheDocument();
    });

    await user.click(screen.getAllByRole("button", { name: "Edit" })[0]);
    expect(screen.getByLabelText("Resume label")).toHaveValue("Current Resume");
    expect(updateResume).not.toHaveBeenCalled();
  });

  it("requires confirmation before deleting a resume", async () => {
    const user = userEvent.setup();
    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.getByText("Delete?")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "No" }));

    expect(deleteResume).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Yes" }));

    await waitFor(() => {
      expect(deleteResume).toHaveBeenCalledWith("resume-1");
    });
  });

  it("requires confirmation before deleting a cover letter", async () => {
    const user = userEvent.setup();
    renderVault();

    await screen.findByText("resume.pdf");
    await user.click(screen.getByRole("button", { name: "Cover Letters" }));
    await screen.findByText("Original cover letter content");
    await user.click(screen.getByRole("button", { name: "Delete" }));

    const deleteRow = screen.getByText("Delete?").closest("div");
    expect(deleteRow).not.toBeNull();
    await user.click(within(deleteRow as HTMLDivElement).getByRole("button", { name: "Yes" }));

    await waitFor(() => {
      expect(deleteCoverLetter).toHaveBeenCalledWith("letter-1");
    });
  });

  it("forwards a dropped resume file to the upload API", async () => {
    renderVault();

    await screen.findByText("resume.pdf");
    expect(latestDropHandler).toBeTypeOf("function");

    const file = new File(["resume"], "candidate.pdf", { type: "application/pdf" });
    latestDropHandler?.([file]);

    await waitFor(() => {
      expect(upload).toHaveBeenCalledWith(file);
    });
  });
});
