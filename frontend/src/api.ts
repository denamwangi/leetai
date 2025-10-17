import type { DailyPlan, OverallStats, TopicStats } from './types';

const BASE_URL = import.meta.env.VITE_BACKEND_URL ?? 'http://localhost:8000';

async function handle<T>(res: Response): Promise<T> {
  if (!res || !res.ok) {
    const status = typeof res?.status === 'number' ? res.status : 0;
    let errorMessage = status ? `HTTP ${status}` : 'Network error';
    try {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const json = await res.json();
        errorMessage = json.detail || json.message || errorMessage;
      } else {
        const text = await res.text();
        if (text) errorMessage = text;
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(errorMessage);
  }
  return res.json();
}

export const api = {
  // IMPORTANT: Must be async and await fetch() before passing to handle()
  // The handle() function expects a Response object, not a Promise<Response>
  // If you pass a Promise to handle(), it will see status: undefined and throw "Network error"
  sync: async (limit = 20, dryRun = false) => {
    const url = `${BASE_URL}/api/sync?limit=${limit}&dry_run=${dryRun}`;
    const response = await fetch(url, { 
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    return handle<{ new_problems: number; new_submissions: number; message: string }>(response);
  },

  overallStats: async () => {
    const res = await fetch(`${BASE_URL}/api/stats`);
    return handle<OverallStats>(res);
  },

  topicStats: async () => {
    const res = await fetch(`${BASE_URL}/api/stats/topics`);
    return handle<TopicStats[]>(res);
  },

  dailyPlan: async (params: { date?: string; time_minutes: number; custom_instructions?: string }) => {
    const qs = new URLSearchParams();
    if (params.date) qs.set('date', params.date);
    qs.set('time_minutes', String(params.time_minutes));
    if (params.custom_instructions) qs.set('custom_instructions', params.custom_instructions);
    const res = await fetch(`${BASE_URL}/api/daily-plan?${qs.toString()}`);
    return handle<DailyPlan>(res);
  },
};


