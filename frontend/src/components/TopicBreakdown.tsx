import type { TopicStats } from '../types'
import { TopicCard } from './TopicCard'

interface TopicBreakdownProps {
  topics: TopicStats[]
}

export function TopicBreakdown({ topics }: TopicBreakdownProps) {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Topic Breakdown</h2>
        <p className="text-gray-600">Detailed analysis of your progress across different topics</p>
      </div>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {topics.map(topic => (
          <TopicCard key={topic.topic} {...topic} />
        ))}
      </div>
    </div>
  )
}
