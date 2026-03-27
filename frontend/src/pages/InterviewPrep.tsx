import { Brain, CheckCircle, ClockCounterClockwise, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { interviewApi, type InterviewSession } from "../api/interview";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SectionHeader } from "../components/system/SectionHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { Surface } from "../components/system/Surface";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";
import {
  InterviewGenerateForm,
  InterviewQuestionCard,
  InterviewSessionHistoryCard,
  InterviewSessionNotes,
} from "../components/interview/InterviewPanels";

const tabs = [
  { id: "practice", label: "Practice", icon: <Brain size={14} weight="bold" /> },
  { id: "history", label: "History", icon: <ClockCounterClockwise size={14} weight="bold" /> },
] as const;

export default function InterviewPrep() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("practice");
  const [activeSession, setActiveSession] = useState<InterviewSession | null>(null);

  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ["interview-sessions"],
    queryFn: () => interviewApi.listSessions().then((response) => response.data),
  });

  const generateMutation = useMutation({
    mutationFn: (params: { job_id: string; types: string[]; count: number }) =>
      interviewApi.generate(params),
    onSuccess: (response) => {
      setActiveSession(response.data);
      toast("success", "Interview questions generated");
      queryClient.invalidateQueries({ queryKey: ["interview-sessions"] });
    },
    onError: () => toast("error", "Failed to generate questions"),
  });

  const loadSessionMutation = useMutation({
    mutationFn: (id: string) => interviewApi.getSession(id),
    onSuccess: (response) => {
      setActiveSession(response.data);
      setActiveTab("practice");
    },
    onError: () => toast("error", "Failed to load session"),
  });

  const metrics = useMemo(
    () => [
      {
        key: "sessions",
        label: "Sessions",
        value: `${sessions?.length ?? 0}`,
        hint: "Saved practice sessions.",
        icon: <ClockCounterClockwise size={18} weight="bold" />,
      },
      {
        key: "active",
        label: "Active session",
        value: activeSession ? `${activeSession.questions.length}` : "0",
        hint: activeSession ? "Loaded into practice." : "No session loaded.",
        icon: <Brain size={18} weight="bold" />,
        tone: activeSession ? ("success" as const) : ("default" as const),
      },
      {
        key: "latest",
        label: "Latest score",
        value:
          sessions?.[0] && sessions[0].overall_score !== null ? `${sessions[0].overall_score?.toFixed(1)}` : "-",
        hint: "Most recent overall score.",
        icon: <CheckCircle size={18} weight="bold" />,
      },
      {
        key: "mode",
        label: "Mode",
        value: activeTab === "practice" ? "Practice" : "History",
        hint: "Current view.",
        icon: <Sparkle size={18} weight="bold" />,
      },
    ],
    [activeSession, activeTab, sessions]
  );

  return (
    <div className="space-y-6">
      <PageHeader
        className="hero-panel"
        eyebrow="Prepare"
        title="Interview Prep"
        description="Generate questions from a target job, practice answers, and keep session history close."
      />

      <MetricStrip items={metrics} />

      <Tabs tabs={tabs.map((tab) => ({ ...tab }))} activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === "practice" ? (
        <SplitWorkspace
          primary={
            <div className="space-y-6">
              <InterviewGenerateForm
                onGenerate={(params) => generateMutation.mutate(params)}
                isPending={generateMutation.isPending}
              />

              {activeSession ? (
                <div className="space-y-4">
                  <SectionHeader title="Active session" description={`${activeSession.questions.length} questions loaded.`} />
                  {activeSession.questions.map((question, index) => (
                    <InterviewQuestionCard
                      key={`${activeSession.id}-${index}`}
                      question={question}
                      index={index}
                      sessionId={activeSession.id}
                    />
                  ))}
                </div>
              ) : null}

              {!activeSession && !generateMutation.isPending ? (
                <Surface tone="default" padding="lg" radius="xl">
                  <EmptyState
                    icon={<Brain size={40} weight="bold" />}
                    title="No active session"
                    description="Select a job and generate questions to start."
                  />
                </Surface>
              ) : null}
            </div>
          }
          secondary={<InterviewSessionNotes activeTab={activeTab} />}
        />
      ) : null}

      {activeTab === "history" ? (
        <div className="space-y-4">
          {loadingSessions ? (
            <div className="grid gap-4 md:grid-cols-2">
              {Array.from({ length: 4 }).map((_, index) => (
                <Surface key={index} tone="default" padding="lg" radius="xl" className="brutal-panel">
                  <Skeleton variant="text" className="h-4 w-1/3" />
                  <Skeleton variant="text" className="mt-3 h-4 w-1/2" />
                  <div className="mt-3 flex gap-2">
                    <Skeleton variant="rect" className="h-6 w-20" />
                    <Skeleton variant="rect" className="h-6 w-20" />
                  </div>
                </Surface>
              ))}
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <Surface tone="default" padding="lg" radius="xl" className="brutal-panel">
              <EmptyState
                icon={<ClockCounterClockwise size={40} weight="bold" />}
                title="No sessions yet"
                description="Generate your first set of interview questions."
              />
            </Surface>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {sessions.map((session: InterviewSession) => (
                <InterviewSessionHistoryCard
                  key={session.id}
                  session={session}
                  onSelect={() => loadSessionMutation.mutate(session.id)}
                />
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
