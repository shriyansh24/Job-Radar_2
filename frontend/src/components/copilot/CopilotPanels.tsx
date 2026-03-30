import { Brain, Briefcase, FileText, Lightbulb, MagicWand, Sparkle } from "@phosphor-icons/react";
import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { type CoverLetterResult } from "../../api/copilot";
import { cn } from "../../lib/utils";
import {
  CHAT_PROMPTS,
  LETTER_STYLES,
  HISTORY_PROMPTS,
} from "./CopilotData";
import { type TranscriptEntry } from "./CopilotData";
import Badge from "../ui/Badge";
import EmptyState from "../ui/EmptyState";
import Select from "../ui/Select";
import Skeleton from "../ui/Skeleton";
import Textarea from "../ui/Textarea";
import { SectionHeader } from "../system/SectionHeader";
import { StateBlock } from "../system/StateBlock";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";

export function MarkdownBlock({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none text-text-primary prose-p:leading-6 prose-headings:text-text-primary prose-strong:text-text-primary prose-li:text-text-secondary prose-p:text-text-secondary dark:prose-invert">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}

export function TranscriptPanel({
  jobOptions,
  selectedJobId,
  onJobChange,
  transcript,
  isLoading,
  onPrompt,
  onSend,
  value,
  onValueChange,
}: {
  jobOptions: { value: string; label: string }[];
  selectedJobId: string;
  onJobChange: (value: string) => void;
  transcript: TranscriptEntry[];
  isLoading: boolean;
  onPrompt: (prompt: string) => void;
  onSend: () => void;
  value: string;
  onValueChange: (value: string) => void;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader title="Chat" description="Choose a job and send prompts." />
      <div className="mt-6">
        <Select
          label="Job"
          value={selectedJobId}
          onChange={(event) => onJobChange(event.target.value)}
          options={jobOptions}
          placeholder="Choose a job"
        />
      </div>
      <div className="mt-6">
        {transcript.length === 0 ? (
          <EmptyState
            icon={<Sparkle size={34} weight="bold" />}
            title="Start a chat"
            description="Choose a job or send a prompt."
          />
        ) : (
          <div className="space-y-4">
            {transcript.map((entry, index) => (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: index * 0.03 }}
                className={cn(
                  "border-2 px-4 py-4",
                  entry.role === "assistant"
                    ? "max-w-[48rem] border-border bg-[var(--color-bg-secondary)]"
                    : "ml-auto max-w-[48rem] border-border bg-[var(--color-accent-primary-subtle)]"
                )}
              >
                <div className="mb-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-muted">
                  {entry.label}
                </div>
                <MarkdownBlock content={entry.content} />
              </motion.div>
            ))}
          </div>
        )}
        {isLoading ? (
          <div className="mt-4 border-2 border-border bg-[var(--color-bg-tertiary)] px-4 py-4">
            <Skeleton variant="text" className="h-4 w-28" />
            <Skeleton variant="text" className="mt-3 h-4 w-full" />
            <Skeleton variant="text" className="mt-2 h-4 w-5/6" />
          </div>
        ) : null}
      </div>

      <div className="mt-6 space-y-4 border-t-2 border-border pt-6">
        <div className="flex flex-wrap gap-2">
          {CHAT_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => onPrompt(prompt)}
              className="border-2 border-border bg-[var(--color-bg-secondary)] px-3 py-2 font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-text-secondary transition-colors hover:bg-[var(--color-bg-tertiary)] hover:text-text-primary"
            >
              {prompt}
            </button>
          ))}
        </div>
        <Textarea
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          placeholder="Ask about search, interviews, or application triage."
          className="min-h-[120px]"
        />
        <div className="flex justify-end">
          <Button
            variant="primary"
            onClick={onSend}
            disabled={!value.trim()}
            icon={<Sparkle size={16} weight="bold" />}
          >
            Send
          </Button>
        </div>
      </div>
    </Surface>
  );
}

export function JobContextPanel({
  selectedJobLabel,
  selectedJobLocation,
  matchScore,
  summary,
}: {
  selectedJobLabel: string;
  selectedJobLocation: string | null;
  matchScore: number | null;
  summary: string | null;
}) {
  return selectedJobLabel ? (
    <Surface tone="default" padding="md" radius="xl">
      <SectionHeader title="Job" />
      <div className="mt-4 space-y-3 text-sm leading-6 text-text-secondary">
        <p>{selectedJobLocation ?? "Flexible location"}</p>
        {matchScore !== null ? (
          <Badge variant={matchScore >= 0.7 ? "success" : "warning"}>Match {Math.round(matchScore * 100)}%</Badge>
        ) : null}
        <p>{summary ?? "No summary yet."}</p>
      </div>
    </Surface>
  ) : (
    <StateBlock
      tone="muted"
      icon={<Briefcase size={18} weight="bold" />}
      title="No job selected"
      description="Choose a job to add context."
    />
  );
}

export function HistoryPanel({
  question,
  onQuestionChange,
  onAnalyze,
  loading,
  answer,
}: {
  question: string;
  onQuestionChange: (value: string) => void;
  onAnalyze: () => void;
  loading: boolean;
  answer: string;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader title="History" description="Query applications and outcomes." />
      <Textarea
        className="mt-6 min-h-[180px]"
        value={question}
        onChange={(event) => onQuestionChange(event.target.value)}
        placeholder="Example: Which roles lead to callbacks?"
      />
      <div className="mt-4 flex justify-end">
        <Button variant="primary" onClick={onAnalyze} disabled={!question.trim() || loading} icon={<Brain size={16} weight="bold" />}>
          Analyze
        </Button>
      </div>

      <div className="mt-6 border-t-2 border-border pt-6">
        {loading ? (
          <div className="space-y-3">
            <Skeleton variant="text" className="h-4 w-1/3" />
            <Skeleton variant="text" className="h-4 w-full" />
            <Skeleton variant="text" className="h-4 w-5/6" />
            <Skeleton variant="text" className="h-4 w-4/5" />
          </div>
        ) : answer ? (
          <MarkdownBlock content={answer} />
        ) : (
          <EmptyState icon={<Lightbulb size={32} weight="bold" />} title="No answer yet" description="Run a question." />
        )}
      </div>
    </Surface>
  );
}

export function LettersPanel({
  selectedJobId,
  jobOptions,
  style,
  onStyleChange,
  template,
  onTemplateChange,
  onJobChange,
  onGenerate,
  pending,
  coverLetter,
}: {
  selectedJobId: string;
  jobOptions: { value: string; label: string }[];
  style: string;
  onStyleChange: (value: string) => void;
  template: string;
  onTemplateChange: (value: string) => void;
  onJobChange: (value: string) => void;
  onGenerate: () => void;
  pending: boolean;
  coverLetter: CoverLetterResult | null;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl">
      <SectionHeader title="Letters" description="Generate a draft for the selected job." />
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Select
          label="Job"
          value={selectedJobId}
          onChange={(event) => onJobChange(event.target.value)}
          options={jobOptions}
          placeholder="Choose a job"
        />
        <Select
          label="Style"
          value={style}
          onChange={(event) => onStyleChange(event.target.value)}
          options={LETTER_STYLES}
        />
      </div>
      <Textarea
        label="Notes"
        className="mt-4 min-h-[220px]"
        value={template}
        onChange={(event) => onTemplateChange(event.target.value)}
        placeholder="Optional notes for tone or emphasis."
      />
      <div className="mt-4 flex justify-end">
        <Button variant="primary" onClick={onGenerate} disabled={!selectedJobId || pending} icon={<MagicWand size={16} weight="bold" />}>
          Generate
        </Button>
      </div>

      <div className="mt-6 border-t-2 border-border pt-6">
        {pending ? (
          <div className="space-y-3">
            <Skeleton variant="text" className="h-4 w-1/4" />
            <Skeleton variant="text" className="h-4 w-full" />
            <Skeleton variant="text" className="h-4 w-full" />
            <Skeleton variant="text" className="h-4 w-5/6" />
          </div>
        ) : coverLetter ? (
          <Surface tone="subtle" padding="md" radius="xl">
            <div className="text-sm leading-6 text-text-secondary">{coverLetter.content}</div>
          </Surface>
        ) : (
          <EmptyState icon={<FileText size={32} weight="bold" />} title="No draft" description="Generate a draft for the selected job." />
        )}
      </div>
    </Surface>
  );
}

export function HistoryActionRail({
  onQuestion,
}: {
  onQuestion: (prompt: string) => void;
}) {
  return (
    <Surface tone="default" padding="md" radius="xl">
      <SectionHeader title="Quick prompts" />
      <div className="mt-4 space-y-2">
        {HISTORY_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => onQuestion(prompt)}
            className="w-full border-2 border-border bg-[var(--color-bg-secondary)] px-4 py-3 text-left text-sm leading-6 text-text-secondary transition-colors hover:bg-[var(--color-bg-tertiary)] hover:text-text-primary"
          >
            {prompt}
          </button>
        ))}
      </div>
    </Surface>
  );
}
