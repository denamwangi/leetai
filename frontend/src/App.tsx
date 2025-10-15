import './App.css'
import './index.css'
import { useEffect, useState } from 'react'
import { api } from './api'
import type { DailyPlan, OverallStats, TopicStats } from './types'
import { TopicCard } from './components/TopicCard'
import { ProblemCard } from './components/ProblemCard'

function App() {
  const [stats, setStats] = useState<OverallStats | null>(null)
  const [topics, setTopics] = useState<TopicStats[]>([])
  const [plan, setPlan] = useState<DailyPlan | null>(null)
  const [timeMinutes, setTimeMinutes] = useState(60)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    (async () => {
      try {
        setLoading(true)
        const [s, t] = await Promise.all([api.overallStats(), api.topicStats()])
        setStats(s)
        setTopics(t)
      } catch (e: any) {
        setError(e.message || 'Failed to load')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const handleSync = async () => {
    try {
      setLoading(true)
      setError(null)
      await api.sync(20, false)
      const [s, t] = await Promise.all([api.overallStats(), api.topicStats()])
      setStats(s)
      setTopics(t)
    } catch (e: any) {
      setError(e.message || 'Sync failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGeneratePlan = async () => {
    try {
      setLoading(true)
      setError(null)
      const p = await api.dailyPlan({ time_minutes: timeMinutes })
      setPlan(p)
    } catch (e: any) {
      setError(e.message || 'Plan failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">LeetCode Assistant</h1>
          <button 
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              backgroundColor: loading ? '#9ca3af' : '#2563eb',
              color: 'white',
              fontWeight: '500',
              border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
            onClick={handleSync} 
            disabled={loading}
          >
            {loading ? 'Syncing...' : 'Sync'}
          </button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-8">
        {error && <div className="p-3 bg-red-100 text-red-700 rounded">{error}</div>}

        <section>
          <h2 className="text-base font-semibold mb-3">Overall Progress</h2>
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat label="Solved" value={stats.total_problems_solved} />
              <Stat label="Avg Attempts" value={stats.average_attempts_per_problem} />
              <Stat label="Current Streak" value={stats.current_streak_days} />
              <Stat label="Longest Streak" value={stats.longest_streak_days} />
            </div>
          )}
        </section>

        <section>
          <h2 className="text-base font-semibold mb-3">Topics</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {topics.map(t => (
              <TopicCard key={t.topic} {...t} />
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-base font-semibold mb-3">Daily Plan</h2>
          <div className="flex items-center gap-2 mb-3">
            <input 
              type="number" 
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
              value={timeMinutes} 
              onChange={e => setTimeMinutes(parseInt(e.target.value || '0'))} 
              min="15"
              max="480"
              placeholder="60"
            />
            <button 
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                backgroundColor: loading ? '#9ca3af' : '#16a34a',
                color: 'white',
                fontWeight: '500',
                border: 'none',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1
              }}
              onClick={handleGeneratePlan} 
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Generate Plan'}
            </button>
          </div>
          {plan && (
            <div className="space-y-3">
              <div className="text-sm text-gray-700">Focus: <span className="font-medium">{plan.focus_topic}</span> {plan.is_cached && <span className="ml-2 text-xs text-gray-500">(cached)</span>}</div>
              <div className="grid md:grid-cols-2 gap-3">
                {plan.recommendations.map(r => (
                  <ProblemCard key={r.leetcode_number + r.title} {...r} />
                ))}
              </div>
              <div className="text-sm text-gray-600 whitespace-pre-wrap">{plan.ai_rationale}</div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border bg-white p-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  )
}

export default App
