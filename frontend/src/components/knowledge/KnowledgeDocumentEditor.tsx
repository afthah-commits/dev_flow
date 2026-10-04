import React, { useState, useEffect } from 'react';
import { Save, Clock, FileText, Trash, ChevronDown } from 'lucide-react';
import { knowledgeApi } from '../../lib/knowledgeApi';
import { KnowledgeDocument, KnowledgeDocumentVersion } from '../../types';

interface Props {
  docId: string;
  onUpdate: () => void;
  onDelete: () => void;
}

export default function KnowledgeDocumentEditor({ docId, onUpdate, onDelete }: Props) {
  const [doc, setDoc] = useState<KnowledgeDocument | null>(null);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [versions, setVersions] = useState<KnowledgeDocumentVersion[]>([]);
  const [showVersions, setShowVersions] = useState(false);

  useEffect(() => {
    loadDoc();
  }, [docId]);

  const loadDoc = async () => {
    try {
      const res = await knowledgeApi.getDocument(docId);
      setDoc(res);
      setTitle(res.title);
      setContent(res.content);
      
      const vRes = await knowledgeApi.getDocumentVersions(docId);
      setVersions(vRes);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async (summary?: string) => {
    setSaving(true);
    try {
      const res = await knowledgeApi.updateDocument(docId, {
        title,
        content,
        change_summary: summary || 'Auto-save update'
      });
      setDoc(res);
      setLastSaved(new Date());
      onUpdate();
      
      const vRes = await knowledgeApi.getDocumentVersions(docId);
      setVersions(vRes);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async (versionId: string) => {
    if (!confirm('Are you sure you want to restore this version?')) return;
    try {
      await knowledgeApi.restoreDocumentVersion(docId, versionId);
      loadDoc();
      onUpdate();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await knowledgeApi.deleteDocument(docId);
      onDelete();
    } catch (err) {
      console.error(err);
    }
  };

  if (!doc) return <div className="flex-1 p-8 text-gray-500">Loading document...</div>;

  return (
    <div className="flex-1 flex flex-col h-full bg-gray-950 overflow-hidden">
      {/* Editor Header */}
      <div className="flex-none p-4 border-b border-gray-800 bg-gray-900/50 flex justify-between items-center">
        <div className="flex-1 mr-4">
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            onBlur={() => title !== doc.title && handleSave('Updated title')}
            className="w-full bg-transparent text-xl font-semibold text-white outline-none focus:border-b focus:border-gray-600 pb-1"
            placeholder="Document Title"
          />
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            {saving ? 'Saving...' : lastSaved ? `Saved ${lastSaved.toLocaleTimeString()}` : ''}
          </span>
          <button onClick={() => handleSave('Manual save')} className="p-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded shadow-sm">
            <Save className="w-4 h-4" />
          </button>
          
          <div className="relative">
            <button onClick={() => setShowVersions(!showVersions)} className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded shadow-sm flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span className="text-xs">v{doc.version_number}</span>
            </button>
            
            {showVersions && (
              <div className="absolute right-0 mt-2 w-72 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-10 overflow-hidden">
                <div className="p-2 border-b border-gray-700 bg-gray-800 text-sm font-medium">Version History</div>
                <div className="max-h-64 overflow-y-auto">
                  {versions.map(v => (
                    <div key={v.version_number} className="p-3 border-b border-gray-800 hover:bg-gray-800/50">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-sm text-gray-200">Version {v.version_number}</span>
                        <span className="text-xs text-gray-500">{new Date(v.created_at).toLocaleString()}</span>
                      </div>
                      <div className="text-xs text-gray-400 mb-2">{v.change_summary || 'No summary'}</div>
                      {v.version_number !== doc.version_number && (
                        <button 
                          onClick={() => handleRestore(v.version_number.toString())}
                          className="text-xs text-indigo-400 hover:text-indigo-300"
                        >
                          Restore this version
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <button onClick={handleDelete} className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-800 rounded">
            <Trash className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Editor Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Simple markdown raw editor (left) */}
        <div className="flex-1 border-r border-gray-800 p-4 overflow-y-auto bg-gray-900/30">
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            onBlur={() => content !== doc.content && handleSave()}
            className="w-full h-full bg-transparent text-gray-300 outline-none resize-none font-mono text-sm leading-relaxed"
            placeholder="Write markdown here..."
          />
        </div>
        
        {/* Simple markdown preview (right) */}
        <div className="flex-1 p-6 overflow-y-auto bg-gray-950 prose prose-invert prose-indigo max-w-none">
          <div dangerouslySetInnerHTML={{ 
            // In a real app we'd use marked or similar, here we just do a very basic transform for demo
            __html: content
              .replace(/^# (.*$)/gim, '<h1>$1</h1>')
              .replace(/^## (.*$)/gim, '<h2>$1</h2>')
              .replace(/^### (.*$)/gim, '<h3>$1</h3>')
              .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
              .replace(/\n$/gim, '<br />') 
          }} />
        </div>
      </div>
    </div>
  );
}
