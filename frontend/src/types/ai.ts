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

// --- Phase 47: AI-assisted planning & estimation (advisory only) ---
export interface AIPlanningSuggestion {
  title: string;
  description: string;
  priority: string;
}

export interface AIPlanningCapacity {
  status: 'OK' | 'OVER_CAPACITY' | 'INSUFFICIENT_DATA';
  sprint_id?: string;
  sprint_name?: string;
  capacity_points?: number;
  committed_points?: number;
  remaining_points?: number;
}

export interface AIPlanningAnalysis {
  task_id?: string;
  project_id: string;
  complexity: 'LOW' | 'MEDIUM' | 'HIGH';
  complexity_factors: string[];
  estimate_points: number;
  estimate_confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  estimate_factors: string[];
  risks: string[];
  missing_information: string[];
  dependency_concerns: string[];
  suggested_breakdown: AIPlanningSuggestion[];
  capacity?: AIPlanningCapacity;
  advisory: boolean;
  provider: string;
}
