import React, { useEffect, useState } from 'react';
import { collaborationApi } from '../lib/collaborationApi';
import { Discussion } from '../types/collaboration';
import { MessageCircle, Plus, Search } from 'lucide-react';
import CommentThread from '../components/CommentThread';
import { useAuth } from '../hooks/useAuth';

export default function ProjectDiscussions({ projectId }: { projectId: string }) {
  const [discussions, setDiscussions] = useState<Discussion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [activeDisc, setActiveDisc] = useState<Discussion | null>(null);
  const [formData, setFormData] = useState({ title: '', content: '' });

  const loadDiscussions = () => {
    collaborationApi.getDiscussions(projectId)
      .then(setDiscussions)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDiscussions();
  }, [projectId]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await collaborationApi.createDiscussion(projectId, formData);
    setShowForm(false);
    setFormData({ title: '', content: '' });
    loadDiscussions();
  };

  if (activeDisc) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 border-b border-gray-800 pb-4">
          <button onClick={() => setActiveDisc(null)} className="text-gray-400 hover:text-white px-3 py-1 bg-gray-800 rounded">
            Back
          </button>
          <div>
            <h2 className="text-2xl font-bold text-white">{activeDisc.title}</h2>
            <p className="text-sm text-gray-500">Status: {activeDisc.status} • {new Date(activeDisc.created_at).toLocaleString()}</p>
          </div>
        </div>
        
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-8 text-gray-200">
          {activeDisc.content}
        </div>

        <CommentThread entityType="DISCUSSION" entityId={activeDisc.id} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-blue-400" />
          Discussions
        </h2>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded flex items-center gap-1 text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> New Discussion
        </button>
      </div>

      <div className="space-y-3">
        {discussions.length === 0 && !loading && (
          <div className="p-8 text-center text-gray-500 bg-gray-900 border border-gray-800 rounded-lg">
            No discussions found. Start one!
          </div>
        )}
        
        {discussions.map(d => (
          <div 
            key={d.id} 
            onClick={() => setActiveDisc(d)}
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 cursor-pointer hover:border-blue-500/50 transition-colors"
          >
            <h3 className="text-lg font-medium text-white mb-1">{d.title}</h3>
            <p className="text-sm text-gray-400 line-clamp-2">{d.content}</p>
            <div className="mt-3 text-xs text-gray-500 flex items-center gap-4">
              <span>{new Date(d.created_at).toLocaleString()}</span>
              <span className={`px-2 py-0.5 rounded ${
                d.status === 'OPEN' ? 'bg-green-500/10 text-green-400' : 'bg-gray-800'
              }`}>{d.status}</span>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-2xl shadow-xl">
            <h3 className="text-lg font-bold text-white mb-4">Start Discussion</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Title</label>
                <input required type="text" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Content</label>
                <textarea required rows={6} value={formData.content} onChange={e => setFormData({...formData, content: e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white" />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded">Post Discussion</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
