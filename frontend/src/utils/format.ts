export function formatDate(value: string): string {
  if (!value) return '—'
  const d = new Date(value)
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n)
}

export function formatCurrencyRials(amount: number): string {
  return new Intl.NumberFormat('fa-IR', {
    style: 'decimal',
    maximumFractionDigits: 0,
  }).format(amount) + ' ریال'
}
