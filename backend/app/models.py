"""Public wire models from contracts/types.md."""

from typing import Literal
from pydantic import BaseModel, Field

Grade = Literal["Junior", "Middle", "Senior", "Lead"]


class CareerGoal(BaseModel):
    target_role: str
    target_grade: Grade


class TargetProfile(BaseModel):
    role: str
    grade: Grade
    source: Literal["career_goal", "next_grade"]


class EmployeeSummary(BaseModel):
    employee_id: str
    full_name: str
    department: str
    role: str
    grade: Grade
    career_goal: CareerGoal | None


class EmployeeProfile(EmployeeSummary):
    manager_id: str | None
    hire_date: str
    tenure_months: int
    work_format: Literal["office", "hybrid", "remote"]
    preferred_language: Literal["kk", "ru", "en"]
    skills: dict[str, int]
    last_review_date: str


class EmployeeListResponse(BaseModel):
    employees: list[EmployeeSummary]


class EmployeeProfileResponse(BaseModel):
    employee: EmployeeProfile
    target: TargetProfile | None


class SkillGapItem(BaseModel):
    skill_id: str
    name: str
    type: Literal["hard", "soft"]
    category: str
    current_level: int
    required_level: int
    gap: int
    critical: bool


class SkillGapResponse(BaseModel):
    employee_id: str
    target: TargetProfile | None
    status: Literal["in_progress", "ready", "no_target"]
    progress_pct: float | None
    total_required_points: int
    total_met_points: int
    total_gap_points: int
    critical_gap_points: int
    critical_skills_met: int
    critical_skills_total: int
    skills: list[SkillGapItem]


class ScoreBreakdown(BaseModel):
    critical_skill_coverage: float
    total_gap_coverage: float
    career_goal_alignment: float
    completion_likelihood: float
    time_efficiency: float


class MatchedSkillGain(BaseModel):
    skill_id: str
    name: str
    current_level: int
    required_level: int
    projected_level: int
    gap_closed: int
    critical: bool


class ProjectedImpact(BaseModel):
    progress_before_pct: float
    progress_after_pct: float
    progress_delta_pct: float
    total_gap_points_before: int
    total_gap_points_after: int
    critical_gap_points_after: int


class Recommendation(BaseModel):
    event_id: str
    title: str
    description: str
    type: str
    format: Literal["online", "offline", "self_paced"]
    duration_hours: float
    next_session_date: str | None
    score: float
    score_breakdown: ScoreBreakdown
    matched_skill_gains: list[MatchedSkillGain]
    projected_impact: ProjectedImpact
    explanation: str


class RecommendationsResponse(BaseModel):
    employee_id: str
    target: TargetProfile | None
    recommendations: list[Recommendation]


class RoadmapStep(BaseModel):
    order: int
    recommendation: Recommendation
    progress_before_pct: float
    progress_after_pct: float


class RoadmapResponse(BaseModel):
    employee_id: str
    target: TargetProfile | None
    status: Literal["in_progress", "ready", "no_target", "no_activities"]
    starting_progress_pct: float | None
    ending_progress_pct: float | None
    steps: list[RoadmapStep]


class AppliedSkillGain(BaseModel):
    skill_id: str
    before_level: int
    after_level: int
    gain: int


class CompletionResponse(BaseModel):
    employee_id: str
    event_id: str
    activity_status: Literal["completed"] = "completed"
    applied_skill_gains: list[AppliedSkillGain]
    skill_gap: SkillGapResponse
    recommendations: list[Recommendation]
    roadmap: RoadmapResponse


class DepartmentSummary(BaseModel):
    department: str
    employee_count: int
    average_progress_pct: float | None
    employees_ready: int


class HROverviewResponse(BaseModel):
    as_of_date: str
    employee_count: int
    employees_with_explicit_goal: int
    employees_without_explicit_goal: int
    employees_ready: int
    employees_without_target: int
    average_progress_pct: float | None
    grade_counts: dict[Grade, int]
    departments: list[DepartmentSummary]


class DatasetCounts(BaseModel):
    employees: int
    events: int
    skills: int
    role_profiles: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    as_of_date: str
    dataset: DatasetCounts


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ActivitySkill(BaseModel):
    skill_id: str
    name: str
    current_level: int
    required_level: int | None = None
    gain: int | None = None
    max_level: int | None = None
    met: bool | None = None


class ActivityDetailsResponse(BaseModel):
    employee_id: str
    event_id: str
    title: str
    description: str
    type: str
    format: Literal["online", "offline", "self_paced"]
    duration_hours: float
    upcoming_sessions: list[str]
    next_session_date: str | None
    prerequisites: list[ActivitySkill]
    develops_skills: list[ActivitySkill]
    external_url: str | None
    provider_url: str | None
    status: Literal["not_started", "enrolled", "in_progress", "completed"]
    eligible: bool
    recommendation: Recommendation | None


class ActivityActionResponse(BaseModel):
    employee_id: str
    event_id: str
    status: Literal["enrolled", "in_progress"]


class ActivityHistoryItem(BaseModel):
    record_id: str | None
    event_id: str
    title: str
    date: str | None
    status: str
    source: Literal["dataset", "demo"]


class ActivityHistoryResponse(BaseModel):
    employee_id: str
    activities: list[ActivityHistoryItem]


class NavigatorRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    intent: Literal["why_course", "compare", "blockers", "first_skill", "after_activity", "faster_route", "four_hours", "data_sources", "disagree", "general"] | None = None
    event_id: str | None = None
    weekly_hours: float | None = Field(default=None, gt=0, le=80)


class NavigatorResponse(BaseModel):
    employee_id: str
    provider: Literal["template", "openai", "nvidia"]
    intent: str
    summary: str
    profile_facts: list[str]
    reason: str
    expected_effect: str
    limitation: str
    next_step: str
    evidence_ids: list[str]
    ai_explanation: dict | None = None


class AIStatusResponse(BaseModel):
    configured_provider: Literal["template", "openai", "nvidia"]
    active_provider: Literal["template", "openai", "nvidia"]
    fallback_provider: Literal["template", "openai", "nvidia"]
    nvidia_configured: bool
    openai_configured: bool
    template_fallback_available: bool
