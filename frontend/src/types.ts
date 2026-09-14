export type Role = 'patient' | 'provider' | 'admin'

export interface Org {
  id: number
  name: string
  slug: string
  subscription_tier: string
}

export interface Provider {
  user_id: number
  display_name: string
  email: string
  specialties: string[]
  city: string
  region: string
  weekly_capacity: number
  remaining_slots: number
  accepted_tiers: string[]
  bio: string
}

export interface Patient {
  user_id: number
  display_name: string
  preferred_specialties: string[]
  city: string
  region: string
  access_tier: string
}

export interface UserMe {
  id: number
  email: string
  display_name: string
  role: Role
  organization: Org
  patient: Patient | null
  provider: Provider | null
}

export interface Persona {
  email: string
  password: string
  role: Role
  display_name: string
  org_slug: string
  org_name: string
}

export interface ScoreBreakdown {
  specialty: number
  location: number
  tier: number
  availability: number
  weights: Record<string, number>
}

export interface MatchResult {
  provider: Provider
  score: number
  breakdown: ScoreBreakdown
}

export interface MatchResponse {
  patient: Patient
  results: MatchResult[]
  formula: string
}

export interface Appointment {
  id: number
  scheduled_for: string
  status: string
}

export interface MatchRequest {
  id: number
  org_id: number
  patient_user_id: number
  patient_name: string
  provider_user_id: number
  provider_name: string
  score: number
  status: string
  notes: string
  created_at: string
  appointment: Appointment | null
}

export interface TenantSummary {
  organization: Org
  patient_count: number
  provider_count: number
  admin_count: number
  open_requests: number
  accepted_requests: number
  scheduled_requests: number
  specialties_offered: string[]
}

export interface AuditLog {
  id: number
  method: string
  path: string
  status_code: number
  actor_user_id: number | null
  org_id: number | null
  duration_ms: number
  created_at: string
}
