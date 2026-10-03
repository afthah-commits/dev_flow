export type EntityType = 'PROJECT' | 'TASK' | 'SPRINT' | 'RELEASE' | 'DEPLOYMENT' | 'PIPELINE' | 'MILESTONE' | 'DISCUSSION';
export type DiscussionStatus = 'OPEN' | 'RESOLVED' | 'ARCHIVED';

export interface CommentReaction {
  id: string;
  comment_id: string;
  user_id: string;
  reaction: string;
}

export interface Comment {
  id: string;
  organization_id: string;
  author_id: string;
  entity_type: EntityType;
  entity_id: string;
  parent_id?: string;
  content: string;
  is_edited: boolean;
  edited_at?: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  reactions?: CommentReaction[];
}

export interface Discussion {
  id: string;
  organization_id: string;
  project_id: string;
  author_id: string;
  title: string;
  content: string;
  status: DiscussionStatus;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  organization_id: string;
  uploaded_by: string;
  entity_type: EntityType;
  entity_id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  storage_key: string;
  created_at: string;
}
