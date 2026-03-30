export type SearchMode = "exact" | "semantic";

export const SOURCE_OPTIONS = [
  { value: "", label: "All sources" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "indeed", label: "Indeed" },
  { value: "glassdoor", label: "Glassdoor" },
  { value: "theirstack", label: "TheirStack" },
  { value: "career_page", label: "Career page" },
];

export const REMOTE_OPTIONS = [
  { value: "", label: "All remote types" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

export const EXPERIENCE_OPTIONS = [
  { value: "", label: "All levels" },
  { value: "entry", label: "Entry" },
  { value: "mid", label: "Mid" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead" },
  { value: "executive", label: "Executive" },
];

export const SORT_OPTIONS = [
  { value: "scraped_at", label: "Date" },
  { value: "match_score", label: "Match score" },
  { value: "tfidf_score", label: "TF-IDF score" },
  { value: "company_name", label: "Company" },
];

export function scoreLabel(score: number | null) {
  if (score === null) return null;
  return `${Math.round(score * 100)}%`;
}

export function freshnessLabel(score: number | null | undefined) {
  if (score == null) return null;
  return `Fresh ${Math.round(score * 100)}%`;
}

export function freshnessVariant(
  score: number | null | undefined
): "success" | "warning" | "danger" | "default" {
  if (score == null) return "default";
  if (score >= 0.75) return "success";
  if (score >= 0.45) return "warning";
  return "danger";
}
