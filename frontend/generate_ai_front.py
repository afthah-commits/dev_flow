import os

os.makedirs("c:/personal_projects/devflow/frontend/src/types", exist_ok=True)

ai_types = """export interface AIMessage {
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
"""
with open("c:/personal_projects/devflow/frontend/src/types/ai.ts", "w") as f: f.write(ai_types)

ai_api = """import { api } from './axios';
import { AIConversation, AIMessage, AIActionResponse, TaskSuggestion, TaskBreakdown } from '../types/ai';

export const aiApi = {
  listConversations: async (projectId?: string): Promise<AIConversation[]> => {
    const res = await api.get('/ai/conversations', { params: { project_id: projectId } });
    return res.data;
  },
  createConversation: async (title: string, projectId?: string): Promise<AIConversation> => {
    const res = await api.post('/ai/conversations', { title, project_id: projectId });
    return res.data;
  },
  getConversation: async (id: string): Promise<AIConversation> => {
    const res = await api.get(`/ai/conversations/${id}`);
    return res.data;
  },
  deleteConversation: async (id: string): Promise<void> => {
    await api.delete(`/ai/conversations/${id}`);
  },
  sendMessage: async (conversationId: string, message: string): Promise<AIMessage> => {
    const res = await api.post(`/ai/conversations/${conversationId}/messages`, { message });
    return res.data;
  },
  
  // Quick Actions
  suggestTask: async (projectId: string, instruction: string): Promise<AIActionResponse> => {
    const res = await api.post(`/ai/projects/${projectId}/actions/task-suggestion`, { instruction });
    return res.data;
  },
  breakdownTask: async (projectId: string, taskId: string): Promise<AIActionResponse> => {
    const res = await api.post(`/ai/projects/${projectId}/actions/task-breakdown`, { task_id: taskId });
    return res.data;
  }
};
"""
with open("c:/personal_projects/devflow/frontend/src/lib/aiApi.ts", "w") as f: f.write(ai_api)

print("AI Types and API created")
