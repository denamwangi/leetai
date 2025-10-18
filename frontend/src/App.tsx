import './App.css'
import './index.css'
import { useEffect, useState } from 'react'
import { api } from './api'
import type { DailyPlan, OverallStats, TopicStats } from './types'
import { Sidebar } from './components/Sidebar'
import { TopicBreakdown } from './components/TopicBreakdown'
import { DailyPlan as DailyPlanComponent } from './components/DailyPlan'

type ContentType = 'welcome' | 'topicBreakdown' | 'dailyPlan'

function App() {
  const [stats, setStats] = useState<OverallStats | null>(null)
  const [topics, setTopics] = useState<TopicStats[]>([])
  const [plan, setPlan] = useState<DailyPlan | null>(null)
  const [timeMinutes, setTimeMinutes] = useState(60)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [info, setInfo] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeContent, setActiveContent] = useState<ContentType>('welcome')

  useEffect(() => {
    (async () => {
      try {
        setLoading(true)
        setError(null)
        setInfo(null)
        const [s, t] = await Promise.all([api.overallStats(), api.topicStats()])
        setStats(s)
        setTopics(t)
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load data. Make sure the backend is running on port 8000.')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const handleSync = async () => {
    try {
      setLoading(true)
      setError(null)
      setInfo(null)
      const syncResult = await api.sync(20, false)
      const [s, t] = await Promise.all([api.overallStats(), api.topicStats()])
      setStats(s)
      setTopics(t)
      
      // Show info message for successful sync
      if (syncResult.message) {
        setInfo(syncResult.message)
        // Auto-clear info message after 5 seconds
        setTimeout(() => setInfo(null), 5000)
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Sync failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGeneratePlan = async () => {
    try {
      setLoading(true)
      setError(null)
      setInfo(null)
      const p = await api.dailyPlan({ time_minutes: timeMinutes })
      setPlan(p)
      setActiveContent('dailyPlan')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Plan failed')
    } finally {
      setLoading(false)
    }
  }

  const handleShowTopicBreakdown = () => {
    setActiveContent('topicBreakdown')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold">LeetCode Assistant</h1>
          </div>
          <button 
            className="px-4 py-2 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" 
            onClick={handleSync} 
            disabled={loading}
          >
            {loading ? 'Syncing...' : 'Sync'}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden relative">
        {/* Mobile Overlay */}
        {sidebarOpen && (
          <div 
            className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <div className={`
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
          fixed lg:relative
          top-0 left-0
          z-50 lg:z-auto
          transition-transform duration-300 ease-in-out
          lg:transition-none
        `}>
          <Sidebar
            stats={stats}
            topics={topics}
            plan={plan}
            timeMinutes={timeMinutes}
            setTimeMinutes={setTimeMinutes}
            onGeneratePlan={handleGeneratePlan}
            onShowTopicBreakdown={handleShowTopicBreakdown}
            loading={loading}
            onClose={() => setSidebarOpen(false)}
          />
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {error && <div className="p-3 bg-red-100 text-red-700 rounded mb-4">{error}</div>}
            {info && <div className="p-3 bg-blue-100 text-blue-700 rounded mb-4">{info}</div>}
            
            {activeContent === 'welcome' && (
              <div className="text-center text-gray-500 mt-20">
                <h2 className="text-xl font-semibold mb-2">Welcome to LeetCode Assistant</h2>
                <p>Use the sidebar to view your progress and generate daily study plans.</p>
              </div>
            )}

            {activeContent === 'topicBreakdown' && (
              <TopicBreakdown topics={topics} />
            )}

            {activeContent === 'dailyPlan' && plan && (
              <DailyPlanComponent plan={plan} />
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
