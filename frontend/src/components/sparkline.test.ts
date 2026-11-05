import type { SeriesPoint } from '../types';
import { buildWeekChartGeometry } from './Sparkline';

const W = 200;
const H = 46;

function series(...values: number[]): SeriesPoint[] {
  return values.map((value, index) => ({
    week_start: `2026-0${index + 1}-01`,
    value,
    current: index === values.length - 1,
  }));
}

describe('buildWeekChartGeometry', () => {
  it('returns nothing to draw for an empty series', () => {
    const geometry = buildWeekChartGeometry([], null, null, W, H);
    expect(geometry.bars).toEqual([]);
    expect(geometry.band).toBeNull();
    expect(geometry.hasHistory).toBe(false);
  });

  it('draws one bar per week, spread across the width', () => {
    const geometry = buildWeekChartGeometry(series(10, 20, 30), null, null, W, H);
    expect(geometry.bars).toHaveLength(3);
    const xs = geometry.bars.map((bar) => bar.x);
    expect(xs).toEqual([...xs].sort((a, b) => a - b));
    expect(xs[0]).toBeGreaterThanOrEqual(0);
    const last = geometry.bars[2]!;
    expect(last.x + last.width).toBeLessThanOrEqual(W + 0.001);
  });

  it('keeps the tallest value tallest and anchors bars at the bottom', () => {
    const geometry = buildWeekChartGeometry(series(10, 800, 40), null, null, W, H);
    const [small, tall, mid] = geometry.bars;
    expect(tall!.height).toBeGreaterThan(mid!.height);
    expect(mid!.height).toBeGreaterThan(small!.height);
    for (const bar of geometry.bars) {
      expect(bar.y + bar.height).toBeCloseTo(H, 5);
    }
  });

  it('keeps the usual-range band inside the plot', () => {
    const geometry = buildWeekChartGeometry(series(120, 300), 10, 90, W, H);
    expect(geometry.band).not.toBeNull();
    expect(geometry.band!.y).toBeGreaterThanOrEqual(0);
    expect(geometry.band!.height).toBeGreaterThan(0);
    expect(geometry.band!.y + geometry.band!.height).toBeLessThanOrEqual(H + 0.001);
  });

  it('gives a zero week no visible bar but keeps the slot', () => {
    const geometry = buildWeekChartGeometry(series(0, 5), null, null, W, H);
    expect(geometry.bars[0]!.height).toBe(0);
    expect(geometry.bars).toHaveLength(2);
  });

  it('survives a single flat week', () => {
    const geometry = buildWeekChartGeometry(series(7), null, null, W, H);
    expect(geometry.bars).toHaveLength(1);
    expect(geometry.bars[0]!.height).toBeGreaterThan(0);
  });

  it('marks only the last bar as current', () => {
    const geometry = buildWeekChartGeometry(series(1, 2, 3), 1, 3, W, H);
    expect(geometry.bars.filter((bar) => bar.current)).toHaveLength(1);
    expect(geometry.bars.at(-1)?.current).toBe(true);
  });
});
