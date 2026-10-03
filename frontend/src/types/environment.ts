export interface Environment {
  id: string;
  organization_id: string;
  project_id: string;
  name: string;
  url?: string;
  branch?: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}
