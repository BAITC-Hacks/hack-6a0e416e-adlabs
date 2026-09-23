export type Grade = 'Junior' | 'Middle' | 'Senior' | 'Lead';
export type CareerGoal = { target_role: string; target_grade: Grade };
export type TargetProfile = { role: string; grade: Grade; source: 'career_goal' | 'next_grade' };
export type EmployeeSummary = {
  employee_id: string; full_name: string; department: string;
  role: string; grade: Grade; career_goal: CareerGoal | null;
};
export type EmployeeProfile = EmployeeSummary & {
  manager_id: string | null; hire_date: string; tenure_months: number;
  work_format: 'office' | 'hybrid' | 'remote';
  preferred_language: 'kk' | 'ru' | 'en';
  skills: Record<string, number>;
  last_review_date: string;
};
export type EmployeeListResponse = { employees: EmployeeSummary[] };
export type EmployeeProfileResponse = { employee: EmployeeProfile; target: TargetProfile | null };
export type SkillGapItem = {
  skill_id: string; name: string; type: 'hard' | 'soft'; category: string;
  current_level: number; required_level: number; gap: number; critical: boolean;
};
export type SkillGapResponse = {
  employee_id: string; target: TargetProfile | null;
  status: 'in_progress' | 'ready' | 'no_target';
  progress_pct: number | null; total_required_points: number;
  total_met_points: number; total_gap_points: number;
  critical_gap_points: number; critical_skills_met: number;
  critical_skills_total: number; skills: SkillGapItem[];
};
export type ScoreBreakdown = {
  critical_skill_coverage: number; total_gap_coverage: number;
  career_goal_alignment: number; completion_likelihood: number;
  time_efficiency: number;
};
export type MatchedSkillGain = {
  skill_id: string; name: string; current_level: number;
  required_level: number; projected_level: number;
  gap_closed: number; critical: boolean;
};
export type ProjectedImpact = {
  progress_before_pct: number; progress_after_pct: number;
  progress_delta_pct: number; total_gap_points_before: number;
  total_gap_points_after: number; critical_gap_points_after: number;
};
export type Recommendation = {
  event_id: string; title: string; description: string; type: string;
  format: 'online' | 'offline' | 'self_paced';
  duration_hours: number; next_session_date: string | null;
  score: number; score_breakdown: ScoreBreakdown;
  matched_skill_gains: MatchedSkillGain[];
  projected_impact: ProjectedImpact; explanation: string;
};
export type RecommendationsResponse = {
  employee_id: string; target: TargetProfile | null;
  recommendations: Recommendation[];
};
export type RoadmapStep = {
  order: number; recommendation: Recommendation;
  progress_before_pct: number; progress_after_pct: number;
};
export type RoadmapResponse = {
  employee_id: string; target: TargetProfile | null;
  status: 'in_progress' | 'ready' | 'no_target' | 'no_activities';
  starting_progress_pct: number | null;
  ending_progress_pct: number | null; steps: RoadmapStep[];
};
export type AppliedSkillGain = {
  skill_id: string; before_level: number; after_level: number; gain: number;
};
export type CompletionResponse = {
  employee_id: string; event_id: string; activity_status: 'completed';
  applied_skill_gains: AppliedSkillGain[];
  skill_gap: SkillGapResponse; recommendations: Recommendation[];
  roadmap: RoadmapResponse;
};
export type ActivitySkill = { skill_id: string; name: string; current_level: number; required_level: number | null; gain: number | null; max_level: number | null; met: boolean | null };
export type ActivityDetailsResponse = {
  employee_id: string; event_id: string; title: string; description: string; type: string;
  format: 'online' | 'offline' | 'self_paced'; duration_hours: number;
  upcoming_sessions: string[]; next_session_date: string | null;
  prerequisites: ActivitySkill[]; develops_skills: ActivitySkill[];
  external_url: string | null; provider_url: string | null;
  status: 'not_started' | 'enrolled' | 'in_progress' | 'completed';
  eligible: boolean; recommendation: Recommendation | null;
};
export type ActivityActionResponse = { employee_id: string; event_id: string; status: 'enrolled' | 'in_progress' };
export type ActivityHistoryItem = { record_id: string | null; event_id: string; title: string; date: string | null; status: string; source: 'dataset' | 'demo' };
export type ActivityHistoryResponse = { employee_id: string; activities: ActivityHistoryItem[] };
export type NavigatorIntent = 'why_course' | 'compare' | 'blockers' | 'first_skill' | 'after_activity' | 'faster_route' | 'four_hours' | 'data_sources' | 'disagree' | 'career_transition' | 'general';
export type NavigatorResponse = {
  employee_id: string; provider: 'template' | 'openai' | 'nvidia'; intent: string;
  summary: string; profile_facts: string[]; reason: string; expected_effect: string;
  limitation: string; next_step: string; evidence_ids: string[];
  ai_explanation: {
    summary: string; why_recommended: string[]; expected_impact: string[];
    limitations: string[]; next_step: string; confidence: 'high' | 'medium' | 'low';
    evidence_ids: string[];
  } | null;
};
export type DepartmentSummary = {
  department: string; employee_count: number;
  average_progress_pct: number | null; employees_ready: number;
};
export type HROverviewResponse = {
  as_of_date: string; employee_count: number;
  employees_with_explicit_goal: number; employees_without_explicit_goal: number;
  employees_ready: number; employees_without_target: number;
  average_progress_pct: number | null; grade_counts: Record<Grade, number>;
  departments: DepartmentSummary[];
};
export type ErrorResponse = { error: { code: string; message: string } };
