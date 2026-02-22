import { apiClient } from './client'
import type {
  User,
  Role,
  Case,
  Complaint,
  Evidence,
  EvidenceLink,
  Suspect,
  Interrogation,
  Trial,
  Verdict,
  Notification,
  Statistics,
  PaginatedResponse,
  ApiSuccess,
} from '@/types'

const unwrap = <T>(res: { data: ApiSuccess<T> }) => res.data.data

// Auth
export const authApi = {
  login: (identifier: string, password: string) =>
    apiClient.post<ApiSuccess<{ user: User; tokens: { access: string; refresh: string } }>>('auth/login/', {
      identifier,
      password,
    }).then((res) => res.data.data),

  register: (payload: {
    username: string
    password: string
    email: string
    phone: string
    full_name: string
    national_id: string
    role_ids?: number[]
  }) =>
    apiClient.post<ApiSuccess<{ id: number; username: string; email: string; phone: string; full_name: string; national_id: string; is_active: boolean; roles: Role[]; role_names: string[]; date_joined: string }>>('auth/register/', payload).then((res) => res.data.data),

  refreshToken: (refresh: string) =>
    apiClient.post<{ access: string }>('auth/token/refresh/', { refresh }).then((res) => res.data.access),
}

// Users & Roles
export const usersApi = {
  list: (params?: { is_active?: boolean; username?: string }) =>
    apiClient.get<PaginatedResponse<User> | User[]>('auth/users/', { params }).then((res) => res.data),
  listDetectives: () =>
    apiClient
      .get<PaginatedResponse<User> | User[]>('auth/users/detectives/')
      .then((res) => (Array.isArray(res.data) ? res.data : (res.data as PaginatedResponse<User>).results ?? [])),
  get: (id: number) => apiClient.get<ApiSuccess<User>>(`auth/users/${id}/`).then(unwrap),
  update: (id: number, data: Partial<User> & { role_ids?: number[] }) =>
    apiClient.patch<ApiSuccess<User>>(`auth/users/${id}/`, data).then(unwrap),
}

export const rolesApi = {
  list: () =>
    apiClient
      .get<Role[] | PaginatedResponse<Role>>('auth/roles/')
      .then((res) => (Array.isArray(res.data) ? res.data : (res.data as PaginatedResponse<Role>).results ?? [])),
  create: (data: { name: string; description?: string }) =>
    apiClient.post<Role>('auth/roles/', data).then((res) => res.data),
  update: (id: number, data: Partial<Role>) => apiClient.patch<Role>(`auth/roles/${id}/`, data).then((res) => res.data),
  delete: (id: number) => apiClient.delete(`auth/roles/${id}/`),
}

// Statistics
export const statisticsApi = {
  get: () =>
    apiClient.get<ApiSuccess<Statistics>>('statistics/').then((res) => res.data.data),
}

// Cases
export interface CrimeSceneCasePayload {
  title: string
  description?: string
  scene_date: string // YYYY-MM-DD
  scene_time: string // HH:mm
  location_description?: string
  witnesses?: { national_id: string; phone: string }[]
}

export const casesApi = {
  list: (params?: { status?: string; severity?: string }) =>
    apiClient.get<PaginatedResponse<Case> | Case[]>('cases/', { params }).then((res) => res.data),
  get: (id: number) => apiClient.get<Case>('cases/' + id + '/').then((res) => res.data),
  create: (data: Partial<Case>) => apiClient.post<Case>('cases/', data).then((res) => res.data),
  createCrimeScene: (data: CrimeSceneCasePayload) =>
    apiClient.post<{ success: true; data: Case }>('cases/crime-scene/', data).then((res) => res.data.data),
  update: (id: number, data: Partial<Case>) => apiClient.patch<Case>(`cases/${id}/`, data).then((res) => res.data),
}

// Complaints
export const complaintsApi = {
  list: () => apiClient.get<PaginatedResponse<Complaint> | Complaint[]>('complaints/').then((res) => res.data),
  get: (id: number) => apiClient.get<Complaint>(`complaints/${id}/`).then((res) => res.data),
  create: (data: { title: string; description: string }) =>
    apiClient.post<Complaint>('complaints/', data).then((res) => res.data),
  traineeReview: (id: number, action: 'approve' | 'return_correction', correction_message?: string) =>
    apiClient.post(`complaints/${id}/trainee-review/`, { action, correction_message }).then((res) => res.data),
  officerReview: (id: number, action: 'approve' | 'send_back') =>
    apiClient.post(`complaints/${id}/officer-review/`, { action }).then((res) => res.data),
  correct: (id: number, data: { title?: string; description?: string }) =>
    apiClient.post(`complaints/${id}/correct/`, data).then((res) => res.data),
}

// Evidence
export const evidenceApi = {
  list: (params?: { case?: number }) =>
    apiClient.get<PaginatedResponse<Evidence> | Evidence[]>('evidence/', { params }).then((res) => res.data),
  get: (id: number) => apiClient.get<Evidence>(`evidence/${id}/`).then((res) => res.data),
  create: (data: FormData | Record<string, unknown>) =>
    apiClient.post<Evidence>('evidence/', data, data instanceof FormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : {}).then((res) => res.data),
  delete: (id: number) => apiClient.delete(`evidence/${id}/`),
  biologicalReview: (id: number, validity_status: 'approved' | 'rejected') =>
    apiClient.post(`evidence/${id}/biological-review/`, { validity_status }).then((res) => res.data),
}

// Evidence links (for detective board)
export const evidenceLinksApi = {
  list: (caseId: number) =>
    apiClient.get<PaginatedResponse<EvidenceLink> | EvidenceLink[]>(`cases/${caseId}/evidence-links/`).then((res) => res.data),
  create: (caseId: number, data: { evidence_from: number; evidence_to: number; link_type?: string }) =>
    apiClient.post<EvidenceLink>(`cases/${caseId}/evidence-links/`, data).then((res) => res.data),
  delete: (caseId: number, linkId: number) => apiClient.delete(`cases/${caseId}/evidence-links/${linkId}/`),
}

// Suspects
export const suspectsApi = {
  list: (params?: { case?: number }) =>
    apiClient.get<PaginatedResponse<Suspect> | Suspect[]>('suspects/', { params }).then((res) => res.data),
  highPriority: () =>
    apiClient.get<PaginatedResponse<Suspect> | Suspect[]>('suspects/high-priority/').then((res) => res.data),
  get: (id: number) => apiClient.get<Suspect>(`suspects/${id}/`).then((res) => res.data),
  propose: (caseId: number, userId: number) =>
    apiClient.post<{ data: Suspect }>('suspects/', { case_id: caseId, user_id: userId }).then((res) => res.data),
  supervisorReview: (id: number, action: 'approve' | 'reject') =>
    apiClient.post(`suspects/${id}/supervisor-review/`, { action }).then((res) => res.data),
}

// Interrogations
export const interrogationsApi = {
  list: (params?: { suspect?: number }) =>
    apiClient.get<PaginatedResponse<Interrogation> | Interrogation[]>('interrogations/', { params }).then((res) => res.data),
  create: (data: { suspect: number; detective_probability?: number; supervisor_probability?: number }) =>
    apiClient.post<Interrogation>('interrogations/', data).then((res) => res.data),
  captainDecision: (id: number, captain_decision: string) =>
    apiClient.post(`interrogations/${id}/captain-decision/`, { captain_decision }).then((res) => res.data),
  chiefConfirm: (id: number) => apiClient.post(`interrogations/${id}/chief-confirm/`).then((res) => res.data),
}

// Trials & Verdicts
export const trialsApi = {
  list: () => apiClient.get<PaginatedResponse<Trial> | Trial[]>('trials/').then((res) => res.data),
  get: (id: number) => apiClient.get<Trial>(`trials/${id}/`).then((res) => res.data),
  create: (data: { case: number; judge?: number }) => apiClient.post<Trial>('trials/', data).then((res) => res.data),
  update: (id: number, data: Partial<Trial>) => apiClient.patch<Trial>(`trials/${id}/`, data).then((res) => res.data),
}

export const verdictsApi = {
  list: () => apiClient.get<PaginatedResponse<Verdict> | Verdict[]>('verdicts/').then((res) => res.data),
  create: (data: { trial: number; title: string; description?: string; punishment_title?: string; punishment_description?: string }) =>
    apiClient.post<Verdict>('verdicts/', data).then((res) => res.data),
}

// Notifications
export const notificationsApi = {
  list: () =>
    apiClient.get<PaginatedResponse<Notification> | Notification[]>('notifications/').then((res) => res.data),
  markRead: (id: number) => apiClient.post(`notifications/${id}/read/`).then((res) => res.data),
}
