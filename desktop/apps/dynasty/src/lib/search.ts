export function normalizePlayerSearch(value: unknown): string {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

export function matchesPlayerSearch(parts: readonly unknown[], query: string): boolean {
  if (!query) return true;
  const normalizedQuery = normalizePlayerSearch(query);
  if (!normalizedQuery) return true;
  return normalizePlayerSearch(parts.join(" ")).includes(normalizedQuery);
}
