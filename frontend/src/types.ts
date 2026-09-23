export type Language = "ru" | "en" | "kk";
export type DemoRole = "employee" | "hr";

export interface CareerGoal {
  target_role: string;
  target_grade: string;
}

export interface Employee {
  employee_id: string;
  full_name: string;
  department: string;
  role: string;
  grade: string;
  manager_id: string | null;
  hire_date: string;
  tenure_months: number;
  work_format: string;
  preferred_language: Language;
  career_goal: CareerGoal | null;
  last_review_date: string;
}

export interface SkillGap {
  skill_id: string;
  name: string;
  category: string;
  current: number;
  required: number;
  gap: number;
  critical: boolean;
  baseline?: number;
  improved_after_review?: boolean;
}

export interface LearningEvent {
  event_id: string;
  title: string;
  description: string;
  type: string;
  format: string;
  duration_hours: number;
  mandatory: boolean;
  develops_skills: Array<{ skill_id: string; gain: number; max_level: number }>;
  prerequisites: Record<string, number>;
  upcoming_sessions: string[];
}

export interface Recommendation extends LearningEvent {
  score: number;
  locked: boolean;
  unmet_prerequisites: Record<string, number>;
  quest_chain: LearningEvent[];
  impact: {
    readiness_before: number;
    readiness_after: number;
    readiness_gain: number;
  };
  reasons: Array<{ group: "goal" | "skills" | "history"; text: string }>;
}

export interface CareerNode {
  kind: "current" | "target" | "future";
  role: string;
  grade: string;
  label: string;
}

export interface ProgressData {
  xp: number;
  rank: string;
  next_rank: string;
  rank_floor: number;
  next_rank_xp: number;
  completed_quests: number;
  achievements: Array<{ code: string; title: string }>;
}

export interface DashboardData {
  employee: Employee;
  career_goal: CareerGoal | null;
  readiness: number;
  top_gaps: SkillGap[];
  active_quest: LearningEvent | null;
  next_quest: Recommendation | null;
  progress: ProgressData;
  career_map: CareerNode[];
}

export interface SkillsData {
  employee_id: string;
  career_goal: CareerGoal | null;
  readiness: number;
  skills: SkillGap[];
}

export interface CareerData {
  employee_id: string;
  current: { role: string; grade: string };
  goal: CareerGoal | null;
  readiness: number;
  gaps: SkillGap[];
  career_map: CareerNode[];
}

export interface QuestItem extends LearningEvent {
  state?: string;
  started_at?: string;
  completed_at?: string;
  progress?: number;
}

export interface QuestData {
  employee_id: string;
  recommended: Recommendation[];
  active: QuestItem[];
  completed: QuestItem[];
}

export interface HROverview {
  top_gaps: Array<{ skill_id: string; name: string; critical: boolean; employees: number }>;
  employees_without_goal: Employee[];
  employees_without_next_step: Employee[];
  participation: Record<string, number>;
  totals: { employees: number; events: number; activity_records: number };
}

export interface CoachReply {
  answer: string;
  actions: Array<
    | { type: "navigate"; to: string }
    | { type: "quest"; event_id: string; label: string }
  >;
}
