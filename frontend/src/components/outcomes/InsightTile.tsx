import { Surface } from "../system/Surface";

export function InsightTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <Surface tone="subtle" padding="md" radius="xl" className="h-full">
      <div className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-2 text-2xl font-black tracking-[-0.05em] text-text-primary">{value}</div>
      <p className="mt-2 text-sm leading-6 text-text-secondary">{hint}</p>
    </Surface>
  );
}
