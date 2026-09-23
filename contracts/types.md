# Career Quest shared wire models

TypeScript notation defines the JSON contract. Pydantic models must serialize the same field names. Percentages and weighted score components are rounded to one decimal for output; calculations use unrounded values. Nullable fields are present with `null`.

```ts
type Grade = "Junior" | "Middle" | "Senior" | "Lead";
type CareerGoal = { target_role: string; target_grade: Grade };
type TargetProfile = { role: string; grade: Grade; source: "career_goal" | "next_grade" };
type EmployeeSummary = {
  employee_id: string; full_name: string; department: string;
  role: string; grade: Grade; career_goal: CareerGoal | null;
};
type EmployeeProfile = EmployeeSummary & {
  manager_id: string | null; hire_date: string; tenure_months: number;
  work_format: "office" | "hybrid" | "remote";
  preferred_language: "kk" | "ru" | "en";
  skills: Record<string, number>; // skill_id -> integer 0..5; absent skill = 0
  last_review_date: string;
};
type EmployeeListResponse = { employees: EmployeeSummary[] };
type EmployeeProfileResponse = { employee: EmployeeProfile; target: TargetProfile | null };

type SkillGapItem = {
  skill_id: string; name: string; type: "hard" | "soft"; category: string;
  current_level: number; required_level: number; gap: number; critical: boolean;
};
type SkillGapResponse = {
  employee_id: string; target: TargetProfile | null;
  status: "in_progress" | "ready" | "no_target";
  progress_pct: number | null; total_required_points: number;
  total_met_points: number; total_gap_points: number;
  critical_gap_points: number; critical_skills_met: number;
  critical_skills_total: number; skills: SkillGapItem[];
};

type ScoreBreakdown = {
  critical_skill_coverage: number; // weighted points 0..45
  total_gap_coverage: number; // weighted points 0..25
  career_goal_alignment: number; // weighted points 0..15
  completion_likelihood: number; // weighted points 0..10
  time_efficiency: number; // weighted points 0..5
};
type MatchedSkillGain = {
  skill_id: string; name: string; current_level: number;
  required_level: number; projected_level: number;
  gap_closed: number; critical: boolean;
};
type ProjectedImpact = {
  progress_before_pct: number; progress_after_pct: number;
  progress_delta_pct: number; // percentage points
  total_gap_points_before: number; total_gap_points_after: number;
  critical_gap_points_after: number;
};
type Recommendation = {
  event_id: string; title: string; description: string; type: string;
  format: "online" | "offline" | "self_paced";
  duration_hours: number; next_session_date: string | null;
  score: number; score_breakdown: ScoreBreakdown;
  matched_skill_gains: MatchedSkillGain[];
  projected_impact: ProjectedImpact; explanation: string;
};
type RecommendationsResponse = {
  employee_id: string; target: TargetProfile | null;
  recommendations: Recommendation[]; // 0..3
};

type RoadmapStep = {
  order: number; recommendation: Recommendation;
  progress_before_pct: number; progress_after_pct: number;
};
type RoadmapResponse = {
  employee_id: string; target: TargetProfile | null;
  status: "in_progress" | "ready" | "no_target" | "no_activities";
  starting_progress_pct: number | null;
  ending_progress_pct: number | null; steps: RoadmapStep[]; // 0..3
};
type AppliedSkillGain = {
  skill_id: string; before_level: number; after_level: number; gain: number;
};
type CompletionResponse = {
  employee_id: string; event_id: string;
  applied_skill_gains: AppliedSkillGain[];
  skill_gap: SkillGapResponse; recommendations: Recommendation[];
  roadmap: RoadmapResponse;
};

type DepartmentSummary = {
  department: string; employee_count: number;
  average_progress_pct: number | null; employees_ready: number;
};
type HROverviewResponse = {
  as_of_date: string; employee_count: number;
  employees_with_explicit_goal: number; employees_without_explicit_goal: number;
  employees_ready: number; employees_without_target: number;
  average_progress_pct: number | null; grade_counts: Record<Grade, number>;
  departments: DepartmentSummary[];
};
type HealthResponse = {
  status: "ok"; as_of_date: string;
  dataset: { employees: number; events: number; skills: number; role_profiles: number };
};
type ErrorResponse = { error: { code: string; message: string } };
```
