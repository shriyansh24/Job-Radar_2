import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { jobsApi } from "../api/jobs";
import {
  networkingApi,
  type Contact,
  type ReferralSuggestion,
} from "../api/networking";
import { toast } from "../components/ui/toastService";

export function useNetworkingReferrals({
  contacts,
}: {
  contacts: Contact[] | undefined;
}) {
  const queryClient = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState("");
  const [generatedMessage, setGeneratedMessage] = useState("");
  const [suggestions, setSuggestions] = useState<ReferralSuggestion[]>([]);

  const { data: referralRequests } = useQuery({
    queryKey: ["networking", "referral-requests"],
    queryFn: () => networkingApi.listReferralRequests().then((response) => response.data),
  });

  const { data: recentJobs } = useQuery({
    queryKey: ["jobs", "networking-context"],
    queryFn: () =>
      jobsApi
        .list({ page_size: 12, sort_by: "scraped_at", sort_order: "desc" })
        .then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedJobId && recentJobs?.items.length) {
      setSelectedJobId(recentJobs.items[0].id);
    }
  }, [recentJobs, selectedJobId]);

  const suggestionsMutation = useMutation({
    mutationFn: (jobId: string) => networkingApi.suggestReferrals(jobId).then((response) => response.data),
    onSuccess: (results) => {
      setSuggestions(results);
      if (!results.length) {
        toast("info", "No referral suggestions for that job yet");
      }
    },
    onError: () => toast("error", "Failed to fetch referral suggestions"),
  });

  const outreachMutation = useMutation({
    mutationFn: (payload: { contactId: string; jobId: string }) =>
      networkingApi.generateOutreach(payload.contactId, payload.jobId).then((response) => response.data),
    onSuccess: (response) => {
      setGeneratedMessage(response.message);
    },
    onError: () => toast("error", "Failed to draft outreach"),
  });

  const createReferralRequestMutation = useMutation({
    mutationFn: (payload: { contactId: string; jobId: string; message: string }) =>
      networkingApi
        .createReferralRequest({
          contact_id: payload.contactId,
          job_id: payload.jobId,
          message_template: payload.message || undefined,
        })
        .then((response) => response.data),
    onSuccess: () => {
      toast("success", "Referral request draft created");
      queryClient.invalidateQueries({ queryKey: ["networking", "referral-requests"] });
    },
    onError: () => toast("error", "Failed to create referral request"),
  });

  const jobOptions =
    recentJobs?.items.map((job) => ({
      value: job.id,
      label: `${job.title} - ${job.company_name ?? "Unknown company"}`,
    })) ?? [];

  const selectedJob = recentJobs?.items.find((job) => job.id === selectedJobId) ?? null;

  const referralQueueItems =
    referralRequests?.map((request) => {
      const requestContact = contacts?.find((contact) => contact.id === request.contact_id);
      return {
        id: request.id,
        contactName: requestContact?.name ?? "Unknown contact",
        jobLabel: `Job ${request.job_id.slice(0, 10)}...`,
        status: request.status,
        messageTemplate: request.message_template,
      };
    }) ?? [];

  return {
    createReferralRequestMutation,
    generatedMessage,
    jobOptions,
    outreachMutation,
    recentJobs,
    referralQueueItems,
    referralRequests,
    selectedJob,
    selectedJobId,
    setGeneratedMessage,
    setSelectedJobId,
    suggestions,
    suggestionsMutation,
  };
}
