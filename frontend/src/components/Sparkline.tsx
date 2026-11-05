import type { SeriesPoint } from '../types';

export interface WeekBar {
  x: number;
  y: number;
  width: number;
  height: number;
  value: number;
  current: boolean;
  weekStart: string;
}

export interface WeekChartGeometry {
  bars: WeekBar[];
  band: { y: number; height: number } | null;
  plotHeight: number;
  hasHistory: boolean;
}

const MAX_BAR_WIDTH = 14;
const MIN_BAR_WIDTH = 3;
const GAP_RATIO = 0.32;
const PADDING_RATIO = 0.12;

/**
 * One bar per week plus a shaded strip for the account's usual range.
 *
 * Bars, not a line: a support agent reading this for the first time should see
 * "eight weeks, one of them is different" without knowing what a sparkline is.
 * The scale always includes the usual range, so the band never lies off-chart.
 */
export function buildWeekChartGeometry(
  series: SeriesPoint[],
  low: number | null,
  high: number | null,
  width: number,
  height: number,
): WeekChartGeometry {
  const hasBand = low !== null && high !== null && Number.isFinite(low) && Number.isFinite(high);
  const values = series.map((point) => point.value).filter((value) => Number.isFinite(value));
  const domainValues = hasBand ? [...values, low as number, high as number] : values;

  if (domainValues.length === 0) {
    return { bars: [], band: null, plotHeight: height, hasHistory: false };
  }

  let min = Math.min(0, ...domainValues);
  let max = Math.max(...domainValues);
  if (max === min) {
    max = min + Math.max(1, Math.abs(max) * 0.1);
  }
  // Padding only at the top: the bottom is a real zero.
  const top = max + (max - min) * PADDING_RATIO;
  const scaleY = (value: number): number => {
    const ratio = (value - min) / (top - min || 1);
    return Math.min(height, Math.max(0, height - ratio * height));
  };

  const count = series.length;
  const slot = count > 0 ? width / count : width;
  const barWidth = Math.min(MAX_BAR_WIDTH, Math.max(MIN_BAR_WIDTH, slot * (1 - GAP_RATIO)));

  const bars: WeekBar[] = series.map((point, index) => {
    const centre = slot * index + slot / 2;
    const top = scaleY(point.value);
    // A tiny value still needs a visible sliver, but the bar must never overflow.
    const rawHeight = point.value > 0 ? Math.max(1.5, height - top) : 0;
    const barHeight = Math.min(height, rawHeight);
    return {
      x: centre - barWidth / 2,
      y: height - barHeight,
      width: barWidth,
      height: barHeight,
      value: point.value,
      current: point.current,
      weekStart: point.week_start,
    };
  });

  const band = hasBand
    ? {
        y: scaleY(high as number),
        height: Math.max(1, scaleY(low as number) - scaleY(high as number)),
      }
    : null;

  return { bars, band, plotHeight: height, hasHistory: true };
}

interface SparklineProps {
  series: SeriesPoint[];
  low: number | null;
  high: number | null;
  percent?: boolean;
  width?: number;
  height?: number;
  label: string;
}

function summarise(
  series: SeriesPoint[],
  low: number | null,
  high: number | null,
  percent: boolean,
): string {
  const format = (value: number) =>
    percent ? `${value.toFixed(1)}%` : new Intl.NumberFormat('en-US').format(value);
  const history = series.filter((point) => !point.current);
  const values = history.map((point) => format(point.value)).join(', ');
  const current = series.find((point) => point.current);
  const band =
    low !== null && high !== null
      ? ` Usual range ${format(low)} to ${format(high)}.`
      : ' No usual range yet.';
  return `${history.length} earlier weeks: ${values}.${
    current ? ` This period: ${format(current.value)}.` : ''
  }${band}`;
}

export function Sparkline({
  series,
  low,
  high,
  percent = false,
  width = 200,
  height = 46,
  label,
}: SparklineProps) {
  const geometry = buildWeekChartGeometry(series, low, high, width, height);
  const historyCount = series.filter((point) => !point.current).length;

  if (!geometry.hasHistory) {
    return <div className="weekchart weekchart--empty" aria-label={`${label}: no history yet`} />;
  }

  return (
    <figure className="weekchart">
      <svg
        className="weekchart__plot"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${label}. ${summarise(series, low, high, percent)}`}
        preserveAspectRatio="none"
      >
        {geometry.band ? (
          <rect
            className="weekchart__band"
            x={0}
            y={geometry.band.y}
            width={width}
            height={geometry.band.height}
          />
        ) : null}
        {geometry.bars.map((bar) => (
          <rect
            key={bar.weekStart}
            className={bar.current ? 'weekchart__bar weekchart__bar--current' : 'weekchart__bar'}
            x={bar.x}
            y={bar.y}
            width={bar.width}
            height={bar.height}
            rx={Math.min(2, bar.width / 2)}
          />
        ))}
      </svg>
      <figcaption className="weekchart__caption">
        <span>{historyCount > 0 ? `${historyCount} weeks ago` : 'start'}</span>
        {geometry.band ? (
          <span className="weekchart__key">
            <i className="weekchart__key-band" aria-hidden="true" />
            usual range
          </span>
        ) : (
          <span />
        )}
        <span>now</span>
      </figcaption>
    </figure>
  );
}
