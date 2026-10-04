import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Folder, CheckSquare, MessageCircle, Server, Rocket } from 'lucide-react';
import { searchApi } from '../lib/searchApi';
import { SearchResult } from '../types/search';

export function GlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults(null);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchApi.globalSearch(query);
        setResults(res);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center pt-24 p-4">
      <div className="bg-gray-900 border border-gray-700 w-full max-w-2xl rounded-xl shadow-2xl flex flex-col max-h-[80vh] overflow-hidden">
        <div className="flex items-center px-4 py-3 border-b border-gray-800">
          <Search className="w-5 h-5 text-gray-500 mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search projects, tasks, discussions... (Ctrl+K to open)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-white outline-none text-lg"
          />
          <button onClick={() => setIsOpen(false)} className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">ESC</button>
        </div>

        <div className="overflow-y-auto p-2 flex-1">
          {loading && <div className="p-4 text-center text-gray-500">Searching...</div>}
          
          {results && !loading && (
            <div className="space-y-4">
              {results.projects.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">Projects</div>
                  {results.projects.map(p => (
                    <button key={p.id} onClick={() => { navigate(`/projects/${p.id}`); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded flex items-center gap-3 group">
                      <Folder className="w-4 h-4 text-indigo-400" />
                      <span className="text-gray-300 group-hover:text-white">{p.title}</span>
                    </button>
                  ))}
                </div>
              )}
              
              {results.tasks.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">Tasks</div>
                  {results.tasks.map(t => (
                    <button key={t.id} onClick={() => { navigate(`/projects/${t.project_id}?task=${t.id}`); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded flex items-center gap-3 group">
                      <CheckSquare className="w-4 h-4 text-emerald-400" />
                      <span className="text-gray-300 group-hover:text-white">{t.title}</span>
                    </button>
                  ))}
                </div>
              )}

              {results.discussions.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">Discussions</div>
                  {results.discussions.map(d => (
                    <button key={d.id} onClick={() => { navigate(`/projects/${d.project_id}`); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded flex items-center gap-3 group">
                      <MessageCircle className="w-4 h-4 text-blue-400" />
                      <span className="text-gray-300 group-hover:text-white">{d.title}</span>
                    </button>
                  ))}
                </div>
              )}

              {!loading && results.projects.length === 0 && results.tasks.length === 0 && results.discussions.length === 0 && (
                <div className="p-4 text-center text-gray-500">No results found for "{query}"</div>
              )}
            </div>
          )}
          
          {!results && !loading && (
            <div className="p-4 space-y-2">
              <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">Commands</div>
              <button onClick={() => { navigate('/projects/new'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Create Project</button>
              <button onClick={() => { navigate('/projects'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Projects</button>
              <button onClick={() => { navigate('/analytics/collaboration'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Analytics</button>
              <button onClick={() => { navigate('/settings/notifications'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Notifications</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
