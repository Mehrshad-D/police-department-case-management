export interface DashboardModule {
  id: string
  label: string
  path: string
  icon: string
  roles: string[]
  description?: string
}

export const DASHBOARD_MODULES: DashboardModule[] = [
  {
    id: 'cases',
    label: 'Cases',
    path: '/dashboard/cases',
    icon: 'folder',
    roles: ['Detective', 'Sergeant', 'Captain', 'Police Chief', 'Police Officer', 'System Administrator'],
    description: 'Manage and track cases',
  },
  {
    id: 'complaints',
    label: 'Complaints',
    path: '/dashboard/complaints',
    icon: 'file-text',
    roles: ['Intern', 'Police Officer', 'Detective', 'Sergeant', 'Captain', 'Police Chief', 'System Administrator', 'Complainant / Witness'],
    description: 'Review and process complaints',
  },
  {
    id: 'board',
    label: 'Detective Board',
    path: '/dashboard/board',
    icon: 'layout',
    roles: ['Detective', 'Sergeant', 'System Administrator'],
    description: 'Visual evidence board with connections',
  },
  {
    id: 'high-priority',
    label: 'Most Wanted',
    path: '/dashboard/high-priority',
    icon: 'alert-triangle',
    roles: ['Detective', 'Sergeant', 'Captain', 'Police Chief', 'Police Officer', 'System Administrator'],
    description: 'Track most wanted suspects (>30 days under investigation)',
  },
  {
    id: 'reports',
    label: 'Reports',
    path: '/dashboard/reports',
    icon: 'file',
    roles: ['Detective', 'Sergeant', 'Captain', 'Police Chief', 'Judge', 'System Administrator'],
    description: 'Case reports and summaries',
  },
  {
    id: 'documents',
    label: 'Documents & Evidence',
    path: '/dashboard/documents',
    icon: 'archive',
    roles: ['Detective', 'Police Officer', 'Forensic Doctor', 'System Administrator'],
    description: 'Upload and review evidence',
  },
  {
    id: 'tips',
    label: 'Tips & Rewards',
    path: '/dashboard/tips',
    icon: 'message-circle',
    roles: ['Police Officer', 'Detective', 'Sergeant', 'Captain', 'Police Chief', 'System Administrator', 'Complainant / Witness'],
    description: 'Submit tips; officer/detective review; redeem reward codes',
  },
  {
    id: 'trials',
    label: 'Trials',
    path: '/dashboard/trials',
    icon: 'scale',
    roles: ['Judge', 'Captain', 'Police Chief', 'System Administrator'],
    description: 'Trials and verdicts',
  },
  {
    id: 'admin',
    label: 'Admin Panel',
    path: '/dashboard/admin',
    icon: 'settings',
    roles: ['System Administrator'],
    description: 'User and role management',
  },
]

export function getModulesForRoles(roleNames: string[]): DashboardModule[] {
  const set = new Set(roleNames.map((r) => r.toLowerCase()))
  return DASHBOARD_MODULES.filter((m) => m.roles.some((r) => set.has(r.toLowerCase())))
}
