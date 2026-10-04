import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Folder, CheckSquare, MessageCircle, Server, Rocket, FileText, Bug } from 'lucide-react';
import { searchApi } from '../lib/searchApi';
import { SearchResultItem } from '../types/search';

export function GlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
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
      } catch (err) {
        console.error(err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const getIcon = (type: string) => {
    switch (type) {
      case 'PROJECT': return <Folder className="w-4 h-4 text-indigo-400" />;
      case 'TASK': return <CheckSquare className="w-4 h-4 text-emerald-400" />;
      case 'DISCUSSION': return <MessageCircle className="w-4 h-4 text-blue-400" />;
      case 'ENVIRONMENT': return <Server className="w-4 h-4 text-blue-400" />;
      case 'DEPLOYMENT': return <Rocket className="w-4 h-4 text-orange-400" />;
      case 'DOCUMENT': return <FileText className="w-4 h-4 text-purple-400" />;
      case 'INCIDENT': return <Bug className="w-4 h-4 text-red-400" />;
      default: return <Search className="w-4 h-4 text-gray-400" />;
    }
  };

  const groupedResults = results?.reduce((acc, item) => {
    if (!acc[item.entity_type]) acc[item.entity_type] = [];
    acc[item.entity_type].push(item);
    return acc;
  }, {} as Record<string, SearchResultItem[]>) || {};

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center pt-24 p-4">
      <div className="bg-gray-900 border border-gray-700 w-full max-w-2xl rounded-xl shadow-2xl flex flex-col max-h-[80vh] overflow-hidden">
        <div className="flex items-center px-4 py-3 border-b border-gray-800">
          <Search className="w-5 h-5 text-gray-500 mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search projects, tasks, docs... (Ctrl+K to open)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-white outline-none text-lg"
          />
          <button onClick={() => setIsOpen(false)} className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">ESC</button>
        </div>

        <div className="overflow-y-auto p-2 flex-1">
          {loading && <div className="p-4 text-center text-gray-500">Searching...</div>}
          
          {results && !loading && results.length > 0 && (
            <div className="space-y-4">
              {Object.entries(groupedResults).map(([type, items]) => (
                <div key={type}>
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">{type}</div>
                  {items.map(item => (
                    <button 
                      key={`${item.entity_type}-${item.entity_id}`} 
                      onClick={() => { 
                        // Note: For document we can just navigate to item.url if we set it properly,
                        // but url returned by backend search API isn't exactly the frontend URL.
                        // Wait, Phase 27 spec says url should be like `/knowledge/documents/...` or `/projects/...`
                        navigate(item.url); 
                        setIsOpen(false); 
                      }} 
                      className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded flex flex-col group"
                    >
                      <div className="flex items-center gap-3">
                        {getIcon(item.entity_type)}
                        <span className="text-gray-300 group-hover:text-white font-medium">{item.title}</span>
                      </div>
                      {item.snippet && (
                        <div className="text-xs text-gray-500 mt-1 pl-7 line-clamp-1">{item.snippet}</div>
                      )}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          )}

          {!loading && results && results.length === 0 && (
            <div className="p-4 text-center text-gray-500">No results found for "{query}"</div>
          )}
          
          {!results && !loading && (
            <div className="p-4 space-y-2">
              <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">Commands</div>
              <button onClick={() => { navigate('/projects/new'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Create Project</button>
              <button onClick={() => { navigate('/knowledge'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Knowledge Base</button>
              <button onClick={() => { navigate('/analytics/collaboration'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Analytics</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
