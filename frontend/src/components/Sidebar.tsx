import { useState } from 'react'
import type { DailyPlan, OverallStats, TopicStats } from '../types'
import { TopicCard } from './TopicCard'
import { ProblemCard } from './ProblemCard'

interface SidebarProps {
  stats: OverallStats | null
  topics: TopicStats[]
  plan: DailyPlan | null
  timeMinutes: number
  setTimeMinutes: (minutes: number) => void
  onGeneratePlan: () => void
  loading: boolean
  onClose?: () => void
}

type TabType = 'topics' | 'plan'

export function Sidebar({ 
  stats, 
  topics, 
  plan, 
  timeMinutes, 
  setTimeMinutes, 
  onGeneratePlan, 
  loading,
  onClose
}: SidebarProps) {
  const [activeTab, setActiveTab] = useState<TabType>('topics')

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Mobile Close Button */}
      {onClose && (
        <div className="lg:hidden flex justify-end p-3 border-b border-gray-200">
          <button
            onClick={onClose}
            className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'topics'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('topics')}
        >
          Topics
        </button>
        <button
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'plan'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('plan')}
        >
          Daily Plan
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'topics' && (
          <div className="p-4 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Overall Progress</h3>
              {stats && (
                <div className="grid grid-cols-2 gap-2">
                  <Stat label="Solved" value={stats.total_problems_solved} />
                  <Stat label="Avg Attempts" value={stats.average_attempts_per_problem} />
                  <Stat label="Current Streak" value={stats.current_streak_days} />
                  <Stat label="Longest Streak" value={stats.longest_streak_days} />
                </div>
              )}
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Topic Breakdown</h3>
              <div className="space-y-3">
                {topics.map(topic => (
                  <TopicCard key={topic.topic} {...topic} />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'plan' && (
          <div className="p-4 space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Generate Plan</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Time Available (minutes)
                  </label>
                  <input 
                    type="number" 
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                    value={timeMinutes} 
                    onChange={e => setTimeMinutes(parseInt(e.target.value || '0'))} 
                    min="15"
                    max="480"
                    placeholder="60"
                  />
                </div>
                <button 
                  className="w-full px-4 py-2 rounded-md bg-green-600 text-white font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm" 
                  onClick={onGeneratePlan} 
                  disabled={loading}
                >
                  {loading ? 'Generating...' : 'Generate Plan'}
                </button>
              </div>
            </div>

            {plan && (
              <div className="border border-gray-200 rounded-lg bg-green-50 p-3">
                <div className="text-xs text-green-700">
                  ✓ Plan generated successfully! Check the main content area to view your daily plan.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border bg-white p-2">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  )
}
