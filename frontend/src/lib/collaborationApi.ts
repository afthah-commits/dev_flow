import { api } from './axios';
import { Comment, Discussion } from '../types/collaboration';

export const collaborationApi = {
  getComments: async (entityType: string, entityId: string) => {
    const res = await api.get(`/comments`, { params: { entity_type: entityType, entity_id: entityId } });
    return res.data as Comment[];
  },
  createComment: async (data: { entity_type: string; entity_id: string; parent_id?: string; content: string }) => {
    const res = await api.post(`/comments`, data);
    return res.data as Comment;
  },
  updateComment: async (commentId: string, content: string) => {
    const res = await api.patch(`/comments/${commentId}`, { content });
    return res.data as Comment;
  },
  deleteComment: async (commentId: string) => {
    await api.delete(`/comments/${commentId}`);
  },
  pinComment: async (commentId: string) => {
    const res = await api.post(`/comments/${commentId}/pin`);
    return res.data as Comment;
  },
  unpinComment: async (commentId: string) => {
    const res = await api.post(`/comments/${commentId}/unpin`);
    return res.data as Comment;
  },
  getReplies: async (commentId: string) => {
    const res = await api.get(`/comments/${commentId}/replies`);
    return res.data as Comment[];
  },
  addReaction: async (commentId: string, reaction: string) => {
    const res = await api.post(`/comments/${commentId}/reactions`, { reaction });
    return res.data;
  },
  removeReaction: async (commentId: string, reaction: string) => {
    await api.delete(`/comments/${commentId}/reactions/${reaction}`);
  },
  createDiscussion: async (projectId: string, data: { title: string; content: string }) => {
    const res = await api.post(`/projects/${projectId}/discussions`, data);
    return res.data as Discussion;
  },
  getDiscussions: async (projectId: string) => {
    const res = await api.get(`/projects/${projectId}/discussions`);
    return res.data as Discussion[];
  }
};
