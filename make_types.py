import os

os.makedirs('frontend/src/types', exist_ok=True)
os.makedirs('frontend/src/lib', exist_ok=True)
os.makedirs('frontend/src/hooks', exist_ok=True)

types_collab = '''export type EntityType = 'PROJECT' | 'TASK' | 'SPRINT' | 'RELEASE' | 'DEPLOYMENT' | 'PIPELINE' | 'MILESTONE' | 'DISCUSSION';
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
'''
with open('frontend/src/types/collaboration.ts', 'w', encoding='utf-8') as f: f.write(types_collab)

types_search = '''export interface SearchResult {
  projects: any[];
  tasks: any[];
  discussions: any[];
  users: any[];
  sprints: any[];
  releases: any[];
}
'''
with open('frontend/src/types/search.ts', 'w', encoding='utf-8') as f: f.write(types_search)

api_collab = '''import { api } from './axios';
import { Comment, Discussion } from '../types/collaboration';

export const collaborationApi = {
  getComments: async (entityType: string, entityId: string) => {
    const res = await api.get(/comments, { params: { entity_type: entityType, entity_id: entityId } });
    return res.data as Comment[];
  },
  createComment: async (data: { entity_type: string; entity_id: string; parent_id?: string; content: string }) => {
    const res = await api.post(/comments, data);
    return res.data as Comment;
  },
  updateComment: async (commentId: string, content: string) => {
    const res = await api.patch(/comments/\, { content });
    return res.data as Comment;
  },
  deleteComment: async (commentId: string) => {
    await api.delete(/comments/\);
  },
  pinComment: async (commentId: string) => {
    const res = await api.post(/comments/\/pin);
    return res.data as Comment;
  },
  unpinComment: async (commentId: string) => {
    const res = await api.post(/comments/\/unpin);
    return res.data as Comment;
  },
  getReplies: async (commentId: string) => {
    const res = await api.get(/comments/\/replies);
    return res.data as Comment[];
  },
  addReaction: async (commentId: string, reaction: string) => {
    const res = await api.post(/comments/\/reactions, { reaction });
    return res.data;
  },
  removeReaction: async (commentId: string, reaction: string) => {
    await api.delete(/comments/\/reactions/\);
  },
  createDiscussion: async (projectId: string, data: { title: string; content: string }) => {
    const res = await api.post(/projects/\/discussions, data);
    return res.data as Discussion;
  },
  getDiscussions: async (projectId: string) => {
    const res = await api.get(/projects/\/discussions);
    return res.data as Discussion[];
  }
};
'''
with open('frontend/src/lib/collaborationApi.ts', 'w', encoding='utf-8') as f: f.write(api_collab)

api_search = '''import { api } from './axios';
import { SearchResult } from '../types/search';

export const searchApi = {
  globalSearch: async (query: string) => {
    const res = await api.get('/search', { params: { q: query } });
    return res.data as SearchResult;
  }
};
'''
with open('frontend/src/lib/searchApi.ts', 'w', encoding='utf-8') as f: f.write(api_search)

hooks_ws = '''import { useEffect, useState, useRef } from 'react';
import { useAuth } from './useAuth';

export function useRealtime(orgId?: string) {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token || !orgId) return;

    // Use standard WS URL (in real app replace with env var)
    const wsUrl = ws://localhost:8000/api/v1/ws?token=\&org_id=\;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = (e) => console.error("WS Error:", e);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Dispatch custom event so components can listen globally
        window.dispatchEvent(new CustomEvent('realtime_event', { detail: data }));
      } catch(e) {}
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [token, orgId]);

  return { isConnected };
}
'''
with open('frontend/src/hooks/useRealtime.ts', 'w', encoding='utf-8') as f: f.write(hooks_ws)

print("Files created successfully.")
