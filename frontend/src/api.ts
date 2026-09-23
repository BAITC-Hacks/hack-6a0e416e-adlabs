import type {
  CareerData,
  CoachReply,
  DashboardData,
  DemoRole,
  Employee,
  HROverview,
  Language,
  QuestData,
  SkillsData,
} from "./types";


const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export interface ApiContext {
  role?: DemoRole;
  employeeId?: string | null;
}

async function request<T>(path: string, init: RequestInit = {}, context: ApiContext = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  headers.set("X-Demo-Role", context.role || "employee");
  if (context.employeeId) headers.set("X-Employee-ID", context.employeeId);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch (error) {
    throw new ApiError("Backend is unavailable. Check that the API is running.", 0, error);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data?.error?.message || `Request failed with status ${response.status}`;
    throw new ApiError(message, response.status, data);
  }
  return data as T;
}

export const api = {
  employees: (query = "") =>
    request<{ results: Employee[]; count: number }>(`/employees/?limit=200&q=${encodeURIComponent(query)}`),
  employee: (employeeId: string) =>
    request<Employee>(`/employees/${employeeId}/`, {}, { employeeId }),
  dashboard: (employeeId: string) =>
    request<DashboardData>(`/employees/${employeeId}/dashboard/`, {}, { employeeId }),
  skills: (employeeId: string) =>
    request<SkillsData>(`/employees/${employeeId}/skills/`, {}, { employeeId }),
  career: (employeeId: string) =>
    request<CareerData>(`/employees/${employeeId}/career/`, {}, { employeeId }),
  quests: (employeeId: string) =>
    request<QuestData>(`/employees/${employeeId}/quests/`, {}, { employeeId }),
  roleProfiles: () => request<{ results: Array<{ role: string; grade: string }> }>("/role-profiles/"),
  updateGoal: (employeeId: string, target_role: string, target_grade: string) =>
    request<CareerData>(
      `/employees/${employeeId}/career-goal/`,
      { method: "POST", body: JSON.stringify({ target_role, target_grade }) },
      { employeeId },
    ),
  startQuest: (employeeId: string, eventId: string) =>
    request<{ state: string; event_id: string }>(
      `/quests/${eventId}/start/`,
      { method: "POST", body: JSON.stringify({ employee_id: employeeId }) },
      { employeeId },
    ),
  completeQuest: (employeeId: string, eventId: string) =>
    request<{ state: string; xp_awarded: number; idempotent: boolean; dashboard: DashboardData }>(
      `/quests/${eventId}/complete/`,
      { method: "POST", body: JSON.stringify({ employee_id: employeeId }) },
      { employeeId },
    ),
  coach: (employeeId: string, question: string, language: Language) =>
    request<CoachReply>(
      "/ai/chat/",
      { method: "POST", body: JSON.stringify({ employee_id: employeeId, question, language }) },
      { employeeId },
    ),
  hrOverview: () => request<HROverview>("/hr/overview/", {}, { role: "hr" }),
};
