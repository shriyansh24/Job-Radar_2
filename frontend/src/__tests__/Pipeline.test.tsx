import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "./testUtils";

const pipelineMocks = vi.hoisted(() => ({
  pipeline: vi.fn(),
  transition: vi.fn(),
}));

vi.mock("../api/pipeline", () => ({
  pipelineApi: pipelineMocks,
}));

vi.mock("../components/pipeline/AddApplicationModal", () => ({
  default: () => null,
}));

vi.mock("../components/pipeline/ApplicationModal", () => ({
  default: () => null,
}));

vi.mock("../components/pipeline/PipelineColumn", () => ({
  default: ({
    label,
    apps,
  }: {
    label: string;
    apps: Array<{
      id: string;
      position_title: string | null;
      company_name: string | null;
    }>;
  }) => (
    <section>
      <h2>{label}</h2>
      {apps.map((app) => (
        <div key={app.id}>{`${app.position_title ?? "Untitled"} @ ${app.company_name ?? "Unknown"}`}</div>
      ))}
    </section>
  ),
}));

import Pipeline from "../pages/Pipeline";

describe("Pipeline page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pipelineMocks.pipeline.mockResolvedValue({
      data: {
        saved: [
          {
            id: "app-1",
            position_title: "Backend Engineer",
            company_name: "Acme",
          },
        ],
        applied: [
          {
            id: "app-2",
            position_title: "Frontend Engineer",
            company_name: "Beta",
          },
        ],
        screening: [],
        interviewing: [],
        offer: [],
        accepted: [],
        rejected: [],
        withdrawn: [],
      },
    });
    pipelineMocks.transition.mockResolvedValue({ data: null });
  });

  it("renders the pipeline summary and application columns from query data", async () => {
    renderWithProviders(<Pipeline />);

    expect(
      await screen.findByRole("heading", { name: "Applications" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Add Application/i })).toBeInTheDocument();
    expect(await screen.findByText("Saved")).toBeInTheDocument();
    expect(screen.getByText("Applied")).toBeInTheDocument();
    expect(await screen.findByText("Backend Engineer @ Acme")).toBeInTheDocument();
    expect(screen.getByText("Frontend Engineer @ Beta")).toBeInTheDocument();
  });
});
