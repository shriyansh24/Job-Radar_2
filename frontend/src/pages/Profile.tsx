import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi, type UserProfile } from "../api/profile";
import { toast } from "../components/ui/toastService";
import { useAuthStore } from "../store/useAuthStore";
import {
  ProfileActions,
  ProfileAnswerBankSection,
  ProfileEducationSection,
  ProfileExperienceSection,
  ProfileHero,
  ProfileIdentitySection,
  ProfileMetrics,
  ProfilePreferencesSection,
  ProfileSeedsSection,
  ProfileSidebar,
  type FormState,
} from "../components/profile/ProfileSections";
import { SplitWorkspace } from "../components/system/SplitWorkspace";

function createInitialForm(profile?: UserProfile): FormState {
  return {
    full_name: profile?.full_name ?? "",
    phone: profile?.phone ?? "",
    location: profile?.location ?? "",
    linkedin_url: profile?.linkedin_url ?? "",
    github_url: profile?.github_url ?? "",
    portfolio_url: profile?.portfolio_url ?? "",
    work_authorization: profile?.work_authorization ?? "",
    preferred_job_types: profile?.preferred_job_types ?? [],
    preferred_remote_types: profile?.preferred_remote_types ?? [],
    salary_min: profile?.salary_min?.toString() ?? "",
    salary_max: profile?.salary_max?.toString() ?? "",
    education: profile?.education ?? [],
    experience: profile?.work_experience ?? [],
    search_queries: profile?.search_queries ?? [],
    search_locations: profile?.search_locations ?? [],
    watchlist_companies: profile?.watchlist_companies ?? [],
    answer_bank: profile?.answer_bank ?? {},
  };
}

export default function Profile() {
  const queryClient = useQueryClient();
  const user = useAuthStore((state) => state.user);

  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get().then((response) => response.data),
  });

  const [form, setForm] = useState<FormState>(createInitialForm());

  useEffect(() => {
    if (profile) {
      setForm(createInitialForm(profile));
    }
  }, [profile]);

  const saveMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => profileApi.update(data),
    onSuccess: () => {
      toast("success", "Profile saved");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
    onError: () => toast("error", "Failed to save profile"),
  });

  const answerMutation = useMutation({
    mutationFn: () => profileApi.generateAnswers(),
    onSuccess: () => {
      toast("success", "Answer bank generated");
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
    onError: () => toast("error", "Failed to generate answers"),
  });

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function saveProfile() {
    saveMutation.mutate({
      full_name: form.full_name || undefined,
      phone: form.phone || undefined,
      location: form.location || undefined,
      linkedin_url: form.linkedin_url || undefined,
      github_url: form.github_url || undefined,
      portfolio_url: form.portfolio_url || undefined,
      work_authorization: form.work_authorization || undefined,
      preferred_job_types: form.preferred_job_types,
      preferred_remote_types: form.preferred_remote_types,
      salary_min: form.salary_min ? Number(form.salary_min) : undefined,
      salary_max: form.salary_max ? Number(form.salary_max) : undefined,
      education: form.education,
      work_experience: form.experience,
      search_queries: form.search_queries,
      search_locations: form.search_locations,
      watchlist_companies: form.watchlist_companies,
      answer_bank: form.answer_bank,
    });
  }

  function updateAnswer(question: string, answer: string) {
    updateField("answer_bank", {
      ...form.answer_bank,
      [question]: answer,
    });
  }

  function removeAnswer(question: string) {
    const next = { ...form.answer_bank };
    delete next[question];
    updateField("answer_bank", next);
  }

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 lg:px-8">
      <ProfileHero userEmail={user?.email} />

      <ProfileActions
        onGenerateAnswers={() => answerMutation.mutate()}
        onSaveProfile={saveProfile}
        isGenerating={answerMutation.isPending}
        isSaving={saveMutation.isPending}
      />

      <ProfileMetrics
        searchQueryCount={form.search_queries.length}
        watchlistCount={form.watchlist_companies.length}
        educationCount={form.education.length}
        experienceCount={form.experience.length}
      />

      <SplitWorkspace
        primary={
          <div className="space-y-6">
            <ProfileIdentitySection isLoading={isLoading} form={form} userEmail={user?.email} onUpdateField={updateField} />
            <ProfilePreferencesSection form={form} onUpdateField={updateField} />
            <ProfileSeedsSection form={form} onUpdateField={updateField} />
            <ProfileEducationSection form={form} onUpdateField={updateField} />
            <ProfileExperienceSection form={form} onUpdateField={updateField} />
            <ProfileAnswerBankSection
              answerBank={form.answer_bank}
              onGenerate={() => answerMutation.mutate()}
              onUpdateAnswer={updateAnswer}
              onRemoveAnswer={removeAnswer}
              isGenerating={answerMutation.isPending}
            />
          </div>
        }
        secondary={<ProfileSidebar watchlistCount={form.watchlist_companies.length} searchSeedCount={form.search_queries.length} />}
      />
    </div>
  );
}
