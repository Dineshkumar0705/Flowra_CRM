export type UserRole = "super_admin" | "admin" | "manager" | "sales" | "viewer";
export type WorkspacePlan = "free" | "starter" | "pro" | "enterprise";
export type ContactSource =
  | "manual"
  | "import"
  | "whatsapp"
  | "gmail"
  | "web_form"
  | "referral";
export type LeadStatus = "new" | "contacted" | "qualified" | "converted" | "lost";
export type DealPriority = "low" | "medium" | "high" | "urgent";
export type TaskStatus   = "todo" | "in_progress" | "done" | "cancelled";
export type TaskPriority = "low" | "medium" | "high" | "urgent";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar_url?: string;
  created_at?: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  plan: WorkspacePlan;
  owner_id: string;
  created_at?: string;
}

export interface Contact {
  id: string;
  workspace_id: string;
  first_name: string;
  last_name?: string;
  email?: string;
  phone?: string;
  whatsapp_number?: string;
  company_name?: string;
  job_title?: string;
  source: ContactSource;
  lead_status: LeadStatus;
  tags: string[];
  lead_score: number;
  custom_fields?: Record<string, any>;
  avatar_url?: string;
  last_contacted_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  workspace_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_at?: string;
  completed_at?: string;
  contact_id?: string;
  deal_id?: string;
  assigned_to?: string;
  created_by?: string;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskSummary {
  total: number;
  todo: number;
  in_progress: number;
  done: number;
  overdue: number;
}

export interface Deal {
  id: string;
  workspace_id: string;
  title: string;
  value?: number;
  stage: string;
  priority: DealPriority;
  contact_id?: string;
  pipeline_id: string;
  stage_id: string;
  notes?: string;
  created_at: string;
}

export interface Stage {
  id: string;
  name: string;
  position: number;
  color?: string;
}

export interface Pipeline {
  id: string;
  name: string;
  stages: Stage[];
  description?: string;
  created_at?: string;
}

export interface Notification {
  id: string;
  title: string;
  body: string;
  type: string;
  read: boolean;
  created_at: string;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  meta?: PaginationMeta | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  workspace: Workspace;
}

export interface DashboardData {
  total_contacts: number;
  total_deals: number;
  total_revenue: number;
  win_rate: number;
  monthly_revenue: Array<{
    month: string;
    revenue: number;
  }>;
  deals_by_stage: Array<{
    stage: string;
    count: number;
    value: number;
  }>;
}

export interface DealsDashboard {
  total_value: number;
  deals_by_stage: Array<{
    stage: string;
    count: number;
    value: number;
  }>;
  monthly_revenue: Array<{
    month: string;
    revenue: number;
  }>;
  win_rate: number;
}
