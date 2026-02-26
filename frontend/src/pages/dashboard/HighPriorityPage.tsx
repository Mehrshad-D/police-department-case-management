import { useState } from 'react'
import { useSuspectsHighPriority } from '@/hooks/useSuspects'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { CardSkeleton } from '@/components/ui/Skeleton'
import { formatDate, formatCurrencyRials } from '@/utils/format'
import type { Suspect } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data as { results: T[] }).results ?? []
}

export function HighPriorityPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading, error } = useSuspectsHighPriority()
  const list = data ? ensureArray(data as Suspect[] | { results: Suspect[] }) : []
  const filtered = list.filter(
    (s) =>
      s.user_username?.toLowerCase().includes(search.toLowerCase()) ||
      s.case_title?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-100">Most Wanted (Dashboard)</h1>
        <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
      </div>
      <p className="text-slate-400">Approved suspects. Score = crime degree (1–4) × days. Sorted by score DESC. Reward = score × 20,000,000 Rials.</p>
      {error && <p className="text-red-400">Failed to load suspects.</p>}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (<CardSkeleton key={i} />))}
        </div>
      )}
      {!isLoading && filtered.length === 0 && (
        <Card><CardContent className="py-12 text-center text-slate-500">No most wanted suspects.</CardContent></Card>
      )}
      {!isLoading && filtered.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((s) => (
            <Card key={s.id} className="h-full">
              <CardHeader className="flex flex-row items-start justify-between gap-2">
                <CardTitle className="text-base">{s.user_username}</CardTitle>
                <span className="rounded bg-amber-500/20 text-amber-400 px-2 py-0.5 text-xs">Most wanted</span>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-sm text-slate-500">Case: {s.case_title}</p>
                <p className="text-sm text-slate-400">Days pursued: {s.days_pursued ?? 0}</p>
                {s.reward_rials != null && (
                  <p className="text-sm text-primary-400">Reward: {formatCurrencyRials(s.reward_rials)}</p>
                )}
                <p className="text-xs text-slate-600">{formatDate(s.first_pursuit_date)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
