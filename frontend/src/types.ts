export type Difficulty = 'easy' | 'medium' | 'hard';

export interface TopicStats {
  topic: string;
  easy_3d: number;
  medium_3d: number;
  hard_3d: number;
  easy_7d: number;
  medium_7d: number;
  hard_7d: number;
  easy_14d: number;
  medium_14d: number;
  hard_14d: number;
  easy_28d_plus: number;
  medium_28d_plus: number;
  hard_28d_plus: number;
  last_solved_date?: string | null;
  weighted_score: number;
}

export interface OverallStats {
  total_problems_solved: number;
  total_attempts: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  unique_topics_practiced: number;
  current_streak_days: number;
  longest_streak_days: number;
  average_attempts_per_problem: number;
}

export interface ProblemRecommendation {
  leetcode_number: number;
  title: string;
  difficulty: Difficulty;
  reason: string;
  estimated_minutes: number;
  leetcode_url: string;
}

export interface DailyPlan {
  id?: number;
  plan_date: string;
  available_time_minutes: number;
  focus_topic: string;
  recommendations: ProblemRecommendation[];
  ai_rationale: string;
  created_at?: string;
  is_cached: boolean;
}


