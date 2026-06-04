import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import { ChatMessage } from '../lib/types'
import { MessageSquare, Lightbulb, Send, Bot, User } from 'lucide-react'

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hello! I'm Atomcraft, your materials science AI assistant. I can help you discover new materials, predict properties, assess synthesis feasibility, and more. What would you like to explore?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'chat' | 'suggest'>('chat')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    if (!input.trim() || loading) return

    const userMsg: ChatMessage = { role: 'user', content: input, timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      if (mode === 'suggest') {
        const res = await api.chat.suggest({ description: input, num_suggestions: 5 })
        const suggestions = res.suggestions || []
        const response = `Based on your requirements, here are some material suggestions:\n\n${suggestions.map((s: any, i: number) =>
          `${i + 1}. ${s.formula} (${s.name}) — ${s.rationale}\n   Confidence: ${(s.confidence * 100).toFixed(0)}%`
        ).join('\n\n')}`
        setMessages((prev) => [...prev, { role: 'assistant', content: response, timestamp: new Date() }])
      } else {
        const res = await api.chat.query(input)
        setMessages((prev) => [...prev, { role: 'assistant', content: res.response || 'No response generated.', timestamp: new Date() }])
      }
    } catch (e: any) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Error: ${e.message || 'Failed to connect. Make sure the backend is running.'}`,
        timestamp: new Date(),
      }])
    } finally {
      setLoading(false)
    }
  }

  const suggestions = [
    'Design a high-k dielectric material',
    'What cathode materials have high ionic conductivity?',
    'Predict properties of LiFePO4',
    'Check synthesis feasibility of Na3Zr2Si2PO12',
    'Design an experiment for solid-state synthesis',
  ]

  return (
    <div className="p-8 max-w-5xl mx-auto flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Chat</h1>
          <p className="text-sm text-gray-400 mt-1">Your conversational materials science AI</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMode('chat')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${mode === 'chat' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
          >
            Chat
          </button>
          <button
            onClick={() => setMode('suggest')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${mode === 'suggest' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`}
          >
            Suggest Materials
          </button>
        </div>
      </div>

      <div className="flex-1 bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-4 overflow-y-auto scrollbar-thin">
        {messages.map((msg, i) => (
          <div key={i} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} fade-in`}>
            <div className={`flex gap-3 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                msg.role === 'user' ? 'bg-blue-500' : 'bg-gray-100'
              }`}>
                {msg.role === 'user' ? (
                  <User className="w-4 h-4 text-white" />
                ) : (
                  <Bot className="w-4 h-4 text-blue-500" />
                )}
              </div>
              <div className={`rounded-xl p-4 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-50 text-gray-700'
              }`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className={`text-[10px] mt-2 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start fade-in">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                <Bot className="w-4 h-4 text-blue-500" />
              </div>
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mb-3 flex gap-2 flex-wrap">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => { setInput(s); setMode('chat') }}
            className="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-500 rounded-lg transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder={mode === 'chat' ? 'Ask about materials, properties, synthesis...' : 'Describe the material you need...'}
            className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl text-sm font-semibold transition-all disabled:opacity-50 flex items-center gap-2"
          >
            <Send className="w-4 h-4" /> Send
          </button>
        </div>
      </div>
    </div>
  )
}
