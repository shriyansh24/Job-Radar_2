import {
  ArrowsClockwise,
  Buildings,
  CaretDown,
  CaretRight,
  ChatCircleText,
  Lightning,
  ListChecks,
  Question,
  ShieldWarning,
  Target,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  interviewApi,
  type ContextualPrepData,
  type PrepRedFlag,
  type PrepQuestion,
  type PrepStage,
  type QuestionToAsk,
  type SuggestedAnswer,
} from "../../api/interview";
import Badge from "../ui/Badge";
import Button from "../ui/Button";
import Card from "../ui/Card";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";
import { toast } from "../ui/toastService";

const STAGE_OPTIONS = [
  { value: "general", label: "General" },
  { value: "phone_screen", label: "Phone Screen" },
  { value: "technical", label: "Technical" },
  { value: "behavioral", label: "Behavioral" },
  { value: "final", label: "Final Round" },
];

const CATEGORY_VARIANT: Record<string, "info" | "success" | "warning" | "danger" | "default"> = {
  behavioral: "info",
  technical: "warning",
  situational: "danger",
  culture_fit: "success",
  general: "default",
};

function CollapsibleSection({
  title,
  icon,
  defaultOpen = false,
  children,
  badge,
}: {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
  badge?: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Card>
      <button
        type="button"
        className="w-full text-left flex items-center justify-between gap-2"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-semibold text-text-primary">{title}</span>
          {badge}
        </div>
        {open ? (
          <CaretDown size={14} weight="bold" className="text-text-muted" />
        ) : (
          <CaretRight size={14} weight="bold" className="text-text-muted" />
        )}
      </button>
      {open && <div className="mt-3 border-t border-border/50 pt-3">{children}</div>}
    </Card>
  );
}

function CompanyResearchSection({ data }: { data: ContextualPrepData["company_research"] }) {
  return (
    <CollapsibleSection
      title="Company Research"
      icon={<Buildings size={16} weight="bold" className="text-accent-primary" />}
      defaultOpen
    >
      <div className="space-y-3">
        {data.overview && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Overview</p>
            <p className="text-sm text-text-primary leading-relaxed">{data.overview}</p>
          </div>
        )}
        {data.interview_style && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Interview Style</p>
            <p className="text-sm text-text-primary leading-relaxed">{data.interview_style}</p>
          </div>
        )}
        {data.culture_values.length > 0 && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Culture & Values</p>
            <ul className="space-y-1">
              {data.culture_values.map((v, i) => (
                <li key={i} className="text-sm text-text-primary flex items-start gap-2">
                  <span className="text-accent-primary mt-1 shrink-0">*</span>
                  {v}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.recent_news.length > 0 && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Recent News</p>
            <ul className="space-y-1">
              {data.recent_news.map((n, i) => (
                <li key={i} className="text-sm text-text-primary flex items-start gap-2">
                  <span className="text-accent-primary mt-1 shrink-0">*</span>
                  {n}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </CollapsibleSection>
  );
}

function RoleAnalysisSection({ data }: { data: ContextualPrepData["role_analysis"] }) {
  return (
    <CollapsibleSection
      title="Role Analysis"
      icon={<Target size={16} weight="bold" className="text-green-500" />}
      defaultOpen
    >
      <div className="space-y-3">
        {data.seniority_expectations && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Level Expectations</p>
            <p className="text-sm text-text-primary leading-relaxed">{data.seniority_expectations}</p>
          </div>
        )}
        {data.talking_points.length > 0 && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Your Talking Points</p>
            <ul className="space-y-1">
              {data.talking_points.map((tp, i) => (
                <li key={i} className="text-sm text-text-primary flex items-start gap-2">
                  <Lightning size={12} weight="fill" className="text-yellow-500 mt-1 shrink-0" />
                  {tp}
                </li>
              ))}
            </ul>
          </div>
        )}
        {data.skill_gaps.length > 0 && (
          <div>
            <p className="text-xs font-medium text-text-secondary mb-1">Gaps to Address</p>
            <ul className="space-y-1">
              {data.skill_gaps.map((gap, i) => (
                <li key={i} className="text-sm text-text-muted flex items-start gap-2">
                  <ShieldWarning size={12} weight="bold" className="text-orange-500 mt-1 shrink-0" />
                  {gap}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </CollapsibleSection>
  );
}

function LikelyQuestionsSection({ questions }: { questions: PrepQuestion[] }) {
  return (
    <CollapsibleSection
      title="Likely Questions"
      icon={<ChatCircleText size={16} weight="bold" className="text-blue-500" />}
      badge={<Badge variant="info" size="sm">{questions.length}</Badge>}
    >
      <div className="space-y-3">
        {questions.map((q, i) => (
          <div key={i} className="p-3 bg-bg-tertiary rounded-[var(--radius-md)] border border-border/50">
            <div className="flex items-start justify-between gap-2 mb-1">
              <p className="text-sm font-medium text-text-primary">{q.question}</p>
              <Badge variant={CATEGORY_VARIANT[q.category] || "default"} size="sm">
                {q.category.replace("_", " ")}
              </Badge>
            </div>
            {q.why_likely && (
              <p className="text-xs text-text-muted mt-1">Why likely: {q.why_likely}</p>
            )}
            {q.suggested_approach && (
              <p className="text-xs text-accent-primary mt-1">Approach: {q.suggested_approach}</p>
            )}
          </div>
        ))}
      </div>
    </CollapsibleSection>
  );
}

function SuggestedAnswersSection({ answers }: { answers: SuggestedAnswer[] }) {
  return (
    <CollapsibleSection
      title="Suggested Answers (STAR)"
      icon={<ListChecks size={16} weight="bold" className="text-purple-500" />}
      badge={<Badge variant="default" size="sm">{answers.length}</Badge>}
    >
      <div className="space-y-4">
        {answers.map((a, i) => (
          <div key={i} className="p-3 bg-bg-tertiary rounded-[var(--radius-md)] border border-border/50">
            <p className="text-sm font-medium text-text-primary mb-2">{a.question}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div>
                <span className="font-semibold text-text-secondary">S: </span>
                <span className="text-text-primary">{a.star_response.situation}</span>
              </div>
              <div>
                <span className="font-semibold text-text-secondary">T: </span>
                <span className="text-text-primary">{a.star_response.task}</span>
              </div>
              <div>
                <span className="font-semibold text-text-secondary">A: </span>
                <span className="text-text-primary">{a.star_response.action}</span>
              </div>
              <div>
                <span className="font-semibold text-text-secondary">R: </span>
                <span className="text-text-primary">{a.star_response.result}</span>
              </div>
            </div>
            {a.key_points.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {a.key_points.map((kp, j) => (
                  <Badge key={j} variant="success" size="sm">{kp}</Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </CollapsibleSection>
  );
}

function QuestionsToAskSection({ questions }: { questions: QuestionToAsk[] }) {
  return (
    <CollapsibleSection
      title="Questions to Ask"
      icon={<Question size={16} weight="bold" className="text-teal-500" />}
      badge={<Badge variant="default" size="sm">{questions.length}</Badge>}
    >
      <div className="space-y-3">
        {questions.map((q, i) => (
          <div key={i} className="p-3 bg-bg-tertiary rounded-[var(--radius-md)] border border-border/50">
            <p className="text-sm font-medium text-text-primary">{q.question}</p>
            {q.why_effective && (
              <p className="text-xs text-text-muted mt-1">Why effective: {q.why_effective}</p>
            )}
            {q.what_to_listen_for && (
              <p className="text-xs text-accent-primary mt-1">Listen for: {q.what_to_listen_for}</p>
            )}
          </div>
        ))}
      </div>
    </CollapsibleSection>
  );
}

function RedFlagsSection({ flags }: { flags: PrepRedFlag[] }) {
  return (
    <CollapsibleSection
      title="Red Flags & Traps"
      icon={<ShieldWarning size={16} weight="bold" className="text-red-500" />}
      badge={<Badge variant="danger" size="sm">{flags.length}</Badge>}
    >
      <div className="space-y-3">
        {flags.map((f, i) => (
          <div key={i} className="p-3 bg-bg-tertiary rounded-[var(--radius-md)] border border-red-500/20">
            <p className="text-sm font-medium text-red-400">{f.trap}</p>
            {f.why_dangerous && (
              <p className="text-xs text-text-muted mt-1">Why: {f.why_dangerous}</p>
            )}
            {f.better_approach && (
              <p className="text-xs text-green-400 mt-1">Instead: {f.better_approach}</p>
            )}
          </div>
        ))}
      </div>
    </CollapsibleSection>
  );
}

interface InterviewPrepPanelProps {
  applicationId: string;
}

export default function InterviewPrepPanel({ applicationId }: InterviewPrepPanelProps) {
  const queryClient = useQueryClient();
  const [stage, setStage] = useState<PrepStage>("general");

  const { data: prep, isLoading } = useQuery({
    queryKey: ["interview-prep", applicationId],
    queryFn: () => interviewApi.getPrep(applicationId).then((r) => r.data),
    retry: false,
  });

  const generateMutation = useMutation({
    mutationFn: () => interviewApi.generatePrep(applicationId, stage),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interview-prep", applicationId] });
      toast("success", "Interview prep generated");
    },
    onError: () => toast("error", "Failed to generate interview prep"),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton variant="text" className="w-1/3 h-6" />
        <Skeleton variant="rect" className="w-full h-32" />
        <Skeleton variant="rect" className="w-full h-32" />
      </div>
    );
  }

  const prepData = prep?.prep_data;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h3 className="text-sm font-semibold text-text-primary">Interview Prep</h3>
        <div className="flex items-center gap-2">
          <div className="w-40">
            <Select
              options={STAGE_OPTIONS}
              value={stage}
              onChange={(e) => setStage(e.target.value as PrepStage)}
            />
          </div>
          <Button
            variant="secondary"
            size="sm"
            loading={generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
            icon={<ArrowsClockwise size={14} weight="bold" />}
          >
            {prepData ? "Regenerate" : "Generate"}
          </Button>
        </div>
      </div>

      {prep && (
        <p className="text-xs text-text-muted">
          Stage: <Badge variant="info" size="sm">{prep.stage.replace("_", " ")}</Badge>
        </p>
      )}

      {prepData ? (
        <div className="space-y-3">
          <CompanyResearchSection data={prepData.company_research} />
          <RoleAnalysisSection data={prepData.role_analysis} />
          <LikelyQuestionsSection questions={prepData.likely_questions} />
          <SuggestedAnswersSection answers={prepData.suggested_answers} />
          <QuestionsToAskSection questions={prepData.questions_to_ask} />
          <RedFlagsSection flags={prepData.red_flags} />
        </div>
      ) : (
        <Card>
          <div className="text-center py-8">
            <ChatCircleText size={40} weight="bold" className="text-text-muted mx-auto mb-3" />
            <p className="text-sm text-text-muted mb-1">No interview prep yet</p>
            <p className="text-xs text-text-muted">
              Select a stage and click Generate to create contextual interview prep
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}
