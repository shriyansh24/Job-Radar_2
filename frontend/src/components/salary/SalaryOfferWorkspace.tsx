import { CurrencyDollar, TrendUp } from "@phosphor-icons/react";
import { type OfferEvaluation } from "../../api/salary";
import { SectionHeader } from "../system/SectionHeader";
import { Surface } from "../system/Surface";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Skeleton from "../ui/Skeleton";
import { SalaryVerdictDisplay } from "./SalaryWidgets";

export function SalaryOfferWorkspace({
  jobTitle,
  offerAmount,
  evaluation,
  isPending,
  onOfferAmountChange,
  onEvaluate,
}: {
  jobTitle: string;
  offerAmount: string;
  evaluation: OfferEvaluation | null;
  isPending: boolean;
  onOfferAmountChange: (value: string) => void;
  onEvaluate: () => void;
}) {
  return (
    <Surface tone="default" padding="lg" radius="xl" className="hero-panel">
      <SectionHeader title="Offer evaluation" description="Compare an offer against the latest market context." />
      <div className="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1fr)_220px]">
        <Input
          label="Offer amount"
          type="number"
          value={offerAmount}
          onChange={(event) => onOfferAmountChange(event.target.value)}
          placeholder="150000"
          icon={<CurrencyDollar size={16} weight="bold" />}
        />
        <div className="flex items-end">
          <Button
            variant="success"
            className="w-full"
            onClick={onEvaluate}
            loading={isPending}
            disabled={!jobTitle.trim() || !offerAmount || Number(offerAmount) <= 0}
            icon={<TrendUp size={16} weight="bold" />}
          >
            Evaluate
          </Button>
        </div>
      </div>

      {isPending ? <Skeleton variant="rect" className="mt-6 h-24 w-full" /> : null}
      {evaluation ? (
        <div className="mt-6">
          <SalaryVerdictDisplay evaluation={evaluation} />
        </div>
      ) : null}
    </Surface>
  );
}
