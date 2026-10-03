import { api } from './axios';
import { SearchResult } from '../types/search';

export const searchApi = {
  globalSearch: async (query: string) => {
    const res = await api.get('/search', { params: { q: query } });
    return res.data as SearchResult;
  }
};
