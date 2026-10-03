export interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface AIConversation {
  id: string;
  user_id: string;
  project_id?: string;
  title: string;
  created_at: string;
  updated_at?: string;
  messages?: AIMessage[];
}

export interface TaskSuggestion {
  title: string;
  description: string;
  priority: string;
  labels: string[];
}

export interface TaskBreakdown {
  subtasks: TaskSuggestion[];
}

export interface AIActionResponse {
  result: string;
  structured_data?: any;
}
