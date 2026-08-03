import type { LayoutItem } from "../store/useLayoutStore";

const GRID_COLS = 12;
export const ROW_HEIGHT = 76;

function footprint(chart: string): { w: number; h: number } {
  if (chart === "kpi") return { w: 3, h: 2 };
  if (chart === "table") return { w: GRID_COLS, h: 6 };
  return { w: 6, h: 3 };
}

function overlaps(a: LayoutItem, b: LayoutItem): boolean {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

export function compactLayout(layout: LayoutItem[], cols: number = GRID_COLS): LayoutItem[] {
  const placed: LayoutItem[] = [];
  const sorted = [...layout].sort((left, right) => left.y - right.y || left.x - right.x);

  sorted.forEach((item) => {
    const width = Math.max(1, Math.min(item.w, cols));
    const height = Math.max(1, item.h);
    let placedItem: LayoutItem | null = null;

    for (let y = 0; y < 200; y += 1) {
      for (let x = 0; x <= cols - width; x += 1) {
        const candidate = { ...item, x, y, w: width, h: height };
        const hasOverlap = placed.some((existing) => overlaps(candidate, existing));
        if (!hasOverlap) {
          placedItem = candidate;
          break;
        }
      }
      if (placedItem) break;
    }

    if (!placedItem) {
      placed.push({ ...item, x: 0, y: 0, w: width, h: height });
    } else {
      placed.push(placedItem);
    }
  });

  return placed;
}

export function generateDefaultLayout(
  widgets: { id: string; chart: string }[],
  cols: number = GRID_COLS
): LayoutItem[] {
  const items: LayoutItem[] = [];
  let x = 0;
  let y = 0;
  let rowHeight = 0;

  widgets.forEach((widget) => {
    const { w, h } = footprint(widget.chart);
    const width = Math.max(1, Math.min(w, cols));

    if (x + width > cols) {
      x = 0;
      y += rowHeight;
      rowHeight = 0;
    }

    items.push({ i: widget.id, x, y, w: width, h });

    x += width;
    rowHeight = Math.max(rowHeight, h);
  });

  return items;
}

export { GRID_COLS };