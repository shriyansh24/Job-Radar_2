import Badge from '../ui/Badge';

interface FreshnessBadgeProps {
  score: number | null;
}

function getFreshnessInfo(score: number): { label: string; variant: 'success' | 'warning' | 'danger' | 'info' | 'default' } {
  if (score >= 0.9) return { label: 'Just posted', variant: 'success' };
  if (score >= 0.7) return { label: 'Fresh', variant: 'success' };
  if (score >= 0.5) return { label: 'Recent', variant: 'warning' };
  if (score >= 0.3) return { label: 'Getting stale', variant: 'warning' };
  return { label: 'Old posting', variant: 'danger' };
}

export default function FreshnessBadge({ score }: FreshnessBadgeProps) {
  if (score === null || score === undefined) return null;

  const { label, variant } = getFreshnessInfo(score);

  return (
    <Badge variant={variant} size="sm">
      {label}
    </Badge>
  );
}
