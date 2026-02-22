import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCasesList } from '@/hooks/useCases'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { CardSkeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/format'
import type { Case } from '@/types'

function ensureArray<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : data.results ?? []
}

export function CasesPage() {
  const [search, setSearch] = useState('')
  const { data, isLoading, error } = useCasesList()
  const casesList = data ? ensureArray(data as Case[] | { results: Case[] }) : []

  const filtered = casesList.filter(
    (c) =>
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      (c.description && c.description.toLowerCase().includes(search.toLowerCase()))
  )

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      open: 'bg-amber-500/20 text-amber-400',
      under_investigation: 'bg-blue-500/20 text-blue-400',
      pending_approval: 'bg-purple-500/20 text-purple-400',
      referred_to_judiciary: 'bg-slate-500/20 text-slate-400',
      closed: 'bg-green-500/20 text-green-400',
    }
    return map[status] ?? 'bg-slate-600/20 text-slate-300'
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-slate-100">Cases</h1>
        <div className="flex gap-2">
          <Input
            placeholder="Search cases..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
          />
        </div>
      </div>

      {error && <p className="text-red-400">Failed to load cases.</p>}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      )}
      {!isLoading && filtered.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">No cases found.</CardContent>
        </Card>
      )}
      {!isLoading && filtered.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <Link key={c.id} to={`/dashboard/cases/${c.id}`}>
              <Card hover className="h-full">
                <CardHeader className="flex flex-row items-start justify-between gap-2">
                  <CardTitle className="text-base truncate">{c.title}</CardTitle>
                  <span className={`shrink-0 rounded px-2 py-0.5 text-xs ${statusBadge(c.status)}`}>
                    {c.status.replace(/_/g, ' ')}
                  </span>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-500 line-clamp-2">{c.description || '—'}</p>
                  <p className="text-xs text-slate-600 mt-2">{formatDate(c.created_at)}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
