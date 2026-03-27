import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { AutoApplyRuleCreate } from "../../api/auto-apply";
import { autoApplyApi } from "../../api/auto-apply";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { toast } from "../ui/toastService";
import { KeywordInput } from "./KeywordInput";

const EMPTY_RULE: AutoApplyRuleCreate = {
  name: "",
  min_match_score: undefined,
  required_keywords: [],
  excluded_keywords: [],
  is_active: true,
};

export function CreateRuleModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<AutoApplyRuleCreate>({ ...EMPTY_RULE });

  const mutation = useMutation({
    mutationFn: () => autoApplyApi.createRule(form),
    onSuccess: () => {
      toast("success", "Rule created");
      queryClient.invalidateQueries({ queryKey: ["auto-apply-rules"] });
      onClose();
      setForm({ ...EMPTY_RULE });
    },
    onError: () => toast("error", "Failed to create rule"),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Rule" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Rule Name"
            value={form.name ?? ""}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="e.g. Senior Frontend Roles"
          />
          <Input
            label="Min Match Score (%)"
            type="number"
            min={0}
            max={100}
            value={form.min_match_score ?? ""}
            onChange={(event) =>
              setForm({
                ...form,
                min_match_score: event.target.value ? Number(event.target.value) : undefined,
              })
            }
            placeholder="e.g. 75"
          />
        </div>
        <KeywordInput
          label="Required Keywords"
          keywords={form.required_keywords ?? []}
          onChange={(keywords) => setForm({ ...form, required_keywords: keywords })}
          placeholder="e.g. React"
        />
        <KeywordInput
          label="Excluded Keywords"
          keywords={form.excluded_keywords ?? []}
          onChange={(keywords) => setForm({ ...form, excluded_keywords: keywords })}
          placeholder="e.g. Intern"
        />
        <label className="flex items-center gap-3 text-sm text-text-secondary">
          <input
            type="checkbox"
            className="size-4 border-2 border-border accent-[var(--color-accent-primary)]"
            checked={form.is_active ?? true}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
          Enable rule immediately
        </label>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={mutation.isPending}
            disabled={!form.name}
            onClick={() => mutation.mutate()}
          >
            Create Rule
          </Button>
        </div>
      </div>
    </Modal>
  );
}
