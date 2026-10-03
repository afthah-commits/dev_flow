import { api } from './axios';
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
