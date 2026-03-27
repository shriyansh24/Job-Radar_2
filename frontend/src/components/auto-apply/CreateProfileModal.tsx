import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { AutoApplyProfileCreate } from "../../api/auto-apply";
import { autoApplyApi } from "../../api/auto-apply";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Input from "../ui/Input";
import Textarea from "../ui/Textarea";
import { toast } from "../ui/toastService";

const EMPTY_PROFILE: AutoApplyProfileCreate = {
  name: "",
  email: "",
  phone: "",
  linkedin_url: "",
  github_url: "",
  portfolio_url: "",
  cover_letter_template: "",
};

export function CreateProfileModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<AutoApplyProfileCreate>({ ...EMPTY_PROFILE });

  const mutation = useMutation({
    mutationFn: () => autoApplyApi.createProfile(form),
    onSuccess: () => {
      toast("success", "Profile created");
      queryClient.invalidateQueries({ queryKey: ["auto-apply-profiles"] });
      onClose();
      setForm({ ...EMPTY_PROFILE });
    },
    onError: () => toast("error", "Failed to create profile"),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Profile" size="lg">
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Name"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="e.g. Default Profile"
          />
          <Input
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            placeholder="e.g. john@example.com"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Phone"
            value={form.phone ?? ""}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
            placeholder="e.g. +1 555 123 4567"
          />
          <Input
            label="LinkedIn URL"
            value={form.linkedin_url ?? ""}
            onChange={(event) => setForm({ ...form, linkedin_url: event.target.value })}
            placeholder="e.g. https://linkedin.com/in/johndoe"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="GitHub URL"
            value={form.github_url ?? ""}
            onChange={(event) => setForm({ ...form, github_url: event.target.value })}
            placeholder="e.g. https://github.com/johndoe"
          />
          <Input
            label="Portfolio URL"
            value={form.portfolio_url ?? ""}
            onChange={(event) => setForm({ ...form, portfolio_url: event.target.value })}
            placeholder="e.g. https://johndoe.dev"
          />
        </div>
        <Textarea
          label="Cover Letter Template"
          value={form.cover_letter_template ?? ""}
          onChange={(event) => setForm({ ...form, cover_letter_template: event.target.value })}
          placeholder="Write a default cover letter template. Use {company} and {position} as placeholders..."
          rows={5}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            loading={mutation.isPending}
            disabled={!form.name || !form.email}
            onClick={() => mutation.mutate()}
          >
            Create Profile
          </Button>
        </div>
      </div>
    </Modal>
  );
}
