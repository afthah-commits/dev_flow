import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { releaseApi } from '../lib/releaseApi';
import { Release } from '../types/release';
import { Rocket, Plus, Search } from 'lucide-react';

export default function Releases() {
  const { projectId } = useParams<{ projectId: string }>();
  const [releases, setReleases] = useState<Release[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', version: '', release_type: 'MINOR' });

  useEffect(() => {
    if (!projectId) return;
    loadReleases();
  }, [projectId]);

  const loadReleases = () => {
    if (!projectId) return;
    releaseApi.list(projectId).then(setReleases).finally(() => setLoading(false));
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId) return;
    await releaseApi.create(projectId, formData);
    setShowForm(false);
    setFormData({ name: '', version: '', release_type: 'MINOR' });
    loadReleases();
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading releases...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Rocket className="w-5 h-5 text-indigo-400" />
          Releases
        </h2>
        <button
          onClick={() => setShowForm(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded flex items-center gap-1 text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" /> Create Release
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-800 flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
            <input type="text" placeholder="Search releases..." className="w-full bg-gray-800 text-white text-sm rounded border border-gray-700 pl-9 pr-3 py-2 outline-none focus:border-indigo-500" />
          </div>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800 text-gray-400">
            <tr>
              <th className="px-4 py-3">Version</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {releases.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No releases found.</td></tr>
            ) : releases.map(r => (
              <tr key={r.id} className="hover:bg-gray-800/50">
                <td className="px-4 py-3 font-medium text-white">
                  <Link to={`/projects/${projectId}/releases/${r.id}`} className="hover:underline text-indigo-400">
                    {r.version}
                  </Link>
                </td>
                <td className="px-4 py-3">{r.name}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    r.status === 'RELEASED' ? 'bg-green-500/10 text-green-400' :
                    r.status === 'READY' ? 'bg-blue-500/10 text-blue-400' :
                    r.status === 'PLANNED' ? 'bg-purple-500/10 text-purple-400' :
                    'bg-gray-700 text-gray-300'
                  }`}>
                    {r.status}
                  </span>
                </td>
                <td className="px-4 py-3">{r.release_type}</td>
                <td className="px-4 py-3 text-gray-400">{new Date(r.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 w-full max-w-md shadow-xl">
            <h3 className="text-lg font-bold text-white mb-4">New Release</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Version (e.g., v1.0.0)</label>
                <input required type="text" value={formData.version} onChange={e => setFormData({...formData, version: e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                <input required type="text" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Type</label>
                <select value={formData.release_type} onChange={e => setFormData({...formData, release_type: e.target.value})} className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white">
                  <option>MAJOR</option><option>MINOR</option><option>PATCH</option><option>HOTFIX</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-gray-400 hover:text-white">Cancel</button>
                <button type="submit" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded">Create Release</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
