export type TableSortDirection = "ascending" | "descending";
export type TableSortKind = "number" | "text";

function isMissing(value: unknown, kind: TableSortKind): boolean {
  if (value === null || value === undefined || value === "") return true;
  return kind === "number" && (typeof value !== "number" || !Number.isFinite(value));
}

const ownerCollator = new Intl.Collator("en-US", {
  numeric: true,
  sensitivity: "base",
});

export function stableSortRows<T>(
  rows: readonly T[],
  valueFor: (row: T) => unknown,
  kind: TableSortKind,
  direction: TableSortDirection,
): T[] {
  return rows
    .map((row, index) => ({ index, row, value: valueFor(row) }))
    .sort((left, right) => {
      const leftMissing = isMissing(left.value, kind);
      const rightMissing = isMissing(right.value, kind);
      if (leftMissing || rightMissing) {
        if (leftMissing && rightMissing) return left.index - right.index;
        return leftMissing ? 1 : -1;
      }

      let comparison: number;
      if (kind === "number") {
        comparison = (left.value as number) - (right.value as number);
      } else {
        comparison = ownerCollator.compare(String(left.value), String(right.value));
      }
      if (comparison === 0) return left.index - right.index;
      return direction === "ascending" ? comparison : -comparison;
    })
    .map(({ row }) => row);
}
