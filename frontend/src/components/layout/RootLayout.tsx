import { Outlet } from 'react-router-dom'
import { Header } from './Header'

export function RootLayout() {
  return (
    <div className="min-h-screen bg-slate-950">
      <Header />
      <Outlet />
    </div>
  )
}
