import type { DailyPlan, OverallStats, TopicStats } from './types';

const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  sync: (limit = 20, dryRun = false) =>
    handle<{ new_problems: number; new_submissions: number; message: string }>(
      fetch(`${BASE_URL}/api/sync?limit=${limit}&dry_run=${dryRun}`, { method: 'POST' })
    ),

  overallStats: () =>
    handle<OverallStats>(fetch(`${BASE_URL}/api/stats`)),

  topicStats: () =>
    handle<TopicStats[]>(fetch(`${BASE_URL}/api/stats/topics`)),

  dailyPlan: (params: { date?: string; time_minutes: number; custom_instructions?: string }) => {
    const qs = new URLSearchParams();
    if (params.date) qs.set('date', params.date);
    qs.set('time_minutes', String(params.time_minutes));
    if (params.custom_instructions) qs.set('custom_instructions', params.custom_instructions);
    return handle<DailyPlan>(fetch(`${BASE_URL}/api/daily-plan?${qs.toString()}`));
  },
};


