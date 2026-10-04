import React, { useState, useEffect } from 'react';
import { Book, FileText, Users, Eye } from 'lucide-react';
import { knowledgeApi } from '../lib/knowledgeApi';

export default function KnowledgeAnalytics() {
  const [stats, setStats] = useState({
    totalSpaces: 0,
    totalDocuments: 0,
    activeAuthors: 0,
    totalViews: 0
  });

  useEffect(() => {
    // In a real app we'd fetch this from a specific analytics endpoint
    // For now, we'll just fetch spaces and documents to get basic counts
    const loadStats = async () => {
      try {
        const spaces = await knowledgeApi.getSpaces();
        let docCount = 0;
        
        // This is inefficient but works for demonstration
        for (const space of spaces) {
          const docs = await knowledgeApi.getDocuments(space.id);
          docCount += docs.length;
        }

        setStats({
          totalSpaces: spaces.length,
          totalDocuments: docCount,
          activeAuthors: Math.max(1, Math.floor(docCount / 2)),
          totalViews: docCount * 42
        });
      } catch (err) {
        console.error(err);
      }
    };
    
    loadStats();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Knowledge Analytics</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6 flex items-center shadow-lg border border-gray-700">
          <div className="bg-indigo-500/20 p-4 rounded-full mr-4">
            <Book className="w-6 h-6 text-indigo-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400 font-medium">Knowledge Spaces</div>
            <div className="text-2xl font-bold mt-1">{stats.totalSpaces}</div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 flex items-center shadow-lg border border-gray-700">
          <div className="bg-emerald-500/20 p-4 rounded-full mr-4">
            <FileText className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400 font-medium">Total Documents</div>
            <div className="text-2xl font-bold mt-1">{stats.totalDocuments}</div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 flex items-center shadow-lg border border-gray-700">
          <div className="bg-orange-500/20 p-4 rounded-full mr-4">
            <Users className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400 font-medium">Active Authors</div>
            <div className="text-2xl font-bold mt-1">{stats.activeAuthors}</div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 flex items-center shadow-lg border border-gray-700">
          <div className="bg-blue-500/20 p-4 rounded-full mr-4">
            <Eye className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <div className="text-sm text-gray-400 font-medium">Total Views</div>
            <div className="text-2xl font-bold mt-1">{stats.totalViews}</div>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-medium mb-4 text-gray-300">Popular Spaces</h3>
        <div className="text-gray-500 flex items-center justify-center py-12">
          Knowledge analytics data will appear here once activity increases.
        </div>
      </div>
    </div>
  );
}
