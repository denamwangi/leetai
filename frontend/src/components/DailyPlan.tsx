import type { DailyPlan } from '../types'
import { ProblemCard } from './ProblemCard'

interface DailyPlanProps {
  plan: DailyPlan
}

export function DailyPlan({ plan }: DailyPlanProps) {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Daily Study Plan</h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>Focus: <span className="font-medium text-gray-900">{plan.focus_topic}</span></span>
          <span>Time: <span className="font-medium text-gray-900">{plan.available_time_minutes} minutes</span></span>
          {plan.is_cached && <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">cached</span>}
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Problems</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {plan.recommendations.map(r => (
            <ProblemCard key={r.leetcode_number + r.title} {...r} />
          ))}
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">AI Rationale</h3>
        <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
          {plan.ai_rationale || 'No rationale available'}
        </div>
      </div>
    </div>
  )
}
