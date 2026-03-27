import {
  ChatCircleText,
  CheckCircle,
  ShieldWarning,
  Sparkle,
} from "@phosphor-icons/react";

import { type InterviewPrepBundle } from "../../api/interview";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Badge from "../ui/Badge";

function ArraySection({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <Surface tone="subtle" padding="md">
      <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
        {title}
      </div>
      {items.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {items.map((item) => (
            <Badge key={item} variant="secondary">
              {item}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm leading-6 text-text-secondary">{emptyLabel}</p>
      )}
    </Surface>
  );
}

export function InterviewPrepBundlePanel({ bundle }: { bundle: InterviewPrepBundle }) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader
        title="Prep bundle"
        description="Review likely questions, stories, topics, and company-specific notes."
      />

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        <Surface tone="subtle" padding="md">
          <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            <Sparkle size={14} weight="fill" className="text-accent-primary" />
            Company research
          </div>
          <p className="mt-4 text-sm leading-6 text-text-secondary">
            {bundle.company_research?.overview || "No company-specific context returned."}
          </p>
          {bundle.company_research?.recent_news?.length ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {bundle.company_research.recent_news.map((item) => (
                <Badge key={item} variant="secondary">
                  {item}
                </Badge>
              ))}
            </div>
          ) : null}
          {bundle.company_research?.interview_style ? (
            <p className="mt-4 text-sm leading-6 text-text-secondary">
              <span className="font-semibold text-text-primary">Interview style:</span>{" "}
              {bundle.company_research.interview_style}
            </p>
          ) : null}
        </Surface>

        <Surface tone="subtle" padding="md">
          <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            <CheckCircle size={14} weight="bold" className="text-accent-success" />
            Role analysis
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {(bundle.role_analysis?.key_requirements || []).map((item) => (
              <Badge key={item} variant="info">
                {item}
              </Badge>
            ))}
            {(bundle.role_analysis?.skill_gaps || []).map((item) => (
              <Badge key={item} variant="warning">
                {item}
              </Badge>
            ))}
          </div>
          {bundle.role_analysis?.seniority_expectations ? (
            <p className="mt-4 text-sm leading-6 text-text-secondary">
              <span className="font-semibold text-text-primary">Seniority:</span>{" "}
              {bundle.role_analysis.seniority_expectations}
            </p>
          ) : null}
          {bundle.role_analysis?.talking_points?.length ? (
            <div className="mt-4 space-y-2">
              {bundle.role_analysis.talking_points.map((item) => (
                <p key={item} className="text-sm leading-6 text-text-secondary">
                  {item}
                </p>
              ))}
            </div>
          ) : null}
        </Surface>

        <Surface tone="subtle" padding="md">
          <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            <Sparkle size={14} weight="fill" className="text-accent-primary" />
            Likely questions
          </div>
          {bundle.likely_questions.length ? (
            <div className="mt-4 space-y-3">
              {bundle.likely_questions.map((item, index) => (
                <div key={`${item.question}-${index}`} className="border-2 border-border bg-[var(--color-bg-tertiary)] p-3">
                  <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                    {item.category}
                  </div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-text-primary">
                    {item.question}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-text-secondary">
              No likely questions returned.
            </p>
          )}
        </Surface>

        <Surface tone="subtle" padding="md">
          <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            <CheckCircle size={14} weight="bold" className="text-accent-success" />
            STAR stories
          </div>
          {bundle.star_stories.length ? (
            <div className="mt-4 space-y-3">
              {bundle.star_stories.map((story, index) => (
                <div key={`${story.situation}-${index}`} className="border-2 border-border bg-[var(--color-bg-tertiary)] p-3">
                  <p className="text-sm font-semibold text-text-primary">{story.situation}</p>
                  <div className="mt-3 space-y-2 text-sm leading-6 text-text-secondary">
                    <p><span className="font-semibold text-text-primary">Task:</span> {story.task}</p>
                    <p><span className="font-semibold text-text-primary">Action:</span> {story.action}</p>
                    <p><span className="font-semibold text-text-primary">Result:</span> {story.result}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-text-secondary">
              No STAR stories returned.
            </p>
          )}
        </Surface>

        <ArraySection
          title="Technical topics"
          items={bundle.technical_topics}
          emptyLabel="No technical topics returned."
        />

        <ArraySection
          title="Questions to ask"
          items={bundle.questions_to_ask}
          emptyLabel="No interviewer questions returned."
        />

        <ArraySection
          title="Company talking points"
          items={bundle.company_talking_points}
          emptyLabel="No company talking points returned."
        />

        <Surface tone="subtle" padding="md">
          <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
            <ShieldWarning size={14} weight="bold" className="text-accent-warning" />
            Red-flag responses
          </div>
          {bundle.red_flag_responses.length ? (
            <div className="mt-4 space-y-3">
              {bundle.red_flag_responses.map((entry, index) => (
                <div key={`${entry.question}-${index}`} className="border-2 border-border bg-[var(--color-bg-tertiary)] p-3">
                  <p className="text-sm font-semibold text-text-primary">{entry.question}</p>
                  <div className="mt-3 space-y-2 text-sm leading-6 text-text-secondary">
                    <p><span className="font-semibold text-text-primary">Avoid:</span> {entry.avoid}</p>
                    <p><span className="font-semibold text-text-primary">Instead:</span> {entry.instead}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-text-secondary">
              No red-flag guidance returned.
            </p>
          )}
        </Surface>
      </div>

      <div className="mt-6 rounded-none border-2 border-border bg-[var(--color-bg-tertiary)] p-4">
        <div className="flex items-center gap-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
          <ChatCircleText size={14} weight="bold" className="text-accent-primary" />
          Working use
        </div>
        <p className="mt-3 text-sm leading-6 text-text-secondary">
          Use this bundle to tighten stories, rehearse likely prompts, and choose which technical areas to review before the next loop.
        </p>
      </div>
    </Surface>
  );
}
