import { api } from './axios';
import { SearchResultItem } from '../types/search';

export const searchApi = {
  globalSearch: async (query: string, limit: number = 25): Promise<SearchResultItem[]> => {
    // baseURL is already <host>/api/v1 — keep the path base-relative so the
    // resolved URL matches the backend route GET /api/v1/search (Phase 43).
    const res = await api.get<SearchResultItem[]>('/search', { params: { q: query, limit } });
    return res.data;
  }
};
