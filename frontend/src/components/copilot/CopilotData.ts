export type CopilotTab = "assistant" | "history" | "letters";

export interface TranscriptEntry {
  id: string;
  role: "user" | "assistant";
  content: string;
  label: string;
}

export const CHAT_PROMPTS = [
  "Summarize my best current targets.",
  "Build a follow-up plan from recent applications.",
  "List the main gaps for senior frontend roles.",
];

export const HISTORY_PROMPTS = [
  "Which companies ghost me after screening?",
  "What interview patterns show up in my outcomes?",
  "Which roles convert best for me?",
];

export const LETTER_STYLES = [
  { value: "professional", label: "Professional" },
  { value: "startup", label: "Startup" },
  { value: "technical", label: "Technical" },
  { value: "career-change", label: "Career Change" },
];
