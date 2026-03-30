import Badge from "../ui/Badge";
import Input from "../ui/Input";
import { SectionHeader } from "../system/SectionHeader";

const CHIP =
  "inline-flex items-center gap-1 border-2 border-[var(--color-text-primary)] px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.18em]";

export function OnboardingIntegrationsStep({
  fullName,
  openrouterKey,
  serpapiKey,
  onChange,
}: {
  fullName: string;
  openrouterKey: string;
  serpapiKey: string;
  onChange: (patch: { openrouterKey?: string; serpapiKey?: string }) => void;
}) {
  const integrations = [
    {
      provider: "openrouter",
      label: "OpenRouter",
      description: "AI drafting, summarization, and interview prep.",
      value: openrouterKey,
    },
    {
      provider: "serpapi",
      label: "SerpAPI",
      description: "Broader search coverage for discovery.",
      value: serpapiKey,
    },
  ] as const;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Integrations"
        description="Optional keys unlock broader search coverage and stronger drafting."
      />
      <form className="grid gap-4" onSubmit={(event) => event.preventDefault()}>
        <input
          type="text"
          name="integration-username"
          autoComplete="username"
          value={fullName || "onboarding"}
          readOnly
          tabIndex={-1}
          aria-hidden="true"
          className="sr-only"
        />
        {integrations.map((integration) => (
          <div
            key={integration.provider}
            className="border-2 border-[var(--color-text-primary)] bg-[var(--color-bg-tertiary)] p-4 shadow-[4px_4px_0px_0px_var(--color-text-primary)] sm:p-5"
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className={CHIP}>{integration.label}</span>
                  <Badge variant={integration.value ? "success" : "default"} size="sm">
                    {integration.value ? "Ready" : "Optional"}
                  </Badge>
                </div>
                <p className="text-sm leading-6 text-text-secondary">{integration.description}</p>
              </div>
              <div className="min-w-0 flex-1 lg:max-w-md">
                <Input
                  label={`${integration.label} API key`}
                  type="password"
                  autoComplete="off"
                  name={`${integration.provider}-api-key`}
                  value={integration.value}
                  onChange={(event) =>
                    onChange(
                      integration.provider === "openrouter"
                        ? { openrouterKey: event.target.value }
                        : { serpapiKey: event.target.value }
                    )
                  }
                  placeholder={`Enter ${integration.label} key`}
                />
              </div>
            </div>
          </div>
        ))}
      </form>
    </div>
  );
}
