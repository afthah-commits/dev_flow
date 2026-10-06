import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Folder, CheckSquare, MessageCircle, FileText, Users, Workflow as WorkflowIcon, Building2, Bell } from 'lucide-react';
import { searchApi } from '../lib/searchApi';
import { SearchResultItem } from '../types/search';

export function GlobalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
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
      setError(false);
      setLoading(false);
      return;
    }
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const res = await searchApi.globalSearch(query);
        setResults(res);
        setActiveIndex(0);
        setError(false);
      } catch {
        // Never surface raw backend errors; show the error state instead.
        setError(true);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const openResult = useCallback((item: SearchResultItem) => {
    navigate(item.url);
    setIsOpen(false);
    setQuery('');
  }, [navigate]);

  const flatResults = results ?? [];
  const groupedResults = flatResults.reduce((acc, item) => {
    if (!acc[item.entity_type]) acc[item.entity_type] = [];
    acc[item.entity_type].push(item);
    return acc;
  }, {} as Record<string, SearchResultItem[]>);

  const groupedEntries = Object.entries(groupedResults);
  // Flat index across groups for keyboard navigation.
  const flatIndexed = groupedEntries.flatMap(([, items]) => items);

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(i => Math.min(i + 1, Math.max(flatIndexed.length - 1, 0)));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(i => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const item = flatIndexed[activeIndex];
      if (item) openResult(item);
    }
  };

  // Keep the active row in view during keyboard navigation.
  useEffect(() => {
    const el = listRef.current?.querySelector('[data-active="true"]');
    el?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  if (!isOpen) return null;

  let renderedIndex = -1;

  const getIcon = (type: string) => {
    switch (type) {
      case 'PROJECT': return <Folder className="w-4 h-4 text-indigo-400" />;
      case 'TASK': return <CheckSquare className="w-4 h-4 text-emerald-400" />;
      case 'DISCUSSION': return <MessageCircle className="w-4 h-4 text-blue-400" />;
      case 'DOCUMENT': return <FileText className="w-4 h-4 text-purple-400" />;
      case 'CLIENT': return <Building2 className="w-4 h-4 text-amber-400" />;
      case 'WORKFLOW': return <WorkflowIcon className="w-4 h-4 text-sky-400" />;
      case 'MEMBER': return <Users className="w-4 h-4 text-pink-400" />;
      case 'NOTIFICATION': return <Bell className="w-4 h-4 text-yellow-400" />;
      default: return <Search className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center pt-24 p-4">
      <div
        className="bg-gray-900 border border-gray-700 w-full max-w-2xl rounded-xl shadow-2xl flex flex-col max-h-[80vh] overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Global search"
      >
        <div className="flex items-center px-4 py-3 border-b border-gray-800">
          <Search className="w-5 h-5 text-gray-500 mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search projects, tasks, docs... (Ctrl+K to open)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleInputKeyDown}
            aria-label="Search"
            className="flex-1 bg-transparent text-white outline-none text-lg"
          />
          <button onClick={() => setIsOpen(false)} className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">ESC</button>
        </div>

        <div className="overflow-y-auto p-2 flex-1" ref={listRef}>
          {loading && <div className="p-4 text-center text-gray-500" role="status">Searching…</div>}

          {error && !loading && (
            <div className="p-4 text-center text-red-400" role="status">
              Search is temporarily unavailable. Please try again.
            </div>
          )}

          {!error && !loading && results && flatResults.length > 0 && (
            <div className="space-y-4">
              {groupedEntries.map(([type, items]) => (
                <div key={type}>
                  <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">{type}</div>
                  {items.map(item => {
                    renderedIndex += 1;
                    const idx = renderedIndex;
                    return (
                      <button
                        key={`${item.entity_type}-${item.entity_id}`}
                        data-active={idx === activeIndex || undefined}
                        onClick={() => openResult(item)}
                        onMouseEnter={() => setActiveIndex(idx)}
                        className={`w-full text-left px-3 py-2 rounded flex flex-col group ${
                          idx === activeIndex ? 'bg-gray-800' : 'hover:bg-gray-800'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {getIcon(item.entity_type)}
                          <span className="text-gray-300 group-hover:text-white font-medium">{item.title}</span>
                          {item.matched_field && (
                            <span className="ml-auto text-[10px] uppercase text-gray-600">{item.matched_field}</span>
                          )}
                        </div>
                        {item.snippet && (
                          <div className="text-xs text-gray-500 mt-1 pl-7 line-clamp-1">{item.snippet}</div>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          )}

          {!error && !loading && results && flatResults.length === 0 && (
            <div className="p-4 text-center text-gray-500" role="status">
              No results found for &quot;{query}&quot;
            </div>
          )}

          {!results && !loading && !error && (
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
