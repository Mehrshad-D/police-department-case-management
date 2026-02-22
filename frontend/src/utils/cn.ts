export function cn(
  ...classes: (string | undefined | null | false | Record<string, boolean>)[]
): string {
  return classes
    .flatMap((c) => (typeof c === 'object' && c !== null ? Object.entries(c).filter(([, v]) => v).map(([k]) => k) : c))
    .filter(Boolean)
    .join(' ')
}
