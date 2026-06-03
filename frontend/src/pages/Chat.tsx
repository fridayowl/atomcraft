import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'
import { ChatMessage } from '../lib/types'

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hello! I'm AION, your materials science AI assistant. I can help you discover new materials, predict properties, assess synthesis feasibility, and more. What would you like to explore?",
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
          `${i + 1}. **${s.formula}** (${s.name}) — ${s.rationale}\n   Confidence: ${(s.confidence * 100).toFixed(0)}%`
        ).join('\n\n')}`
        setMessages((prev) => [...prev, { role: 'assistant', content: response, timestamp: new Date() }])
      } else {
        const res = await api.chat.query(input)
        setMessages((prev) => [...prev, { role: 'assistant', content: res.response || 'No response generated.', timestamp: new Date() }])
      }
    } catch (e: any) {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Error: ${e.message || 'Failed to connect to AION. Make sure the backend is running.'}`,
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
          <h1 className="text-2xl font-bold gradient-text">AION Chat</h1>
          <p className="text-sm text-gray-400 mt-1">Your conversational materials science AI</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMode('chat')}
            className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${mode === 'chat' ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400'}`}
          >
            Chat
          </button>
          <button
            onClick={() => setMode('suggest')}
            className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${mode === 'suggest' ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400'}`}
          >
            Suggest Materials
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 glass rounded-xl p-6 mb-4 overflow-y-auto scrollbar-thin">
        {messages.map((msg, i) => (
          <div key={i} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} fade-in`}>
            <div className={`max-w-[80%] rounded-xl p-4 ${
              msg.role === 'user'
                ? 'bg-indigo-600/20 border border-indigo-500/20'
                : 'glass-light'
            }`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <p className="text-[10px] text-gray-600 mt-2">
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start fade-in">
            <div className="glass-light rounded-xl p-4">
              <div className="flex gap-2">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      <div className="mb-3">
        <div className="flex gap-2 flex-wrap">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => { setInput(s); setMode('chat') }}
              className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 rounded-lg transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="glass rounded-xl p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder={mode === 'chat' ? 'Ask about materials, properties, synthesis...' : 'Describe the material you need...'}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl text-sm font-semibold transition-all disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
