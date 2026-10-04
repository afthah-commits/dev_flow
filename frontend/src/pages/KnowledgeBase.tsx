import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Book, FileText, ChevronRight, Settings, Trash, Search, MessageSquare } from 'lucide-react';
import { knowledgeApi } from '../lib/knowledgeApi';
import { aiApi } from '../lib/aiApi';
import { KnowledgeSpace, KnowledgeDocument } from '../types';
import KnowledgeDocumentEditor from '../components/knowledge/KnowledgeDocumentEditor';

export default function KnowledgeBase() {
  const { spaceId, docId } = useParams<{ spaceId: string, docId: string }>();
  const navigate = useNavigate();
  const [spaces, setSpaces] = useState<KnowledgeSpace[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [isSpaceModalOpen, setIsSpaceModalOpen] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState('');
  
  // AI assistant
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [askingAi, setAskingAi] = useState(false);

  useEffect(() => {
    loadSpaces();
  }, []);

  useEffect(() => {
    if (spaceId) {
      loadDocuments(spaceId);
    } else {
      setDocuments([]);
    }
  }, [spaceId]);

  const loadSpaces = async () => {
    try {
      const res = await knowledgeApi.getSpaces();
      setSpaces(res);
      if (res.length > 0 && !spaceId) {
        navigate(`/knowledge/${res[0].id}`);
      }
    } catch (err) {
      console.error('Failed to load spaces', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async (id: string) => {
    try {
      const res = await knowledgeApi.getDocuments(id);
      setDocuments(res);
    } catch (err) {
      console.error('Failed to load documents', err);
    }
  };

  const handleCreateSpace = async () => {
    if (!newSpaceName.trim()) return;
    try {
      const res = await knowledgeApi.createSpace({ name: newSpaceName });
      setSpaces([...spaces, res]);
      setIsSpaceModalOpen(false);
      setNewSpaceName('');
      navigate(`/knowledge/${res.id}`);
    } catch (err) {
      console.error('Failed to create space', err);
    }
  };

  const handleCreateDocument = async () => {
    if (!spaceId) return;
    try {
      const res = await knowledgeApi.createDocument({
        space_id: spaceId,
        title: 'Untitled Document',
        content: '# Untitled\n\nStart typing...'
      });
      setDocuments([...documents, res]);
      navigate(`/knowledge/${spaceId}/doc/${res.id}`);
    } catch (err) {
      console.error('Failed to create document', err);
    }
  };

  const handleAskAi = async () => {
    if (!aiQuery.trim()) return;
    setAskingAi(true);
    setAiResponse('');
    try {
      const res = await aiApi.askKnowledge(aiQuery, spaceId);
      setAiResponse(res.answer);
    } catch (err) {
      setAiResponse('Sorry, an error occurred while searching the knowledge base.');
    } finally {
      setAskingAi(false);
    }
  };

  if (loading) return <div className="flex h-screen items-center justify-center text-white">Loading Knowledge Base...</div>;

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden pt-16">
      {/* Sidebar - Spaces */}
      <div className="w-64 border-r border-gray-800 bg-gray-900/50 flex flex-col">
        <div className="p-4 border-b border-gray-800 flex justify-between items-center">
          <h2 className="font-semibold flex items-center gap-2">
            <Book className="w-4 h-4 text-indigo-400" />
            Spaces
          </h2>
          <button onClick={() => setIsSpaceModalOpen(true)} className="p-1 hover:bg-gray-800 rounded">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {spaces.map(s => (
            <button
              key={s.id}
              onClick={() => navigate(`/knowledge/${s.id}`)}
              className={`w-full text-left px-3 py-2 rounded flex items-center gap-2 ${
                s.id === spaceId ? 'bg-indigo-500/10 text-indigo-400' : 'hover:bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              <div className="truncate flex-1">{s.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Sidebar - Documents Tree */}
      {spaceId && (
        <div className="w-72 border-r border-gray-800 bg-gray-900 flex flex-col">
          <div className="p-4 border-b border-gray-800 flex justify-between items-center">
            <h3 className="font-semibold text-sm">Documents</h3>
            <button onClick={handleCreateDocument} className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              <Plus className="w-3 h-3" /> New
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {documents.filter(d => !d.parent_id).map(doc => (
              <div key={doc.id}>
                <button
                  onClick={() => navigate(`/knowledge/${spaceId}/doc/${doc.id}`)}
                  className={`w-full text-left px-3 py-1.5 rounded flex items-center gap-2 text-sm ${
                    doc.id === docId ? 'bg-indigo-500/10 text-indigo-400' : 'hover:bg-gray-800 text-gray-300'
                  }`}
                >
                  <FileText className="w-3 h-3 flex-shrink-0" />
                  <span className="truncate">{doc.title}</span>
                </button>
                {/* Render one level of children for simplicity in this demo */}
                {documents.filter(d => d.parent_id === doc.id).map(child => (
                  <button
                    key={child.id}
                    onClick={() => navigate(`/knowledge/${spaceId}/doc/${child.id}`)}
                    className={`w-full text-left pl-8 pr-3 py-1.5 rounded flex items-center gap-2 text-sm ${
                      child.id === docId ? 'bg-indigo-500/10 text-indigo-400' : 'hover:bg-gray-800 text-gray-400'
                    }`}
                  >
                    <FileText className="w-3 h-3 flex-shrink-0 opacity-50" />
                    <span className="truncate">{child.title}</span>
                  </button>
                ))}
              </div>
            ))}
            {documents.length === 0 && (
              <div className="p-4 text-center text-gray-500 text-sm">No documents in this space.</div>
            )}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-gray-950 overflow-hidden relative">
        {docId ? (
          <KnowledgeDocumentEditor 
            docId={docId} 
            key={docId} 
            onUpdate={() => spaceId && loadDocuments(spaceId)} 
            onDelete={() => navigate(`/knowledge/${spaceId}`)}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 space-y-4 p-8">
            <Book className="w-16 h-16 text-gray-800" />
            <h2 className="text-xl font-semibold text-gray-300">Welcome to Knowledge Base</h2>
            <p className="max-w-md text-center text-gray-400">
              Select a space on the left to browse documents, or create a new space to organize your engineering documentation.
            </p>
            {spaceId && (
              <button 
                onClick={handleCreateDocument}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md mt-4"
              >
                Create First Document
              </button>
            )}
          </div>
        )}

        {/* AI Assistant Overlay (Bottom Right) */}
        <div className="absolute bottom-6 right-6 w-80 bg-gray-900 border border-gray-800 rounded-xl shadow-2xl flex flex-col overflow-hidden">
          <div className="px-4 py-2 bg-indigo-900/30 border-b border-indigo-900/50 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-medium text-indigo-300">Ask Knowledge AI</span>
          </div>
          {aiResponse && (
            <div className="p-3 text-sm text-gray-300 border-b border-gray-800 max-h-64 overflow-y-auto bg-gray-900/80">
              {aiResponse}
            </div>
          )}
          <div className="p-3 flex gap-2">
            <input 
              type="text" 
              value={aiQuery}
              onChange={e => setAiQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAskAi()}
              placeholder="Ask a question..."
              className="flex-1 bg-gray-950 border border-gray-800 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
            <button 
              onClick={handleAskAi}
              disabled={askingAi}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded text-sm font-medium"
            >
              {askingAi ? '...' : 'Ask'}
            </button>
          </div>
        </div>
      </div>

      {/* New Space Modal */}
      {isSpaceModalOpen && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-lg max-w-md w-full p-6 border border-gray-700">
            <h3 className="text-lg font-medium text-white mb-4">Create New Space</h3>
            <input
              type="text"
              value={newSpaceName}
              onChange={e => setNewSpaceName(e.target.value)}
              placeholder="Space Name (e.g., Engineering Handbook)"
              className="w-full bg-gray-950 border border-gray-700 rounded px-3 py-2 text-white mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button onClick={() => setIsSpaceModalOpen(false)} className="px-4 py-2 text-gray-400 hover:text-white">Cancel</button>
              <button onClick={handleCreateSpace} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded">Create Space</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
