import type { EducationEntry, ExperienceEntry } from "../../api/profile";

const JOB_TYPE_OPTIONS = [
  { value: "full_time", label: "Full-time" },
  { value: "part_time", label: "Part-time" },
  { value: "contract", label: "Contract" },
  { value: "freelance", label: "Freelance" },
  { value: "internship", label: "Internship" },
];

const REMOTE_TYPE_OPTIONS = [
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

const WORK_AUTH_OPTIONS = [
  { value: "", label: "Select..." },
  { value: "citizen", label: "US Citizen" },
  { value: "permanent_resident", label: "Permanent Resident" },
  { value: "h1b", label: "H-1B Visa" },
  { value: "opt", label: "OPT/CPT" },
  { value: "ead", label: "EAD" },
  { value: "other", label: "Other" },
];

const EMPTY_EDUCATION: EducationEntry = {
  school: "",
  degree: "",
  field: "",
  start_date: null,
  end_date: null,
};

const EMPTY_EXPERIENCE: ExperienceEntry = {
  company: "",
  title: "",
  start_date: null,
  end_date: null,
  description: null,
};

const BRUTAL_PANEL = "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const BRUTAL_PANEL_ALT = "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-primary)] !shadow-[4px_4px_0px_0px_var(--color-text-primary)]";
const BRUTAL_BUTTON = "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] !shadow-none";
const BRUTAL_PRIMARY_BUTTON = "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-accent-primary)] !text-white !shadow-none";
const BRUTAL_FIELD = "!rounded-none !border-2 !border-[var(--color-text-primary)] !bg-[var(--color-bg-secondary)] !text-[var(--color-text-primary)] placeholder:!text-[var(--color-text-muted)] !shadow-none focus:!border-[var(--color-accent-primary)] focus:!ring-0";

type FormState = {
  full_name: string;
  phone: string;
  location: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  work_authorization: string;
  preferred_job_types: string[];
  preferred_remote_types: string[];
  salary_min: string;
  salary_max: string;
  education: EducationEntry[];
  experience: ExperienceEntry[];
  search_queries: string[];
  search_locations: string[];
  watchlist_companies: string[];
  answer_bank: Record<string, string>;
};

export {
  JOB_TYPE_OPTIONS,
  REMOTE_TYPE_OPTIONS,
  WORK_AUTH_OPTIONS,
  EMPTY_EDUCATION,
  EMPTY_EXPERIENCE,
  BRUTAL_PANEL,
  BRUTAL_PANEL_ALT,
  BRUTAL_BUTTON,
  BRUTAL_PRIMARY_BUTTON,
  BRUTAL_FIELD,
};
export type { FormState };
