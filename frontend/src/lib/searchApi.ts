import { api } from './axios';
import { SearchResultItem } from '../types/search';

export const searchApi = {
  globalSearch: async (query: string) => {
    const res = await api.get<SearchResultItem[]>('/api/v1/search', { params: { q: query } });
    return res.data;
  }
};
