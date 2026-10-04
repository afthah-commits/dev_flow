import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import { aiApi } from '../lib/aiApi';
import { projectApi } from '../lib/projectApi';

export default function AICommandCenter() {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  
  const [dailyBrief, setDailyBrief] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [risks, setRisks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    projectApi.list().then((data: any) => {
      setProjects(data);
      if (data.length > 0) {
        setSelectedProjectId(data[0].id);
      }
    });
  }, []);

  const loadInsights = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    try {
      const brief = await aiApi.getDailyBrief(selectedProjectId);
      setDailyBrief(brief);
      const summ = await aiApi.getProjectSummary(selectedProjectId);
      setSummary(summ);
      const r = await aiApi.getProjectRisks(selectedProjectId);
      setRisks(r);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, [selectedProjectId]);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">AI Engineering Command Center</h1>
        <select 
          className="border p-2 rounded"
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
        >
          {projects.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </div>

      <Button onClick={loadInsights} disabled={loading}>
        {loading ? 'Analyzing...' : 'Refresh Insights'}
      </Button>

      {dailyBrief && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">AI Engineering Brief</h2>
          <div>
            <p><strong>Recommended Focus:</strong> {dailyBrief.recommended_focus}</p>
            <p><strong>GitHub Changes:</strong> {dailyBrief.github_changes}</p>
            <p><strong>PR Activity:</strong> {dailyBrief.pr_activity}</p>
          </div>
        </div>
      )}

      {summary && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Project Status Summary</h2>
          <div>
            <p><strong>Status:</strong> {summary.current_status}</p>
            <p><strong>Health:</strong> {summary.health}</p>
            <p><strong>Progress:</strong> {summary.progress}</p>
          </div>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Project Risks</h2>
        <div>
          {risks.length > 0 ? (
            <ul className="space-y-4">
              {risks.map((risk, i) => (
                <li key={i} className="border p-4 rounded bg-red-50 dark:bg-red-900/10 text-red-900 dark:text-red-200">
                  <strong>{risk.title} ({risk.severity})</strong>
                  <p>{risk.explanation}</p>
                  <p className="text-sm mt-2"><em>Recommendation: {risk.recommendation}</em></p>
                </li>
              ))}
            </ul>
          ) : (
            <p>No major risks detected.</p>
          )}
        </div>
      </div>
    </div>
  );
}
