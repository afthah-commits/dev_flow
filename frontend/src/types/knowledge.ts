export type SpaceVisibility = 'PRIVATE' | 'TEAM' | 'ORGANIZATION';

export interface KnowledgeSpace {
  id: string;
  organization_id: string;
  project_id?: string;
  name: string;
  slug: string;
  description?: string;
  visibility: SpaceVisibility;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeSpaceCreate {
  name: string;
  description?: string;
  visibility?: SpaceVisibility;
  project_id?: string;
}

export type DocumentStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';

export interface KnowledgeDocument {
  id: string;
  organization_id: string;
  space_id: string;
  parent_id?: string;
  title: string;
  slug: string;
  content: string;
  content_format: string;
  status: DocumentStatus;
  is_pinned: boolean;
  version_number: number;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocumentCreate {
  space_id: string;
  parent_id?: string;
  title: string;
  content: string;
  content_format?: string;
  status?: DocumentStatus;
  is_pinned?: boolean;
}

export interface KnowledgeDocumentUpdate {
  title?: string;
  content?: string;
  status?: DocumentStatus;
  is_pinned?: boolean;
  parent_id?: string;
  change_summary?: string;
}

export interface KnowledgeDocumentVersion {
  document_id: string;
  version_number: number;
  title: string;
  content: string;
  created_by: string;
  created_at: string;
  change_summary?: string;
}
