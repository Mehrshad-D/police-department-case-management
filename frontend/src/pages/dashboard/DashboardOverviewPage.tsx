import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/store/authStore'
import { getModulesForRoles } from '@/config/dashboardModules'
import { useStatistics } from '@/hooks/useStatistics'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatNumber } from '@/utils/format'

const icons: Record<string, string> = {
  folder: '📁',
  'file-text': '📋',
  layout: '🗂️',
  'alert-triangle': '⚠️',
  file: '📄',
  archive: '📦',
  scale: '⚖️',
  settings: '⚙️',
}

export function DashboardOverviewPage() {
  const roleNames = useAuthStore((s) => s.roleNames())
  const modules = getModulesForRoles(roleNames)
  const { data: stats, isLoading } = useStatistics()

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-slate-400 mt-1">Overview and quick access to modules</p>
      </div>

      {stats && (
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Cases</CardTitle></CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-primary-400">{formatNumber(stats.cases_total)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Complaints</CardTitle></CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-primary-400">{formatNumber(stats.complaints_total)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">Evidence</CardTitle></CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-primary-400">{formatNumber(stats.evidence_total)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-slate-400 text-sm">High-priority suspects</CardTitle></CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-primary-400">{formatNumber(stats.suspects_high_priority)}</p>
            </CardContent>
          </Card>
        </motion.section>
      )}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}><CardHeader><Skeleton className="h-4 w-20" /></CardHeader><CardContent><Skeleton className="h-8 w-12" /></CardContent></Card>
          ))}
        </div>
      )}

      <section>
        <h2 className="text-lg font-semibold text-slate-100 mb-4">Modules</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {modules.map((m, i) => (
            <Link key={m.id} to={m.path}>
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card hover className="h-full">
                  <CardContent className="flex items-center gap-4">
                    <span className="text-2xl">{icons[m.icon] ?? '•'}</span>
                    <div>
                      <p className="font-medium text-slate-100">{m.label}</p>
                      {m.description && <p className="text-sm text-slate-500">{m.description}</p>}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
