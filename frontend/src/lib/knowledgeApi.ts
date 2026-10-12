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
    const res = await api.get<KnowledgeSpace[]>('/knowledge/spaces');
    return res.data;
  },
  getSpace: async (id: string) => {
    const res = await api.get<KnowledgeSpace>(`/knowledge/spaces/${id}`);
    return res.data;
  },
  createSpace: async (data: KnowledgeSpaceCreate) => {
    const res = await api.post<KnowledgeSpace>('/knowledge/spaces', data);
    return res.data;
  },
  deleteSpace: async (id: string) => {
    await api.delete(`/knowledge/spaces/${id}`);
  },

  // Documents
  getDocuments: async (spaceId?: string) => {
    const params = spaceId ? { space_id: spaceId } : {};
    const res = await api.get<KnowledgeDocument[]>('/knowledge/documents', { params });
    return res.data;
  },
  getDocument: async (id: string) => {
    const res = await api.get<KnowledgeDocument>(`/knowledge/documents/${id}`);
    return res.data;
  },
  createDocument: async (data: KnowledgeDocumentCreate) => {
    const res = await api.post<KnowledgeDocument>('/knowledge/documents', data);
    return res.data;
  },
  updateDocument: async (id: string, data: KnowledgeDocumentUpdate) => {
    const res = await api.patch<KnowledgeDocument>(`/knowledge/documents/${id}`, data);
    return res.data;
  },
  deleteDocument: async (id: string) => {
    await api.delete(`/knowledge/documents/${id}`);
  },
  
  // Versions
  getDocumentVersions: async (id: string) => {
    const res = await api.get<KnowledgeDocumentVersion[]>(`/knowledge/documents/${id}/versions`);
    return res.data;
  },
  restoreDocumentVersion: async (id: string, versionId: string) => {
    const res = await api.post<KnowledgeDocument>(`/knowledge/documents/${id}/versions/${versionId}/restore`);
    return res.data;
  },
};
