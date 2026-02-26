import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { mostWantedApi } from '@/api/endpoints'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate, formatCurrencyRials } from '@/utils/format'
import type { MostWantedItem } from '@/types'

function AvatarPlaceholder({ name }: { name: string }) {
  const initial = (name || '?').charAt(0).toUpperCase()
  return (
    <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full bg-slate-700 text-2xl font-bold text-slate-300">
      {initial}
    </div>
  )
}

export function MostWantedPage() {
  const { data: list, isLoading, error } = useQuery({
    queryKey: ['most-wanted'],
    queryFn: () => mostWantedApi.list(),
  })
  const items = Array.isArray(list) ? list : []

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/50">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-slate-100">Most Wanted</h1>
          <Link to="/">
            <Button variant="ghost" size="sm">Home</Button>
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <p className="text-slate-400 mb-6">
          Individuals under investigation for more than 30 days. Ranking by score (days × crime degree). Reward = score × 20,000,000 Rials.
        </p>
        {error && <p className="text-red-400">Failed to load list.</p>}
        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        )}
        {!isLoading && items.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-slate-500">
              No most wanted suspects at this time.
            </CardContent>
          </Card>
        )}
        {!isLoading && items.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((s: MostWantedItem, index: number) => (
              <Card key={s.id} className="overflow-hidden">
                <CardHeader className="flex flex-row items-start gap-4">
                  {s.photo ? (
                    <img src={s.photo} alt="" className="h-24 w-24 rounded-full object-cover" />
                  ) : (
                    <AvatarPlaceholder name={s.user_full_name || s.user_username} />
                  )}
                  <div className="min-w-0 flex-1">
                    <CardTitle className="text-lg">
                      #{index + 1} {s.user_full_name || s.user_username}
                    </CardTitle>
                    <p className="text-sm text-slate-500 mt-0.5">Case: {s.case_title}</p>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 border-t border-slate-700 pt-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Days under investigation</span>
                    <span className="text-slate-200">{s.days_under_investigation}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Crime degree (1–4)</span>
                    <span className="text-slate-200">{s.crime_degree}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-500">Score</span>
                    <span className="text-slate-200">{s.ranking_score}</span>
                  </div>
                  <div className="flex justify-between text-sm font-medium text-primary-400">
                    <span>Reward</span>
                    <span>{formatCurrencyRials(s.reward_rials)}</span>
                  </div>
                  <p className="text-xs text-slate-600">{formatDate(s.marked_at)}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
