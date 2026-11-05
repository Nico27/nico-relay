import type { MetricStatus } from '../types';
import { statusGlyph, statusLabel, statusTone } from '../format';

interface StatusChipProps {
  status: MetricStatus;
  compact?: boolean;
}

/** Always text + glyph: status is never conveyed by colour alone. */
export function StatusChip({ status, compact = false }: StatusChipProps) {
  const label = statusLabel(status);
  return (
    <span
      className={`chip chip--${statusTone(status)}${compact ? ' chip--compact' : ''}`}
      aria-label={`Status: ${label}`}
    >
      <span className="chip__glyph" aria-hidden="true">
        {statusGlyph(status)}
      </span>
      <span className="chip__label">{label}</span>
    </span>
  );
}
