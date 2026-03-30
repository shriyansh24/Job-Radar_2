import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import DocumentVault from "../../pages/DocumentVault";

vi.mock("react-dropzone", () => ({
  useDropzone: () => ({
    getRootProps: () => ({}),
    getInputProps: () => ({}),
    isDragActive: false,
  }),
}));

const resume = {
  id: "resume-1",
  label: "Current Resume",
  filename: "resume.pdf",
  parsed_text: "Resume text",
  parsed_structured: null,
  is_default: false,
  created_at: "2026-03-21T12:00:00Z",
};

const coverLetter = {
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
});
