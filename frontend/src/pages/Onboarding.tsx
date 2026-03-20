import {
  FileText,
  CheckCircle,
  Plus,
  X,
  Key,
  MagnifyingGlass,
  RocketLaunch,
  UploadSimple,
  Buildings,
  UserCircle,
} from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { profileApi } from "../api/profile";
import { resumeApi } from "../api/resume";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import { toast } from "../components/ui/Toast";

const STEPS = [
  { label: "Welcome", icon: <RocketLaunch size={16} weight="bold" /> },
  { label: "Profile", icon: <UserCircle size={16} weight="bold" /> },
  { label: "Resume", icon: <FileText size={16} weight="bold" /> },
  { label: "Search", icon: <MagnifyingGlass size={16} weight="bold" /> },
  { label: "Watchlist", icon: <Buildings size={16} weight="bold" /> },
  { label: "API Keys", icon: <Key size={16} weight="bold" /> },
  { label: "Ready", icon: <CheckCircle size={16} weight="bold" /> },
];

interface FormData {
  fullName: string;
  location: string;
  resumeFile: File | null;
  resumeUploaded: boolean;
  searchQueries: string[];
  searchLocations: string[];
  watchlistCompanies: string[];
  openrouterKey: string;
  serpapiKey: string;
}

function ProgressBar({ currentStep }: { currentStep: number }) {
  return (
    <div className="w-full mb-8">
      <div className="flex items-center justify-between">
        {STEPS.map((step, i) => (
          <div key={step.label} className="flex flex-col items-center flex-1">
            <div className="flex items-center w-full">
              {i > 0 && (
                <div
                  className={`flex-1 h-0.5 ${
                    i <= currentStep ? 'bg-accent-primary' : 'bg-border'
                  }`}
                />
              )}
              <div
                className={`flex items-center justify-center w-8 h-8 rounded-full border-2 shrink-0 transition-colors ${
                  i < currentStep
                    ? 'bg-accent-primary border-accent-primary text-white'
                    : i === currentStep
                      ? 'border-accent-primary text-accent-primary bg-accent-primary/10'
                      : 'border-border text-text-muted bg-bg-tertiary'
                }`}
              >
                {i < currentStep ? (
                  <CheckCircle size={16} weight="bold" />
                ) : (
                  step.icon
                )}
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 ${
                    i < currentStep ? 'bg-accent-primary' : 'bg-border'
                  }`}
                />
              )}
            </div>
            <span
              className={`mt-2 text-xs font-medium ${
                i <= currentStep ? 'text-text-primary' : 'text-text-muted'
              }`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TagInput({
  label,
  placeholder,
  tags,
  onAdd,
  onRemove,
}: {
  label: string;
  placeholder: string;
  tags: string[];
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
}) {
  const [inputValue, setInputValue] = useState('');

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault();
      onAdd(inputValue.trim());
      setInputValue('');
    }
  }

  function handleAddClick() {
    if (inputValue.trim()) {
      onAdd(inputValue.trim());
      setInputValue('');
    }
  }

  return (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-1.5">
        {label}
      </label>
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
        />
        <Button
          variant="secondary"
          size="md"
          icon={<Plus size={14} />}
          onClick={handleAddClick}
          disabled={!inputValue.trim()}
        >
          Add
        </Button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {tags.map((tag, i) => (
            <Badge key={i} variant="info" size="md">
              <span className="flex items-center gap-1.5">
                {tag}
                <button
                  type="button"
                  onClick={() => onRemove(i)}
                  className="hover:text-accent-danger transition-colors"
                >
                  <X size={12} />
                </button>
              </span>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<FormData>({
    fullName: '',
    location: '',
    resumeFile: null,
    resumeUploaded: false,
    searchQueries: [],
    searchLocations: [],
    watchlistCompanies: [],
    openrouterKey: '',
    serpapiKey: '',
  });

  const profileMutation = useMutation({
    mutationFn: () =>
      profileApi.update({
        full_name: formData.fullName || null,
        location: formData.location || null,
        search_queries: formData.searchQueries,
        search_locations: formData.searchLocations,
        watchlist_companies: formData.watchlistCompanies,
      }),
    onSuccess: () => {
      toast('success', 'Profile saved! Welcome to JobRadar.');
      navigate('/jobs');
    },
    onError: () => toast('error', 'Failed to save profile. Please try again.'),
  });

  const resumeMutation = useMutation({
    mutationFn: (file: File) => resumeApi.upload(file),
    onSuccess: () => {
      setFormData((prev) => ({ ...prev, resumeUploaded: true }));
      toast('success', 'Resume uploaded successfully');
    },
    onError: () => toast('error', 'Failed to upload resume'),
  });

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        setFormData((prev) => ({ ...prev, resumeFile: file }));
        resumeMutation.mutate(file);
      }
    },
    [resumeMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    multiple: false,
  });

  function handleNext() {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    }
  }

  function handleBack() {
    if (step > 0) {
      setStep((s) => s - 1);
    }
  }

  function handleFinish() {
    profileMutation.mutate();
  }

  function addSearchQuery(value: string) {
    if (!formData.searchQueries.includes(value)) {
      setFormData((prev) => ({
        ...prev,
        searchQueries: [...prev.searchQueries, value],
      }));
    }
  }

  function removeSearchQuery(index: number) {
    setFormData((prev) => ({
      ...prev,
      searchQueries: prev.searchQueries.filter((_, i) => i !== index),
    }));
  }

  function addSearchLocation(value: string) {
    if (!formData.searchLocations.includes(value)) {
      setFormData((prev) => ({
        ...prev,
        searchLocations: [...prev.searchLocations, value],
      }));
    }
  }

  function removeSearchLocation(index: number) {
    setFormData((prev) => ({
      ...prev,
      searchLocations: prev.searchLocations.filter((_, i) => i !== index),
    }));
  }

  function addWatchlistCompany(value: string) {
    if (!formData.watchlistCompanies.includes(value)) {
      setFormData((prev) => ({
        ...prev,
        watchlistCompanies: [...prev.watchlistCompanies, value],
      }));
    }
  }

  function removeWatchlistCompany(index: number) {
    setFormData((prev) => ({
      ...prev,
      watchlistCompanies: prev.watchlistCompanies.filter((_, i) => i !== index),
    }));
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg-primary p-4">
      <div className="w-full max-w-2xl">
        <ProgressBar currentStep={step} />

        <Card padding="lg">
          {/* Step 0: Welcome */}
          {step === 0 && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent-primary/10 mb-6">
                <RocketLaunch size={32} weight="bold" className="text-accent-primary" />
              </div>
              <h2 className="text-2xl font-bold text-text-primary mb-3">
                Welcome to JobRadar
              </h2>
              <p className="text-text-secondary max-w-md mx-auto mb-8">
                Your intelligent job search companion. Let's get you set up in just a few
                steps so we can find the best opportunities for you.
              </p>
              <Button variant="primary" size="lg" onClick={handleNext}>
                Get Started
              </Button>
            </div>
          )}

          {/* Step 1: Profile */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-text-primary mb-1">
                  Your Profile
                </h2>
                <p className="text-sm text-text-muted">
                  Tell us a bit about yourself so we can personalize your experience.
                </p>
              </div>
              <Input
                label="Full Name"
                placeholder="Jane Doe"
                value={formData.fullName}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, fullName: e.target.value }))
                }
              />
              <Input
                label="Location"
                placeholder="San Francisco, CA"
                value={formData.location}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, location: e.target.value }))
                }
              />
            </div>
          )}

          {/* Step 2: Resume */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-text-primary mb-1">
                  Upload Your Resume
                </h2>
                <p className="text-sm text-text-muted">
                  We'll use your resume to match you with relevant jobs and tailor
                  applications.
                </p>
              </div>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-[var(--radius-lg)] p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-accent-primary bg-accent-primary/5'
                    : formData.resumeUploaded
                      ? 'border-accent-success bg-accent-success/5'
                      : 'border-border hover:border-border-focus'
                }`}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center gap-3">
                  {formData.resumeUploaded ? (
                    <>
                      <CheckCircle size={40} className="text-accent-success" />
                      <p className="text-sm font-medium text-text-primary">
                        {formData.resumeFile?.name}
                      </p>
                      <p className="text-xs text-text-muted">
                        Resume uploaded successfully. Drop a new file to replace.
                      </p>
                    </>
                  ) : resumeMutation.isPending ? (
                    <>
                      <UploadSimple
                        size={40}
                        weight="bold"
                        className="text-accent-primary animate-pulse"
                      />
                      <p className="text-sm text-text-secondary">Uploading...</p>
                    </>
                  ) : (
                    <>
                      <UploadSimple size={40} weight="bold" className="text-text-muted" />
                      {isDragActive ? (
                        <p className="text-sm text-accent-primary font-medium">
                          Drop your resume here
                        </p>
                      ) : (
                        <>
                          <p className="text-sm text-text-secondary">
                            Drag and drop your resume, or click to browse
                          </p>
                          <p className="text-xs text-text-muted">
                            PDF, DOC, or DOCX (max 10MB)
                          </p>
                        </>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Search Preferences */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-text-primary mb-1">
                  Search Preferences
                </h2>
                <p className="text-sm text-text-muted">
                  Add the job titles you're interested in and your preferred locations.
                </p>
              </div>
              <TagInput
                label="Job Titles"
                placeholder="e.g. Software Engineer"
                tags={formData.searchQueries}
                onAdd={addSearchQuery}
                onRemove={removeSearchQuery}
              />
              <TagInput
                label="Preferred Locations"
                placeholder="e.g. Remote, New York"
                tags={formData.searchLocations}
                onAdd={addSearchLocation}
                onRemove={removeSearchLocation}
              />
            </div>
          )}

          {/* Step 4: Watchlist */}
          {step === 4 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-text-primary mb-1">
                  Watchlist Companies
                </h2>
                <p className="text-sm text-text-muted">
                  Add companies you'd like to track. We'll alert you when they post new jobs.
                </p>
              </div>
              <TagInput
                label="Companies"
                placeholder="e.g. Google, Stripe, Anthropic"
                tags={formData.watchlistCompanies}
                onAdd={addWatchlistCompany}
                onRemove={removeWatchlistCompany}
              />
            </div>
          )}

          {/* Step 5: API Keys */}
          {step === 5 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-text-primary mb-1">
                  API Keys
                </h2>
                <p className="text-sm text-text-muted">
                  Optional: Add API keys to enable AI features and expanded job search.
                </p>
              </div>
              <Input
                label="OpenRouter API Key"
                placeholder="sk-or-..."
                value={formData.openrouterKey}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, openrouterKey: e.target.value }))
                }
                type="password"
              />
              <p className="text-xs text-text-muted -mt-4">
                Powers AI resume tailoring, interview prep, and cover letter generation.
              </p>
              <Input
                label="SerpAPI Key"
                placeholder="Enter your SerpAPI key..."
                value={formData.serpapiKey}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, serpapiKey: e.target.value }))
                }
                type="password"
              />
              <p className="text-xs text-text-muted -mt-4">
                Enables Google Jobs search for broader job discovery.
              </p>
            </div>
          )}

          {/* Step 6: Ready */}
          {step === 6 && (
            <div className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent-success/10 mb-4">
                  <CheckCircle size={32} className="text-accent-success" />
                </div>
                <h2 className="text-xl font-bold text-text-primary mb-1">
                  You're All Set!
                </h2>
                <p className="text-sm text-text-muted">
                  Here's a summary of what you've configured:
                </p>
              </div>

              <div className="space-y-3">
                {formData.fullName && (
                  <div className="flex items-center gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                    <UserCircle size={16} weight="bold" className="text-text-muted shrink-0" />
                    <div>
                      <p className="text-xs text-text-muted">Name</p>
                      <p className="text-sm font-medium text-text-primary">
                        {formData.fullName}
                      </p>
                    </div>
                  </div>
                )}

                {formData.location && (
                  <div className="flex items-center gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                    <MagnifyingGlass
                      size={16}
                      weight="bold"
                      className="text-text-muted shrink-0"
                    />
                    <div>
                      <p className="text-xs text-text-muted">Location</p>
                      <p className="text-sm font-medium text-text-primary">
                        {formData.location}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                  <FileText size={16} className="text-text-muted shrink-0" />
                  <div>
                    <p className="text-xs text-text-muted">Resume</p>
                    <p className="text-sm font-medium text-text-primary">
                      {formData.resumeUploaded
                        ? formData.resumeFile?.name ?? 'Uploaded'
                        : 'Skipped'}
                    </p>
                  </div>
                </div>

                {formData.searchQueries.length > 0 && (
                  <div className="flex items-start gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                    <MagnifyingGlass
                      size={16}
                      weight="bold"
                      className="text-text-muted shrink-0 mt-0.5"
                    />
                    <div>
                      <p className="text-xs text-text-muted">Job Titles</p>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {formData.searchQueries.map((q) => (
                          <Badge key={q} variant="info" size="sm">
                            {q}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {formData.searchLocations.length > 0 && (
                  <div className="flex items-start gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                    <MagnifyingGlass
                      size={16}
                      weight="bold"
                      className="text-text-muted shrink-0 mt-0.5"
                    />
                    <div>
                      <p className="text-xs text-text-muted">Preferred Locations</p>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {formData.searchLocations.map((l) => (
                          <Badge key={l} variant="info" size="sm">
                            {l}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {formData.watchlistCompanies.length > 0 && (
                  <div className="flex items-start gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                    <Buildings size={16} weight="bold" className="text-text-muted shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-text-muted">Watchlist Companies</p>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {formData.watchlistCompanies.map((c) => (
                          <Badge key={c} variant="info" size="sm">
                            {c}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3 px-4 py-3 bg-bg-tertiary rounded-[var(--radius-md)]">
                  <Key size={16} className="text-text-muted shrink-0" />
                  <div>
                    <p className="text-xs text-text-muted">API Keys</p>
                    <p className="text-sm font-medium text-text-primary">
                      {formData.openrouterKey || formData.serpapiKey
                        ? [
                            formData.openrouterKey && 'OpenRouter',
                            formData.serpapiKey && 'SerpAPI',
                          ]
                            .filter(Boolean)
                            .join(', ')
                        : 'Skipped'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          {step > 0 && (
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-border">
              <Button variant="ghost" onClick={handleBack}>
                Back
              </Button>
              <div className="flex items-center gap-3">
                {((step === 2 && !formData.resumeUploaded) || step === 4 || step === 5) && (
                  <Button variant="ghost" onClick={handleNext}>
                    Skip
                  </Button>
                )}
                {step < STEPS.length - 1 ? (
                  <Button variant="primary" onClick={handleNext}>
                    Next
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    loading={profileMutation.isPending}
                    onClick={handleFinish}
                  >
                    Start Searching
                  </Button>
                )}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
