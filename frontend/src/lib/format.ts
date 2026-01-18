export function formatCurrency(value: string | undefined): string {
  if (!value) return '-'
  const num = parseFloat(value)
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
  }).format(num)
}
