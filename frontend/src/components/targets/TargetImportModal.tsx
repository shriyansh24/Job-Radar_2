import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState, type ChangeEvent } from "react";
import { UploadSimple, CheckCircle, Warning } from "@phosphor-icons/react";
import { scraperApi } from "../../api/scraper";
import Modal from "../ui/Modal";
import Button from "../ui/Button";
import Textarea from "../ui/Textarea";
import { toast } from "../ui/toastService";
import { getSafeExternalUrl } from "../../lib/utils";

interface ImportEntry {
  url: string;
  company_name?: string;
}

function normalizeImportEntries(entries: ImportEntry[]) {
  const normalized: ImportEntry[] = [];

  for (const entry of entries) {
    const safeUrl = getSafeExternalUrl(entry.url);
    if (!safeUrl) {
      return {
        entries: [] as ImportEntry[],
        error: 'Each entry must have a valid "http://" or "https://" URL',
      };
    }

    normalized.push({
      ...entry,
      url: safeUrl,
    });
  }

  return { entries: normalized, error: null as string | null };
}

export function TargetImportModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [jsonText, setJsonText] = useState("");
  const [preview, setPreview] = useState<ImportEntry[] | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: (targets: ImportEntry[]) => scraperApi.importTargets(targets).then((r) => r.data),
    onSuccess: (result) => {
      toast(
        "success",
        `Imported ${result.imported}, skipped ${result.skipped}${result.errors.length ? `, ${result.errors.length} errors` : ""}`
      );
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      onClose();
      setJsonText("");
      setPreview(null);
    },
    onError: () => toast("error", "Import failed"),
  });

  const handleParse = () => {
    setParseError(null);
    try {
      const parsed = JSON.parse(jsonText.trim());
      if (!Array.isArray(parsed)) {
        setParseError("Expected a JSON array");
        setPreview(null);
        return;
      }
      const entries = parsed as ImportEntry[];
      if (entries.some((entry) => !entry.url)) {
        setParseError('Each entry must have a "url" field');
        setPreview(null);
        return;
      }
      const { entries: normalizedEntries, error } = normalizeImportEntries(entries);
      if (error) {
        setParseError(error);
        setPreview(null);
        return;
      }
      setPreview(normalizedEntries);
    } catch (err) {
      setParseError(`Invalid JSON: ${(err as Error).message}`);
      setPreview(null);
    }
  };

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      if (file.name.endsWith(".csv")) {
        const lines = text.trim().split("\n");
        const headers = lines[0].split(",").map((header) => header.trim().replace(/^"|"$/g, ""));
        const urlIdx = headers.findIndex((header) => header.toLowerCase() === "url");
        const nameIdx = headers.findIndex(
          (header) => header.toLowerCase() === "company_name" || header.toLowerCase() === "company"
        );
        if (urlIdx === -1) {
          setParseError('CSV must have a "url" column');
          return;
        }
        const entries: ImportEntry[] = lines.slice(1).map((line) => {
          const cols = line.split(",").map((col) => col.trim().replace(/^"|"$/g, ""));
          return {
            url: cols[urlIdx] ?? "",
            ...(nameIdx !== -1 ? { company_name: cols[nameIdx] } : {}),
          };
        });
        const { entries: normalizedEntries, error } = normalizeImportEntries(entries);
        if (error) {
          setParseError(error);
          setPreview(null);
          return;
        }
        setJsonText(JSON.stringify(normalizedEntries, null, 2));
        setPreview(normalizedEntries);
      } else {
        setJsonText(text);
        setParseError(null);
        setPreview(null);
      }
    } catch {
      setParseError("Failed to read file");
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleClose = () => {
    onClose();
    setJsonText("");
    setPreview(null);
    setParseError(null);
  };

  return (
    <Modal open={open} onClose={handleClose} title="Import Targets" size="lg">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <p className="flex-1 text-sm text-text-secondary">
            Paste a JSON array of <code className="rounded bg-bg-tertiary px-1 py-0.5 font-mono text-xs">{"[{url, company_name}]"}</code> or upload a CSV / JSON file.
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.csv"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            icon={<UploadSimple size={14} weight="bold" />}
          >
            Upload File
          </Button>
        </div>

        <Textarea
          label="JSON Array"
          placeholder='[{"url": "https://...", "company_name": "Acme"}]'
          value={jsonText}
          onChange={(event) => {
            setJsonText(event.target.value);
            setPreview(null);
            setParseError(null);
          }}
          rows={8}
          className="font-mono text-xs"
        />

        {parseError ? (
          <p className="flex items-center gap-1 text-xs text-accent-danger">
            <Warning size={14} weight="fill" />
            {parseError}
          </p>
        ) : null}

        {!preview ? (
          <Button variant="secondary" size="sm" onClick={handleParse} disabled={!jsonText.trim()}>
            Preview
          </Button>
        ) : null}

        {preview ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle size={16} weight="fill" className="text-accent-success" />
              <p className="text-sm font-medium text-text-primary">
                {preview.length} target{preview.length !== 1 ? "s" : ""} ready to import
              </p>
            </div>
            <div className="overflow-hidden border-2 border-border">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-[var(--color-bg-tertiary)] text-text-muted">
                    <th className="px-3 py-2 text-left font-medium">URL</th>
                    <th className="px-3 py-2 text-left font-medium">Company</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.slice(0, 5).map((entry, index) => (
                    <tr key={index} className="border-t-2 border-border">
                      <td className="max-w-[200px] truncate px-3 py-2 text-text-secondary">
                        {entry.url}
                      </td>
                      <td className="px-3 py-2 text-text-secondary">{entry.company_name ?? "-"}</td>
                    </tr>
                  ))}
                  {preview.length > 5 ? (
                    <tr className="border-t-2 border-border">
                      <td colSpan={2} className="px-3 py-2 text-center text-text-muted">
                        ...and {preview.length - 5} more
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            disabled={!preview || importMutation.isPending}
            loading={importMutation.isPending}
            onClick={() => preview && importMutation.mutate(preview)}
          >
            Import {preview ? `${preview.length} Targets` : ""}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
