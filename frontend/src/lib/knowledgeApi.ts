import { api } from './axios';
import { 
  KnowledgeSpace, 
  KnowledgeSpaceCreate,
  KnowledgeDocument,
  KnowledgeDocumentCreate,
  KnowledgeDocumentUpdate,
  KnowledgeDocumentVersion
} from '../types';

export const knowledgeApi = {
  // Spaces
  getSpaces: async () => {
    const res = await api.get<KnowledgeSpace[]>('/api/v1/knowledge/spaces');
    return res.data;
  },
  getSpace: async (id: string) => {
    const res = await api.get<KnowledgeSpace>(`/api/v1/knowledge/spaces/${id}`);
    return res.data;
  },
  createSpace: async (data: KnowledgeSpaceCreate) => {
    const res = await api.post<KnowledgeSpace>('/api/v1/knowledge/spaces', data);
    return res.data;
  },
  deleteSpace: async (id: string) => {
    await api.delete(`/api/v1/knowledge/spaces/${id}`);
  },

  // Documents
  getDocuments: async (spaceId?: string) => {
    const params = spaceId ? { space_id: spaceId } : {};
    const res = await api.get<KnowledgeDocument[]>('/api/v1/knowledge/documents', { params });
    return res.data;
  },
  getDocument: async (id: string) => {
    const res = await api.get<KnowledgeDocument>(`/api/v1/knowledge/documents/${id}`);
    return res.data;
  },
  createDocument: async (data: KnowledgeDocumentCreate) => {
    const res = await api.post<KnowledgeDocument>('/api/v1/knowledge/documents', data);
    return res.data;
  },
  updateDocument: async (id: string, data: KnowledgeDocumentUpdate) => {
    const res = await api.patch<KnowledgeDocument>(`/api/v1/knowledge/documents/${id}`, data);
    return res.data;
  },
  deleteDocument: async (id: string) => {
    await api.delete(`/api/v1/knowledge/documents/${id}`);
  },
  
  // Versions
  getDocumentVersions: async (id: string) => {
    const res = await api.get<KnowledgeDocumentVersion[]>(`/api/v1/knowledge/documents/${id}/versions`);
    return res.data;
  },
  restoreDocumentVersion: async (id: string, versionId: string) => {
    const res = await api.post<KnowledgeDocument>(`/api/v1/knowledge/documents/${id}/versions/${versionId}/restore`);
    return res.data;
  },
};
