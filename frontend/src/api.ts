import type {
  CompletionResponse, EmployeeListResponse, EmployeeProfileResponse,
  HROverviewResponse, RecommendationsResponse, RoadmapResponse, SkillGapResponse,
  ErrorResponse,
} from './types';

const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      ...options,
      headers: { Accept: 'application/json', ...options?.headers },
    });
  } catch {
    throw new ApiError('Не удалось подключиться к серверу. Проверьте, что API запущен.', 0);
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null) as ErrorResponse | null;
    throw new ApiError(
      payload?.error?.message || `Ошибка сервера (${response.status})`,
      response.status,
      payload?.error?.code,
    );
  }
  return response.json() as Promise<T>;
}

const employeePath = (id: string) => `/api/employees/${encodeURIComponent(id)}`;

export const api = {
  employees: () => request<EmployeeListResponse>('/api/employees'),
  profile: (id: string) => request<EmployeeProfileResponse>(employeePath(id)),
  skillGap: (id: string) => request<SkillGapResponse>(`${employeePath(id)}/skill-gap`),
  recommendations: (id: string) => request<RecommendationsResponse>(`${employeePath(id)}/recommendations`),
  roadmap: (id: string) => request<RoadmapResponse>(`${employeePath(id)}/roadmap`),
  complete: (id: string, eventId: string) => request<CompletionResponse>(
    `${employeePath(id)}/activities/${encodeURIComponent(eventId)}/complete`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' },
  ),
  hrOverview: () => request<HROverviewResponse>('/api/hr/overview'),
};
