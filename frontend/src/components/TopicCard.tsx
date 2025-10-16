import type { TopicStats } from '../types';

function getSkillLevel(score: number): { level: string; color: string } {
  if (score >= 80) return { level: 'Advanced', color: 'text-green-600' };
  if (score >= 40) return { level: 'Intermediate', color: 'text-yellow-600' };
  return { level: 'Noob', color: 'text-red-600' };
}

export function TopicCard({ topic, weighted_score }: TopicStats) {
  const { level, color } = getSkillLevel(weighted_score);
  
  return (
    <div className="rounded-lg border p-4 bg-white shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{topic}</h3>
        <span className={`text-sm font-medium ${color}`}>{level}</span>
      </div>
      <div className="mt-2 text-sm text-gray-600">
        Score: {weighted_score.toFixed(1)}
      </div>
    </div>
  );
}


