import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/Button'

export function Header() {
  const { user, logout, hasRole } = useAuthStore()
  const navigate = useNavigate()
  const isAdmin = user && hasRole('System Administrator')

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-slate-700/50 bg-slate-900/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link to="/" className="text-lg font-semibold text-slate-100">
          Police Case Management
        </Link>
        <nav className="flex items-center gap-4">
          {user ? (
            <>
              <Link
                to="/dashboard"
                className="text-sm text-slate-300 hover:text-white transition-colors"
              >
                Dashboard
              </Link>
              {isAdmin && (
                <Link
                  to="/dashboard/admin"
                  className="text-sm text-amber-400 hover:text-amber-300 transition-colors font-medium"
                >
                  Admin Panel
                </Link>
              )}
              <span className="text-sm text-slate-500 hidden sm:inline">
                {user.full_name || user.username}
              </span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost" size="sm">
                  Login
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" size="sm">
                  Register
                </Button>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
