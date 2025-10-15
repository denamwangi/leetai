import type { ProblemRecommendation } from '../types';

export function ProblemCard({ leetcode_number, title, difficulty, reason, estimated_minutes, leetcode_url }: ProblemRecommendation) {
  const badge =
    difficulty === 'easy' ? 'bg-green-100 text-green-700' :
    difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
    'bg-red-100 text-red-700';

  return (
    <a className="block rounded-lg border p-4 bg-white hover:shadow" href={leetcode_url} target="_blank" rel="noreferrer">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold">{leetcode_number}. {title}</h4>
        <span className={`text-xs px-2 py-1 rounded ${badge}`}>{difficulty}</span>
      </div>
      <p className="mt-2 text-sm text-gray-600">{reason}</p>
      <div className="mt-2 text-xs text-gray-500">~{estimated_minutes} min</div>
    </a>
  );
}


