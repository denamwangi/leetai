import type { TopicStats } from '../types';

export function TopicCard({ topic, weighted_score, ...s }: TopicStats) {
  return (
    <div className="rounded-lg border p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{topic}</h3>
        <span className="text-sm text-gray-600">Score: {weighted_score}</span>
      </div>
      <div className="mt-2 grid grid-cols-4 gap-2 text-xs text-gray-700">
        <div>
          <div className="font-medium">3d</div>
          <div>E:{s.easy_3d}</div>
          <div>M:{s.medium_3d}</div>
          <div>H:{s.hard_3d}</div>
        </div>
        <div>
          <div className="font-medium">7d</div>
          <div>E:{s.easy_7d}</div>
          <div>M:{s.medium_7d}</div>
          <div>H:{s.hard_7d}</div>
        </div>
        <div>
          <div className="font-medium">14d</div>
          <div>E:{s.easy_14d}</div>
          <div>M:{s.medium_14d}</div>
          <div>H:{s.hard_14d}</div>
        </div>
        <div>
          <div className="font-medium">28d+</div>
          <div>E:{s.easy_28d_plus}</div>
          <div>M:{s.medium_28d_plus}</div>
          <div>H:{s.hard_28d_plus}</div>
        </div>
      </div>
    </div>
  );
}


