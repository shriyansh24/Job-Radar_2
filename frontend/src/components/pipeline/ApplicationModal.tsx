import { ArrowRight } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { pipelineApi, type Application, type StatusHistory } from "../../api/pipeline";
import Badge from "../ui/Badge";
import Modal from "../ui/Modal";
import { statusBadgeVariant } from "./ApplicationCard";

interface ApplicationModalProps {
  open: boolean;
  onClose: () => void;
  application: Application | null;
}

export default function ApplicationModal({ open, onClose, application }: ApplicationModalProps) {
  const { data: history } = useQuery({
    queryKey: ['application-history', application?.id],
    queryFn: () => pipelineApi.history(application!.id).then((r) => r.data),
    enabled: open && !!application,
  });

  return (
    <Modal open={open} onClose={onClose} title={`History: ${application?.position_title}`}>
      <div className="space-y-3">
        {(history as StatusHistory[] | undefined)?.map((h, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="mt-1">
              <ArrowRight size={14} weight="bold" className="text-accent-primary" />
            </div>
            <div>
              <p className="text-sm text-text-primary">
                {h.old_status ? (
                  <><Badge size="sm">{h.old_status}</Badge> &rarr; <Badge variant={statusBadgeVariant(h.new_status)} size="sm">{h.new_status}</Badge></>
                ) : (
                  <>Created as <Badge variant={statusBadgeVariant(h.new_status)} size="sm">{h.new_status}</Badge></>
                )}
              </p>
              {h.note && <p className="text-xs text-text-muted mt-0.5">{h.note}</p>}
              <p className="text-xs text-text-muted mt-0.5">{format(new Date(h.changed_at), 'PPp')}</p>
            </div>
          </div>
        )) || <p className="text-sm text-text-muted">Loading...</p>}
      </div>
    </Modal>
  );
}
