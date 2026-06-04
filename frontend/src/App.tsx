import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider, useAuth } from './lib/auth'
import { Sidebar } from './components/Sidebar'
import { Home } from './pages/Home'
import { Materials } from './pages/Materials'
import { Generator } from './pages/Generator'
import { Experiments } from './pages/Experiments'
import { Predictor } from './pages/Predictor'
import { Chat } from './pages/Chat'
import { Discover } from './pages/Discover'
import { Atom } from 'lucide-react'

function AppLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-white">
        <Atom className="w-12 h-12 text-blue-500 mb-4 animate-pulse" />
        <h1 className="text-2xl font-semibold text-gray-900 mb-1">Atomcraft</h1>
        <p className="text-sm text-gray-400">Materials Discovery Platform</p>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto scrollbar-thin">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/materials" element={<Materials />} />
          <Route path="/generator" element={<Generator />} />
          <Route path="/predict" element={<Predictor />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/discover" element={<Discover />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  )
}
