import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { releaseApi } from '../lib/releaseApi';
import { Release, ReleaseTask, ReleasePR } from '../types/release';
import ReleaseReadiness from '../components/ReleaseReadiness';
import { Rocket, ArrowLeft, Play, Server, FileText } from 'lucide-react';
import { environmentApi } from '../lib/environmentApi';
import { Environment } from '../types/environment';

export default function ReleaseDetails() {
  const { projectId, releaseId } = useParams<{ projectId: string, releaseId: string }>();
  const [release, setRelease] = useState<Release | null>(null);
  const [tasks, setTasks] = useState<ReleaseTask[]>([]);
  const [prs, setPrs] = useState<ReleasePR[]>([]);
  const [notes, setNotes] = useState('');
  const [envs, setEnvs] = useState<Environment[]>([]);
  const [loading, setLoading] = useState(true);
  const [deployEnv, setDeployEnv] = useState('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!projectId || !releaseId) return;
    Promise.all([
      releaseApi.get(projectId, releaseId),
      releaseApi.getTasks(releaseId),
      releaseApi.getPRs(releaseId),
      releaseApi.getNotes(releaseId),
      environmentApi.list(projectId)
    ]).then(([r, t, p, n, e]) => {
      setRelease(r);
      setTasks(t);
      setPrs(p);
      setNotes(n.notes || '');
      setEnvs(e);
      if (e.length > 0) setDeployEnv(e[0].id);
    }).finally(() => setLoading(false));
  }, [projectId, releaseId]);

  if (loading || !release) return <div className="p-8 text-center text-gray-500">Loading release details...</div>;

  const handleAction = async (action: 'plan' | 'ready' | 'release' | 'cancel') => {
    if (!releaseId) return;
    const fn = releaseApi[action];
    const r = await fn(releaseId);
    setRelease(r);
  };

  const handleGenerateNotes = async () => {
    if (!projectId || !releaseId) return;
    setGenerating(true);
    try {
      const res = await releaseApi.generateAINotes(projectId, releaseId);
      setNotes(res.generated_notes);
      await releaseApi.updateNotes(releaseId, res.generated_notes);
    } finally {
      setGenerating(false);
    }
  };

  const handleDeploy = async () => {
    if (!releaseId || !deployEnv) return;
    await releaseApi.deploy(releaseId, { environment_id: deployEnv, provider: 'MOCK' });
    alert('Deployment triggered!');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/projects/${projectId}`} className="p-2 hover:bg-gray-800 rounded-full text-gray-400 transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{release.version}</h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
              release.status === 'RELEASED' ? 'bg-green-500/10 text-green-400' :
              release.status === 'READY' ? 'bg-blue-500/10 text-blue-400' :
              release.status === 'PLANNED' ? 'bg-purple-500/10 text-purple-400' :
              'bg-gray-700 text-gray-300'
            }`}>
              {release.status}
            </span>
          </div>
          <p className="text-gray-400 mt-1">{release.name} • {release.release_type}</p>
        </div>
        
        <div className="ml-auto flex gap-2">
          {release.status === 'DRAFT' && <button onClick={() => handleAction('plan')} className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 font-medium text-sm">Plan Release</button>}
          {release.status === 'PLANNED' && <button onClick={() => handleAction('ready')} className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 font-medium text-sm">Mark Ready</button>}
          {release.status === 'READY' && <button onClick={() => handleAction('release')} className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 font-medium text-sm flex items-center gap-2"><Rocket className="w-4 h-4"/> Publish Release</button>}
          {release.status !== 'CANCELLED' && release.status !== 'RELEASED' && <button onClick={() => handleAction('cancel')} className="px-4 py-2 border border-gray-700 text-red-400 rounded hover:bg-gray-800 font-medium text-sm">Cancel</button>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-400" /> Release Notes
              </h3>
              <button disabled={generating} onClick={handleGenerateNotes} className="text-sm text-indigo-400 hover:text-indigo-300">
                {generating ? 'Generating...' : 'Generate with AI'}
              </button>
            </div>
            <textarea 
              value={notes}
              onChange={e => setNotes(e.target.value)}
              onBlur={() => releaseId && releaseApi.updateNotes(releaseId, notes)}
              className="w-full h-64 bg-gray-800 text-gray-300 border border-gray-700 rounded-lg p-3 outline-none focus:border-indigo-500 font-mono text-sm"
              placeholder="Release notes markdown..."
            />
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <h3 className="text-lg font-medium text-white mb-4">Included Items</h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-2 uppercase">Tasks ({tasks.length})</h4>
                <ul className="space-y-2">
                  {tasks.map(t => (
                    <li key={t.id} className="flex justify-between text-sm bg-gray-800 p-2 rounded">
                      <span className="text-white">{t.title}</span>
                      <span className="text-gray-400">{t.status?.replace('_', ' ')}</span>
                    </li>
                  ))}
                  {tasks.length === 0 && <li className="text-gray-500 text-sm italic">No tasks included.</li>}
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-2 uppercase">Pull Requests ({prs.length})</h4>
                <ul className="space-y-2">
                  {prs.map(p => (
                    <li key={p.id} className="text-sm bg-gray-800 p-2 rounded text-indigo-400">
                      <a href={p.pr_url || '#'} target="_blank" rel="noreferrer">#{p.pr_number} {p.pr_title}</a>
                    </li>
                  ))}
                  {prs.length === 0 && <li className="text-gray-500 text-sm italic">No pull requests included.</li>}
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <ReleaseReadiness releaseId={releaseId!} />

          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
            <h3 className="text-lg font-medium text-white flex items-center gap-2 mb-4">
              <Server className="w-5 h-5 text-gray-400" /> Deployment
            </h3>
            <div className="space-y-3">
              <select value={deployEnv} onChange={e => setDeployEnv(e.target.value)} className="w-full bg-gray-800 text-white text-sm rounded border border-gray-700 p-2 outline-none">
                {envs.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                {envs.length === 0 && <option value="">No environments setup</option>}
              </select>
              <button 
                onClick={handleDeploy}
                disabled={!deployEnv}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded p-2 flex justify-center items-center gap-2 text-sm font-medium transition-colors disabled:opacity-50"
              >
                <Play className="w-4 h-4" /> Deploy to Environment
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
