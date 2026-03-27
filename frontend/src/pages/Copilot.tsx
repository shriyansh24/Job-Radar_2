import { Brain, Briefcase, ClockCounterClockwise, FileText, MagicWand, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { startTransition, useEffect, useState } from "react";
import { copilotApi, type CoverLetterResult } from "../api/copilot";
import { jobsApi } from "../api/jobs";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { Surface } from "../components/system/Surface";
import Tabs from "../components/ui/Tabs";
import { toast } from "../components/ui/toastService";
import {
  type CopilotTab,
  type TranscriptEntry,
} from "../components/copilot/CopilotData";
import {
  HistoryActionRail,
  HistoryPanel,
  JobContextPanel,
  LettersPanel,
  TranscriptPanel,
} from "../components/copilot/CopilotPanels";

const COPILOT_TABS = [
  { id: "assistant", label: "Assistant", icon: <Sparkle size={14} weight="bold" /> },
  { id: "history", label: "History", icon: <ClockCounterClockwise size={14} weight="bold" /> },
  { id: "letters", label: "Letters", icon: <FileText size={14} weight="bold" /> },
] as const;

export default function Copilot() {
  const [activeTab, setActiveTab] = useState<CopilotTab>("assistant");
  const [selectedJobId, setSelectedJobId] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [historyQuestion, setHistoryQuestion] = useState("");
  const [historyAnswer, setHistoryAnswer] = useState("");
  const [coverLetterStyle, setCoverLetterStyle] = useState("professional");
  const [coverLetterTemplate, setCoverLetterTemplate] = useState("");
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [coverLetter, setCoverLetter] = useState<CoverLetterResult | null>(null);

  const { data: recentJobs, isLoading: loadingJobs } = useQuery({
    queryKey: ["jobs", "copilot-context"],
    queryFn: () =>
      jobsApi
        .list({ page_size: 10, sort_by: "scraped_at", sort_order: "desc" })
        .then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedJobId && recentJobs?.items.length) {
      setSelectedJobId(recentJobs.items[0].id);
    }
  }, [recentJobs, selectedJobId]);

  const jobOptions =
    recentJobs?.items.map((job) => ({
      value: job.id,
      label: `${job.title} - ${job.company_name ?? "Unknown company"}`,
    })) ?? [];

  const selectedJob = recentJobs?.items.find((job) => job.id === selectedJobId) ?? null;

  const chatMutation = useMutation({
    mutationFn: async (message: string) =>
      copilotApi
        .chat(
          message,
          selectedJob
            ? {
                job_title: selectedJob.title,
                company_name: selectedJob.company_name,
                location: selectedJob.location,
                match_score: selectedJob.match_score,
              }
            : null,
          selectedJobId || undefined
        )
        .then((response) => response.data),
    onSuccess: (response) => {
      setTranscript((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: response.response,
          label: "Copilot",
        },
      ]);
      setChatInput("");
    },
    onError: () => toast("error", "Copilot could not respond right now"),
  });

  const askHistoryMutation = useMutation({
    mutationFn: (question: string) => copilotApi.askHistory(question).then((response) => response.data),
    onSuccess: (response) => {
      setHistoryAnswer(response.answer);
      setTranscript((current) => [
        ...current,
        {
          id: `history-${Date.now()}`,
          role: "assistant",
          content: response.answer,
          label: "History",
        },
      ]);
    },
    onError: () => toast("error", "History analysis failed"),
  });

  const coverLetterMutation = useMutation({
    mutationFn: () =>
      copilotApi
        .generateCoverLetter(selectedJobId, coverLetterStyle, coverLetterTemplate || undefined)
        .then((response) => response.data),
    onSuccess: (response) => {
      setCoverLetter(response);
      setTranscript((current) => [
        ...current,
        {
          id: `letter-${Date.now()}`,
          role: "assistant",
          content: response.content,
          label: "Letter",
        },
      ]);
    },
    onError: () => toast("error", "Cover letter generation failed"),
  });

  const sendChat = (message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return;

    setTranscript((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: trimmed,
        label: "You",
      },
    ]);
    chatMutation.mutate(trimmed);
  };

  const runHistoryQuestion = (question: string) => {
    const trimmed = question.trim();
    if (!trimmed) return;
    setHistoryQuestion(trimmed);
    askHistoryMutation.mutate(trimmed);
  };

  const metrics = [
    {
      key: "jobs",
      label: "Jobs",
      value: loadingJobs ? "..." : recentJobs?.items.length ?? 0,
      hint: "Recent jobs loaded.",
      icon: <Briefcase size={18} weight="bold" />,
    },
    {
      key: "messages",
      label: "Messages",
      value: transcript.length,
      hint: "Current session.",
      icon: <Sparkle size={18} weight="bold" />,
      tone: "warning" as const,
    },
    {
      key: "mode",
      label: "Mode",
      value: COPILOT_TABS.find((tab) => tab.id === activeTab)?.label ?? "Assistant",
      hint: "Active tab.",
      icon: <Brain size={18} weight="bold" />,
    },
    {
      key: "draft",
      label: "Draft",
      value: coverLetter?.style ?? "None",
      hint: "Current letter style.",
      icon: <FileText size={18} weight="bold" />,
      tone: "success" as const,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Prepare" title="Copilot" description="Chat, history, and cover letters." />

      <MetricStrip items={metrics} />

      <Surface tone="default" padding="md" radius="xl">
        <div className="space-y-4">
          <div>
            <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">Workspace</div>
            <h2 className="mt-1 font-display text-xl font-black uppercase tracking-[-0.05em] text-foreground">
              Switch tasks
            </h2>
          </div>
          <Tabs
            tabs={COPILOT_TABS.map((tab) => ({ ...tab }))}
            activeTab={activeTab}
            onChange={(nextTab) => startTransition(() => setActiveTab(nextTab as CopilotTab))}
          />
        </div>
      </Surface>

      {activeTab === "assistant" ? (
        <SplitWorkspace
          primary={
            <TranscriptPanel
              jobOptions={jobOptions}
              selectedJobId={selectedJobId}
              onJobChange={setSelectedJobId}
              transcript={transcript}
              isLoading={chatMutation.isPending}
              onPrompt={sendChat}
              onSend={() => sendChat(chatInput)}
              value={chatInput}
              onValueChange={setChatInput}
            />
          }
          secondary={
            <div className="space-y-4">
              <JobContextPanel
                selectedJobLabel={selectedJob?.title ?? ""}
                selectedJobLocation={selectedJob?.location ?? null}
                matchScore={selectedJob?.match_score ?? null}
                summary={selectedJob?.summary_ai ?? null}
              />
            </div>
          }
        />
      ) : null}

      {activeTab === "history" ? (
        <SplitWorkspace
          primary={
            <HistoryPanel
              question={historyQuestion}
              onQuestionChange={setHistoryQuestion}
              onAnalyze={() => runHistoryQuestion(historyQuestion)}
              loading={askHistoryMutation.isPending}
              answer={historyAnswer}
            />
          }
          secondary={<HistoryActionRail onQuestion={runHistoryQuestion} />}
        />
      ) : null}

      {activeTab === "letters" ? (
        <SplitWorkspace
          primary={
            <LettersPanel
              selectedJobId={selectedJobId}
              jobOptions={jobOptions}
              style={coverLetterStyle}
              onStyleChange={setCoverLetterStyle}
              template={coverLetterTemplate}
              onTemplateChange={setCoverLetterTemplate}
              onJobChange={setSelectedJobId}
              onGenerate={() => coverLetterMutation.mutate()}
              pending={coverLetterMutation.isPending}
              coverLetter={coverLetter}
            />
          }
          secondary={
            <div className="space-y-4">
              <div className="space-y-4">
                <Surface tone="default" padding="md" radius="xl">
                  <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
                    <MagicWand size={16} weight="bold" className="text-[var(--color-accent-success)]" />
                    Draft
                  </div>
                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    {coverLetter ? `${coverLetter.style ?? "custom"} draft ready.` : "No draft yet."}
                  </p>
                </Surface>
                <Surface tone="default" padding="md" radius="xl">
                  <div className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.18em]">
                    <Briefcase size={16} weight="bold" className="text-[var(--color-accent-primary)]" />
                    Job
                  </div>
                  <p className="mt-2 text-sm leading-6 text-text-secondary">
                    {selectedJob
                      ? `${selectedJob.title} at ${selectedJob.company_name ?? "Unknown company"}`
                      : "Choose a job before generating a letter."}
                  </p>
                </Surface>
              </div>
            </div>
          }
        />
      ) : null}
    </div>
  );
}
