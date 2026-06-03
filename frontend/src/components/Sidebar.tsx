import { NavLink } from 'react-router-dom'
import { cn } from '../lib/utils'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '◈' },
  { path: '/materials', label: 'Materials', icon: '⬡' },
  { path: '/generator', label: 'Generator', icon: '✦' },
  { path: '/predict', label: 'Predict', icon: '▦' },
  { path: '/experiments', label: 'Experiments', icon: '⚗' },
  { path: '/chat', label: 'AION Chat', icon: '✦' },
]

export function Sidebar() {
  return (
    <aside className="w-64 glass border-r border-gray-800 flex flex-col h-full shrink-0">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-lg font-bold">
            A
          </div>
          <div>
            <h1 className="text-lg font-semibold gradient-text">AION</h1>
            <p className="text-xs text-gray-500">Materials Discovery</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              )
            }
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="glass-light rounded-lg p-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span>All systems operational</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">v0.1.0</p>
        </div>
      </div>
    </aside>
  )
}
