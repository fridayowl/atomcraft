import { NavLink } from 'react-router-dom'
import { cn } from '../lib/utils'
import {
  LayoutDashboard,
  Database,
  Sparkles,
  Beaker,
  LineChart,
  FlaskConical,
  MessageSquare,
  Atom,
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/materials', label: 'Materials', icon: Database },
  { path: '/generator', label: 'Generator', icon: Sparkles },
  { path: '/discover', label: 'Discover', icon: Beaker },
  { path: '/predict', label: 'Predict', icon: LineChart },
  { path: '/experiments', label: 'Experiments', icon: FlaskConical },
  { path: '/chat', label: 'Chat', icon: MessageSquare },
]

export function Sidebar() {
  return (
    <aside className="w-56 bg-white border-r border-gray-100 flex flex-col h-full shrink-0">
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
            <Atom className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-gray-900">Atomcraft</h1>
            <p className="text-[11px] text-gray-400">Materials Discovery</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              )
            }
          >
            <item.icon className="w-4 h-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <span>All systems operational</span>
        </div>
        <p className="text-[11px] text-gray-300 mt-1">v0.1.0</p>
      </div>
    </aside>
  )
}
