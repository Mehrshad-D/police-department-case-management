export interface User {
  id: number
  username: string
  email: string
  phone: string
  full_name: string
  national_id: string
  is_active: boolean
  is_staff?: boolean
  roles: Role[]
  role_names: string[]
  date_joined: string
}

export interface Role {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
}

export interface ApiTokens {
  access: string
  refresh: string
}

export interface LoginPayload {
  identifier: string
  password: string
}

export interface RegisterPayload {
  username: string
  password: string
  email: string
  phone: string
  full_name: string
  national_id: string
  role_ids?: number[]
}

export interface Case {
  id: number
  title: string
  description: string
  severity: number
  status: string
  is_crime_scene_case: boolean
  created_by: number
  created_by_username: string
  assigned_detective: number | null
  assigned_detective_username: string | null
  approved_by_captain: number | null
  created_at: string
  updated_at: string
  complainants?: CaseComplainant[]
  complaint_origin?: Complaint | null
}

export interface CaseComplainant {
  id: number
  case: number
  user: number
  user_username: string
  is_primary: boolean
  notes: string
  added_at: string
}

export interface Complaint {
  id: number
  complainant: number
  complainant_username: string
  title: string
  description: string
  status: string
  correction_count: number
  last_correction_message: string
  case: number | null
  created_at: string
  updated_at: string
}

export interface Evidence {
  id: number
  case: number
  evidence_type: string
  title: string
  description: string
  date_recorded?: string
  recorder: number | null
  recorder_username: string | null
  created_at: string
  updated_at: string
  witness_detail?: { transcript?: string; media_files?: { file: string; media_type: string }[] }
  biological_detail?: { verification_status: string; verification_result?: string | null; images?: { id: number; image: string; caption?: string }[] }
  vehicle_detail?: { model?: string; color?: string; license_plate?: string; serial_number?: string }
  id_document_detail?: { owner_full_name?: string; attributes?: Record<string, unknown> }
}

export interface EvidenceLink {
  id: number
  case: number
  evidence_from: number
  evidence_from_title: string
  evidence_to: number
  evidence_to_title: string
  link_type: string
  created_by: number | null
  created_at: string
}

export interface Suspect {
  id: number
  case: number
  case_title: string
  user: number
  user_username: string
  user_full_name?: string
  user_national_id?: string
  status: string
  rejection_message?: string
  proposed_by_detective: number | null
  approved_by_supervisor: number | null
  approved_at: string | null
  marked_at: string
  first_pursuit_date: string
  days_pursued?: number
  crime_degree?: number
  ranking_score?: number
  reward_rials?: number
  interrogations?: Interrogation[]
}

export interface MostWantedItem {
  id: number
  user: number
  user_username: string
  user_full_name: string
  photo: string | null
  case: number
  case_title: string
  days_under_investigation: number
  crime_degree: number
  ranking_score: number
  reward_rials: number
  marked_at: string
}

export interface Interrogation {
  id: number
  suspect: number
  case_id?: number
  detective_probability: number | null
  supervisor_probability: number | null
  captain_decision: string
  captain_decided_by: number | null
  captain_decided_at: string | null
  chief_confirmed: boolean
  chief_confirmed_at: string | null
  notes?: string
  created_at: string
  updated_at: string
}

export interface CaptainDecision {
  id: number
  suspect: number
  case: number
  final_decision: 'guilty' | 'not_guilty'
  reasoning: string
  decided_by: number | null
  created_at: string
}

export interface ChiefApproval {
  id: number
  captain_decision: number
  status: 'approved' | 'rejected'
  comment: string
  approved_by: number | null
  created_at: string
}

export interface Trial {
  id: number
  case: number
  case_title: string
  judge: number | null
  judge_username: string | null
  started_at: string
  closed_at: string | null
}

export interface Verdict {
  id: number
  trial: number
  verdict_type: 'guilty' | 'innocent'
  title: string
  description: string
  punishment_title: string
  punishment_description: string
  recorded_at: string
  recorded_by: number | null
}

export interface TrialFullDetail {
  id: number
  case: number
  judge: number | null
  judge_username: string | null
  started_at: string
  closed_at: string | null
  case_data: Case
  evidence_items: Evidence[]
  crime_scene_report: unknown | null
  complainants: CaseComplainant[]
  suspects: Suspect[]
  arrested_suspect: Suspect | null
  interrogations: Interrogation[]
  captain_decisions: CaptainDecision[]
  verdict: Verdict | null
  personnel: { id: number; username: string; full_name: string; role_names: string[] }[]
}

export interface TrialFullDataByCase {
  case_data: Case
  evidence_items: Evidence[]
  crime_scene_report: unknown | null
  complainants: CaseComplainant[]
  suspects: Suspect[]
  interrogations: Interrogation[]
  captain_decisions: CaptainDecision[]
  chief_approvals: ChiefApproval[]
  personnel: { id: number; username: string; full_name: string; role_names: string[] }[]
  trial: Trial | null
  verdict: Verdict | null
}

export interface RewardVerifyResponse {
  reward: Reward
  user_info: { id: number; username: string; full_name: string; national_id: string } | null
  reward_amount: number
  case_info: { id: number; title: string } | null
  suspect_info: { id: number; case_id: number } | null
  payment_status: 'paid' | 'unpaid'
  payment_record: { id: number; amount_rials: number; paid_at: string; officer_id: number } | null
}

export interface Notification {
  id: number
  title: string
  message: string
  notification_type: string
  related_model: string
  related_id: string
  read: boolean
  created_at: string
}

export interface Statistics {
  cases_total: number
  cases_open: number
  complaints_total: number
  complaints_pending: number
  evidence_total: number
  suspects_total: number
  suspects_high_priority: number
  users_total: number
}

export interface Tip {
  id: number
  submitter: number
  submitter_username: string
  case: number | null
  title: string
  description: string
  status: string
  reviewed_by_officer: number | null
  reviewed_by_detective: number | null
  created_at: string
  updated_at: string
}

export interface Reward {
  id: number
  tip: number | null
  suspect: number | null
  amount_rials: number
  unique_code: string
  recipient_national_id: string
  claimed: boolean
  claimed_at: string | null
  created_at: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

export type ApiSuccess<T> = { success: true; data: T }
