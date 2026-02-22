import { NavLink } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { getModulesForRoles } from '@/config/dashboardModules'
import { cn } from '@/utils/cn'

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

export function Sidebar() {
  const roleNames = useAuthStore((s) => s.roleNames())
  const modules = getModulesForRoles(roleNames)

  return (
    <aside className="w-56 shrink-0 border-r border-slate-700/50 bg-slate-900/50 p-4">
      <nav className="space-y-1">
        <NavLink
          to="/dashboard"
          end
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive ? 'bg-primary-600/20 text-primary-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
            )
          }
        >
          <span>🏠</span>
          Overview
        </NavLink>
        {modules.map((m) => (
          <NavLink
            key={m.id}
            to={m.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive ? 'bg-primary-600/20 text-primary-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              )
            }
          >
            <span>{icons[m.icon] ?? '•'}</span>
            {m.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
