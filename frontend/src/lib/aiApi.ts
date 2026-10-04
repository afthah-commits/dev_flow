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
  },
  getProjectSummary: async (projectId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/summary`);
    return res.data;
  },
  getProjectRisks: async (projectId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/risks`);
    return res.data;
  },
  getTaskPrioritization: async (projectId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/prioritize`);
    return res.data;
  },
  getSprintPlan: async (projectId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/sprint-plan`);
    return res.data;
  },
  getGitHubSummary: async (projectId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/github/summary`);
    return res.data;
  },
  getReleaseAnalysis: async (releaseId: string) => {
    const res = await api.post(`/ai/releases/${releaseId}/analysis`);
    return res.data;
  },
  getDeploymentAnalysis: async (projectId: string) => {
    const res = await api.post(`/ai/projects/${projectId}/deployment-analysis`);
    return res.data;
  },
  getDailyBrief: async (projectId: string) => {
    const res = await api.get(`/ai/projects/${projectId}/daily-brief`);
    return res.data;
  },
  getUsage: async () => {
    const res = await api.get('/ai/usage');
    return res.data;
  },
  // Phase 26
  getForecast: async (projectId: string) => {
    const res = await api.get(`/ai/projects/${projectId}/forecast`);
    return res.data;
  },
  getRiskEngine: async (projectId: string) => {
    const res = await api.get(`/ai/projects/${projectId}/risk-engine`);
    return res.data;
  },
  getSmartSprintPlan: async (projectId: string) => {
    const res = await api.get(`/ai/projects/${projectId}/sprint-planning`);
    return res.data;
  },
  getHealthReport: async (projectId: string) => {
    const res = await api.get(`/ai/projects/${projectId}/health-report`);
    return res.data;
  },
  getOrgDailyBrief: async () => {
    const res = await api.get(`/ai/daily-brief`);
    return res.data;
  },
  getTaskPriorities: async (projectId: string) => {
    const res = await api.get(`/ai/projects/${projectId}/task-priorities`);
    return res.data;
  },
  askKnowledge: async (question: string, spaceId?: string) => {
    const payload: any = { question };
    if (spaceId) payload.space_id = spaceId;
    const res = await api.post(`/ai/knowledge/ask`, payload);
    return res.data;
  },
  summarizeKnowledgeDocument: async (documentId: string) => {
    const res = await api.post(`/ai/knowledge/documents/${documentId}/summary`);
    return res.data;
  }
};



