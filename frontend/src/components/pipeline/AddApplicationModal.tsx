import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { pipelineApi, type ApplicationCreate } from '../../api/pipeline';
import Modal from '../ui/Modal';
import Input from '../ui/Input';
import Textarea from '../ui/Textarea';
import Button from '../ui/Button';
import { toast } from "../ui/toastService";

interface AddApplicationModalProps {
  open: boolean;
  onClose: () => void;
}

export default function AddApplicationModal({ open, onClose }: AddApplicationModalProps) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ApplicationCreate>({
    company_name: '',
    position_title: '',
    source: 'manual',
  });

  const mutation = useMutation({
    mutationFn: () => pipelineApi.create(form),
    onSuccess: () => {
      toast('success', 'Application created');
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
      onClose();
      setForm({ company_name: '', position_title: '', source: 'manual' });
    },
    onError: () => toast('error', 'Failed to create application'),
  });

  return (
    <Modal open={open} onClose={onClose} title="Add Application">
      <div className="space-y-4">
        <Input
          label="Company Name"
          value={form.company_name}
          onChange={(e) => setForm({ ...form, company_name: e.target.value })}
          placeholder="e.g. Google"
        />
        <Input
          label="Position Title"
          value={form.position_title}
          onChange={(e) => setForm({ ...form, position_title: e.target.value })}
          placeholder="e.g. Senior Software Engineer"
        />
        <Textarea
          label="Notes"
          value={form.notes || ''}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          placeholder="Optional notes..."
        />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button
            variant="primary"
            loading={mutation.isPending}
            disabled={!form.company_name || !form.position_title}
            onClick={() => mutation.mutate()}
          >
            Create
          </Button>
        </div>
      </div>
    </Modal>
  );
}
