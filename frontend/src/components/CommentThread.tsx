import React, { useEffect, useState } from 'react';
import { collaborationApi } from '../lib/collaborationApi';
import { Comment, EntityType } from '../types/collaboration';
import { MessageSquare, Send, ThumbsUp, MoreVertical, Edit2, Trash2, Pin } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface CommentThreadProps {
  entityType: EntityType;
  entityId: string;
}

export default function CommentThread({ entityType, entityId }: CommentThreadProps) {
  const { user } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  const loadComments = () => {
    collaborationApi.getComments(entityType, entityId)
      .then(setComments)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (entityId) loadComments();
    
    const handleWs = (e: any) => {
       // if we had detailed event payload we could just append, but we can also just reload
       // if (e.detail.type === 'COMMENT_CREATED' && e.detail.entity_id === entityId) loadComments();
    };
    window.addEventListener('realtime_event', handleWs);
    return () => window.removeEventListener('realtime_event', handleWs);
  }, [entityId, entityType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    await collaborationApi.createComment({ entity_type: entityType, entity_id: entityId, content: newComment });
    setNewComment('');
    loadComments();
  };

  const handleReact = async (commentId: string, reaction: string) => {
    await collaborationApi.addReaction(commentId, reaction);
    loadComments();
  };

  const handleDelete = async (commentId: string) => {
    if (!confirm("Delete comment?")) return;
    await collaborationApi.deleteComment(commentId);
    loadComments();
  };

  if (loading) return <div className="text-gray-500 text-sm">Loading comments...</div>;

  return (
    <div className="space-y-6">
      <h3 className="text-sm font-medium text-gray-400 flex items-center gap-2">
        <MessageSquare className="w-4 h-4" /> Comments ({comments.length})
      </h3>

      <div className="space-y-4">
        {comments.map(c => (
          <div key={c.id} className={`bg-gray-800/50 rounded-lg p-4 border ${c.is_pinned ? 'border-indigo-500/50' : 'border-gray-700/50'}`}>
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white">
                  U
                </div>
                <span className="text-sm font-medium text-gray-300">User</span>
                <span className="text-xs text-gray-500">{new Date(c.created_at).toLocaleString()}</span>
                {c.is_edited && <span className="text-[10px] text-gray-500">(edited)</span>}
                {c.is_pinned && <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded">Pinned</span>}
              </div>
              
              {user?.id === c.author_id && (
                <button onClick={() => handleDelete(c.id)} className="text-gray-500 hover:text-red-400">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            <div className="text-sm text-gray-200 whitespace-pre-wrap ml-8">{c.content}</div>
            
            <div className="mt-3 ml-8 flex gap-2">
              <button onClick={() => handleReact(c.id, '👍')} className="text-xs flex items-center gap-1 bg-gray-800 hover:bg-gray-700 px-2 py-1 rounded text-gray-400">
                <ThumbsUp className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={newComment}
          onChange={e => setNewComment(e.target.value)}
          placeholder="Add a comment... (use @ to mention)"
          className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm text-white outline-none focus:border-blue-500 min-h-[80px]"
        />
        <button type="submit" disabled={!newComment.trim()} className="absolute bottom-3 right-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white p-1.5 rounded transition-colors">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
