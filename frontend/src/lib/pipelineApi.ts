import { api } from './axios';
import { PipelineRun } from '../types/pipeline';

export const pipelineApi = {
  list: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/pipelines`);
    return res.data as PipelineRun[];
  },
  run: async (projectId: string, data: { provider?: string; branch?: string; commit_sha?: string; workflow_name?: string }) => {
    const res = await api.post(`/projects/${projectId}/pipelines/run`, data);
    return res.data as PipelineRun;
  }
};
