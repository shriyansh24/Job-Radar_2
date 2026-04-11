import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CommandBar } from "../../../components/system/CommandBar";

describe("CommandBar", () => {
  it("renders children content", () => {
    render(<CommandBar>Search input here</CommandBar>);
    expect(screen.getByText("Search input here")).toBeInTheDocument();
  });

  it("renders leading slot when provided", () => {
    render(
      <CommandBar leading={<span data-testid="leading-content">Icon</span>}>
        Main
      </CommandBar>
    );
    expect(screen.getByTestId("leading-content")).toBeInTheDocument();
  });

  it("renders trailing slot when provided", () => {
    render(
      <CommandBar trailing={<button>Filter</button>}>
        Search
      </CommandBar>
    );
    expect(screen.getByRole("button", { name: /filter/i })).toBeInTheDocument();
  });

  it("renders both leading and trailing slots", () => {
    render(
      <CommandBar
        leading={<span data-testid="lead">L</span>}
        trailing={<span data-testid="trail">R</span>}
      >
        Center
      </CommandBar>
    );
    expect(screen.getByTestId("lead")).toBeInTheDocument();
    expect(screen.getByTestId("trail")).toBeInTheDocument();
    expect(screen.getByText("Center")).toBeInTheDocument();
  });

  it("renders without leading/trailing slots when not provided", () => {
    render(<CommandBar>Only children</CommandBar>);
    expect(screen.getByText("Only children")).toBeInTheDocument();
  });

  it("forwards className prop", () => {
    const { container } = render(<CommandBar className="cmd-class">Content</CommandBar>);
    // The root element should have our custom class somewhere in it
    expect(container.innerHTML).toContain("cmd-class");
  });
});
