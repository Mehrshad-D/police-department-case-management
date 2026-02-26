import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useStatistics } from '@/hooks/useStatistics'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatNumber } from '@/utils/format'

export function HomePage() {
  const { data: stats, isLoading, error } = useStatistics()

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <section className="relative overflow-hidden border-b border-slate-800">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 to-transparent" />
        <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl font-bold tracking-tight sm:text-5xl"
          >
            Police Department
            <span className="block text-primary-400">Case Management System</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-4 max-w-2xl text-lg text-slate-400"
          >
            Digitized operations for case tracking, evidence management, suspect investigation,
            and judiciary workflow — all in one secure platform.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mt-8 flex flex-wrap gap-4"
          >
            <Link to="/login">
              <Button size="lg">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button variant="secondary" size="lg">
                Register
              </Button>
            </Link>
            <Link to="/most-wanted">
              <Button variant="outline" size="lg">
                Most Wanted
              </Button>
            </Link>
            <Link to="/submit-tip">
              <Button variant="outline" size="lg">
                Submit a tip
              </Button>
            </Link>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
        <h2 className="text-2xl font-semibold text-slate-100 mb-8">System statistics</h2>
        {error && (
          <p className="text-red-400">Failed to load statistics. Ensure the API is running.</p>
        )}
        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-5 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}
        {stats && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
          >
            <Card hover>
              <CardHeader>
                <CardTitle className="text-slate-400 text-sm font-medium">Total cases</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-primary-400">{formatNumber(stats.cases_total)}</p>
                <p className="text-sm text-slate-500 mt-1">{stats.cases_open} open</p>
              </CardContent>
            </Card>
            <Card hover>
              <CardHeader>
                <CardTitle className="text-slate-400 text-sm font-medium">Complaints</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-primary-400">{formatNumber(stats.complaints_total)}</p>
                <p className="text-sm text-slate-500 mt-1">{stats.complaints_pending} pending</p>
              </CardContent>
            </Card>
            <Card hover>
              <CardHeader>
                <CardTitle className="text-slate-400 text-sm font-medium">Evidence items</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-primary-400">{formatNumber(stats.evidence_total)}</p>
              </CardContent>
            </Card>
            <Card hover>
              <CardHeader>
                <CardTitle className="text-slate-400 text-sm font-medium">High-priority suspects</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-primary-400">{formatNumber(stats.suspects_high_priority)}</p>
                <p className="text-sm text-slate-500 mt-1">{stats.suspects_total} total suspects</p>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </section>
    </div>
  )
}
