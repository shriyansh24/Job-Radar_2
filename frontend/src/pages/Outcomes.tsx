import { Buildings, Ghost, HandCoins, TrendUp } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { outcomesApi, type CompanyInsight, type OutcomeMutation } from "../api/outcomes";
import { pipelineApi } from "../api/pipeline";
import { MetricStrip } from "../components/system/MetricStrip";
import { PageHeader } from "../components/system/PageHeader";
import { SplitWorkspace } from "../components/system/SplitWorkspace";
import { StateBlock } from "../components/system/StateBlock";
import Badge from "../components/ui/Badge";
import { OutcomeCapturePanel } from "../components/outcomes/OutcomeCapturePanel";
import { OutcomeCompanyInsightPanel } from "../components/outcomes/OutcomeCompanyInsightPanel";
import { toast } from "../components/ui/toastService";

const emptyForm: OutcomeMutation = {
  stage_reached: null,
  rejection_reason: null,
  rejection_stage: null,
  days_to_response: null,
  offer_amount: null,
  offer_equity: null,
  offer_total_comp: null,
  negotiated_amount: null,
  final_decision: null,
  was_ghosted: false,
  referral_used: false,
  cover_letter_used: false,
  application_method: null,
  feedback_notes: null,
};

export default function Outcomes() {
  const queryClient = useQueryClient();
  const [selectedApplicationId, setSelectedApplicationId] = useState("");
  const [companyQuery, setCompanyQuery] = useState("");
  const [companyInsight, setCompanyInsight] = useState<CompanyInsight | null>(null);
  const [form, setForm] = useState<OutcomeMutation>({ ...emptyForm });

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ["outcomes", "stats"],
    queryFn: () => outcomesApi.getStats().then((response) => response.data),
  });

  const { data: applications } = useQuery({
    queryKey: ["applications", "outcomes-context"],
    queryFn: () => pipelineApi.list(1, 24).then((response) => response.data),
  });

  useEffect(() => {
    if (!selectedApplicationId && applications?.items.length) {
      const first = applications.items[0];
      setSelectedApplicationId(first.id);
      setCompanyQuery(first.company_name ?? "");
    }
  }, [applications, selectedApplicationId]);

  const outcomeQuery = useQuery({
    queryKey: ["outcomes", selectedApplicationId],
    queryFn: () => outcomesApi.get(selectedApplicationId).then((response) => response.data),
    enabled: Boolean(selectedApplicationId),
    retry: false,
  });

  useEffect(() => {
    if (outcomeQuery.data) {
      setForm({
        stage_reached: outcomeQuery.data.stage_reached,
        rejection_reason: outcomeQuery.data.rejection_reason,
        rejection_stage: outcomeQuery.data.rejection_stage,
        days_to_response: outcomeQuery.data.days_to_response,
        offer_amount: outcomeQuery.data.offer_amount,
        offer_equity: outcomeQuery.data.offer_equity,
        offer_total_comp: outcomeQuery.data.offer_total_comp,
        negotiated_amount: outcomeQuery.data.negotiated_amount,
        final_decision: outcomeQuery.data.final_decision,
        was_ghosted: outcomeQuery.data.was_ghosted,
        referral_used: outcomeQuery.data.referral_used,
        cover_letter_used: outcomeQuery.data.cover_letter_used,
        application_method: outcomeQuery.data.application_method,
        feedback_notes: outcomeQuery.data.feedback_notes,
      });
      return;
    }

    const error = outcomeQuery.error as { response?: { status?: number } } | null;
    if (error?.response?.status === 404) {
      setForm({ ...emptyForm });
    }
  }, [outcomeQuery.data, outcomeQuery.error]);

  const companyInsightMutation = useMutation({
    mutationFn: (company: string) => outcomesApi.getCompanyInsights(company).then((response) => response.data),
    onSuccess: (insight) => setCompanyInsight(insight),
    onError: () => toast("error", "Failed to load company insights"),
  });

  const saveMutation = useMutation({
    mutationFn: () => {
      if (!selectedApplicationId) {
        throw new Error("Application is required");
      }

      const error = outcomeQuery.error as { response?: { status?: number } } | null;
      const isMissing = error?.response?.status === 404 || !outcomeQuery.data;
      if (isMissing) {
        return outcomesApi.create(selectedApplicationId, form).then((response) => response.data);
      }
      return outcomesApi.update(selectedApplicationId, form).then((response) => response.data);
    },
    onSuccess: () => {
      toast("success", "Outcome saved");
      queryClient.invalidateQueries({ queryKey: ["outcomes", selectedApplicationId] });
      queryClient.invalidateQueries({ queryKey: ["outcomes", "stats"] });
    },
    onError: () => toast("error", "Failed to save outcome"),
  });

  const selectedApplication =
    applications?.items.find((application) => application.id === selectedApplicationId) ?? null;
  const applicationOptions =
    applications?.items.map((application) => ({
      value: application.id,
      label: `${application.position_title ?? "Unknown role"} · ${application.company_name ?? "Unknown company"}`,
    })) ?? [];

  const rejectionTotal =
    stats?.top_rejection_reasons.reduce((sum, item) => sum + item.count, 0) ?? 0;

  const metrics = [
    {
      key: "response-rate",
      label: "Response Rate",
      value: loadingStats ? "..." : `${Math.round((stats?.response_rate ?? 0) * 100)}%`,
      hint: "Applications that led to an actual response.",
      icon: <TrendUp size={18} weight="bold" />,
      tone: "default" as const,
    },
    {
      key: "ghost-rate",
      label: "Ghost Rate",
      value: loadingStats ? "..." : `${Math.round((stats?.ghosting_rate ?? 0) * 100)}%`,
      hint: "Applications that never received a meaningful reply.",
      icon: <Ghost size={18} weight="bold" />,
      tone: "warning" as const,
    },
    {
      key: "avg-offer",
      label: "Avg Offer",
      value: loadingStats ? "..." : stats?.avg_offer_amount ? `$${Math.round(stats.avg_offer_amount).toLocaleString()}` : "$0",
      hint: "Average offer amount where compensation was captured.",
      icon: <HandCoins size={18} weight="bold" />,
      tone: "success" as const,
    },
  ];

  return (
    <div className="space-y-6 px-4 py-4 sm:px-6 sm:py-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="space-y-6"
      >
        <PageHeader
          eyebrow="Intelligence"
          title="Outcomes"
          description="Track what happened after applications, compare company patterns, and keep the career data grounded in real history."
          meta={
            <>
              <Badge variant="info" size="sm">
                Application outcomes
              </Badge>
              <Badge variant="success" size="sm">
                Company patterns
              </Badge>
            </>
          }
        />

        <MetricStrip items={metrics} />
      </motion.div>

      <SplitWorkspace
        primary={
          <OutcomeCapturePanel
            applications={applications?.items}
            applicationOptions={applicationOptions}
            selectedApplicationId={selectedApplicationId}
            setSelectedApplicationId={setSelectedApplicationId}
            setCompanyQuery={setCompanyQuery}
            form={form}
            setForm={setForm}
            selectedApplication={selectedApplication}
            saveMutation={saveMutation}
            stats={stats}
            loadingStats={loadingStats}
            rejectionTotal={rejectionTotal}
          />
        }
        secondary={
          <div className="space-y-4">
            <OutcomeCompanyInsightPanel
              companyQuery={companyQuery}
              setCompanyQuery={setCompanyQuery}
              companyInsight={companyInsight}
              loading={companyInsightMutation.isPending}
              onLookup={() => companyInsightMutation.mutate(companyQuery)}
            />

            <StateBlock
              tone="neutral"
              icon={<Buildings size={18} weight="bold" />}
              title="Reading this page"
              description="Outcomes are tied to applications, not raw jobs."
            />
            <StateBlock
              tone="warning"
              icon={<Ghost size={18} weight="bold" />}
              title="Keep it honest"
              description="Capture even partial feedback. Structured fragments are still useful."
            />
          </div>
        }
      />
    </div>
  );
}
