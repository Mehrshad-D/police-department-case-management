import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { RootLayout } from '@/components/layout/RootLayout'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { DashboardOverviewPage } from '@/pages/dashboard/DashboardOverviewPage'
import { CasesPage } from '@/pages/dashboard/CasesPage'
import { CaseDetailPage } from '@/pages/dashboard/CaseDetailPage'
import { ComplaintsPage } from '@/pages/dashboard/ComplaintsPage'
import { ComplaintDetailPage } from '@/pages/dashboard/ComplaintDetailPage'
import { DetectiveBoardPage } from '@/pages/dashboard/DetectiveBoardPage'
import { HighPriorityPage } from '@/pages/dashboard/HighPriorityPage'
import { ReportsPage } from '@/pages/dashboard/ReportsPage'
import { DocumentsPage } from '@/pages/dashboard/DocumentsPage'
import { AdminPage } from '@/pages/dashboard/AdminPage'
import { TipsPage } from '@/pages/tips/TipsPage'

import { RewardClaimPage } from '@/pages/rewards/RewardClaimPage'

function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const user = useAuthStore((s) => s.user)
  if (!user) return <Navigate to="/login" replace />
  if (roles?.length) {
    const roleNames = user.role_names ?? []
    const hasRole = roles.some((r) => roleNames.some((n) => n.toLowerCase() === r.toLowerCase()))
    if (!hasRole) return <Navigate to="/dashboard" replace />
  }
  return <>{children}</>
}

const dashboardElement = (
  <ErrorBoundary>
    <ProtectedRoute>
      <DashboardLayout />
    </ProtectedRoute>
  </ErrorBoundary>
)

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      {
        path: '/dashboard',
        element: dashboardElement,
        children: [
      { path: 'tips', element: <TipsPage /> },
      { path: 'rewards/claim', element: <RewardClaimPage /> },
      { index: true, element: <DashboardOverviewPage /> },
      { path: 'cases', element: <CasesPage /> },
      { path: 'cases/:id', element: <CaseDetailPage /> },
      { path: 'complaints', element: <ComplaintsPage /> },
      { path: 'complaints/:id', element: <ComplaintDetailPage /> },
      { path: 'board', element: <DetectiveBoardPage /> },
      { path: 'high-priority', element: <HighPriorityPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'reports/:id', element: <ReportsPage /> },
      { path: 'documents', element: <DocumentsPage /> },
      {
        path: 'trials',
        element: (
          <div className="space-y-6">
            <h1 className="text-2xl font-bold text-slate-100">Trials</h1>
            <p className="text-slate-400">Trials and verdicts — use API docs for endpoints.</p>
          </div>
        ),
      },
      { path: 'admin', element: <ProtectedRoute roles={['System Administrator']}><AdminPage /></ProtectedRoute> },
    ],
  },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
