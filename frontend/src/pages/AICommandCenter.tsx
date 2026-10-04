import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import { aiApi } from '../lib/aiApi';
import { projectApi } from '../lib/projectApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function AICommandCenter() {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  
  const [orgBrief, setOrgBrief] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [riskEngine, setRiskEngine] = useState<any>(null);
  const [sprintPlan, setSprintPlan] = useState<any>(null);
  const [healthReport, setHealthReport] = useState<any>(null);
  const [taskPriorities, setTaskPriorities] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    projectApi.list().then((data: any) => {
      setProjects(data);
      if (data.length > 0) {
        setSelectedProjectId(data[0].id);
      }
    });
    // Org level data
    aiApi.getOrgDailyBrief().then(setOrgBrief).catch(console.error);
  }, []);

  const loadInsights = async () => {
    if (!selectedProjectId) return;
    setLoading(true);
    try {
      const [fc, rsk, sp, hr, tp] = await Promise.all([
        aiApi.getForecast(selectedProjectId).catch(() => null),
        aiApi.getRiskEngine(selectedProjectId).catch(() => null),
        aiApi.getSmartSprintPlan(selectedProjectId).catch(() => null),
        aiApi.getHealthReport(selectedProjectId).catch(() => null),
        aiApi.getTaskPriorities(selectedProjectId).catch(() => [])
      ]);
      setForecast(fc);
      setRiskEngine(rsk);
      setSprintPlan(sp);
      setHealthReport(hr);
      setTaskPriorities(tp || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, [selectedProjectId]);

  const mockChartData = [
    { name: 'Week 1', velocity: 3, risk: 20 },
    { name: 'Week 2', velocity: 5, risk: 15 },
    { name: 'Week 3', velocity: forecast?.velocity || 4, risk: riskEngine?.overall_risk_score || 30 },
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Predictive AI Engineering Command Center</h1>
        <div className="flex space-x-4">
          <select 
            className="border p-2 rounded bg-gray-800 text-white"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <Button onClick={loadInsights} disabled={loading}>
            {loading ? 'Analyzing...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {orgBrief && (
        <div className="bg-gray-800 rounded-lg p-6 border-l-4 border-blue-500">
          <h2 className="text-xl font-bold mb-4">Today's Org Engineering Brief</h2>
          <div className="space-y-2">
             {orgBrief.recommended_focus_for_today?.map((r: any, i: number) => (
                <div key={i} className="text-sm bg-gray-700 p-2 rounded">
                  <strong>{r.title} ({r.priority})</strong>: {r.reason}
                </div>
             ))}
             {orgBrief.overdue_tasks?.length > 0 && <p className="text-red-400">{orgBrief.overdue_tasks.length} Overdue tasks across org</p>}
             {orgBrief.blocked_tasks?.length > 0 && <p className="text-yellow-400">{orgBrief.blocked_tasks.length} Blocked tasks across org</p>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Health Report */}
        {healthReport && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Overall Engineering Health</h2>
            <div className="space-y-4">
              <p><strong>Health:</strong> {healthReport.project_health}</p>
              <p><strong>Delivery:</strong> {healthReport.delivery_status}</p>
              <div className="bg-gray-700 p-3 rounded text-sm">
                <strong>Executive Summary:</strong>
                <p>{healthReport.executive_summary}</p>
              </div>
            </div>
          </div>
        )}

        {/* Risk Overview */}
        {riskEngine && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4 flex justify-between">
              Project Risk Overview 
              <span className={`px-2 py-1 rounded text-sm ${riskEngine.overall_risk_score > 50 ? 'bg-red-500' : 'bg-green-500'}`}>Score: {riskEngine.overall_risk_score}</span>
            </h2>
            {riskEngine.risks?.length > 0 ? (
              <ul className="space-y-3">
                {riskEngine.risks.map((risk: any, i: number) => (
                  <li key={i} className="bg-gray-700 p-3 rounded">
                    <strong>{risk.title}</strong> ({risk.severity})
                    <p className="text-xs text-gray-400 mt-1">{risk.evidence}</p>
                  </li>
                ))}
              </ul>
            ) : <p>No major risks detected.</p>}
          </div>
        )}

        {/* Delivery Forecast */}
        {forecast && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Delivery Forecast</h2>
            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
              <div className="bg-gray-700 p-2 rounded">
                <p className="text-gray-400">Est. Completion</p>
                <p className="font-bold text-lg">{forecast.estimated_completion_date ? new Date(forecast.estimated_completion_date).toLocaleDateString() : 'N/A'}</p>
              </div>
              <div className="bg-gray-700 p-2 rounded">
                <p className="text-gray-400">Velocity (tasks/wk)</p>
                <p className="font-bold text-lg">{forecast.velocity}</p>
              </div>
              <div className="bg-gray-700 p-2 rounded">
                <p className="text-gray-400">Remaining Tasks</p>
                <p className="font-bold text-lg">{forecast.remaining_tasks}</p>
              </div>
              <div className="bg-gray-700 p-2 rounded">
                <p className="text-gray-400">Confidence</p>
                <p className="font-bold text-lg">{forecast.confidence}</p>
              </div>
            </div>
            
            <div className="h-48 mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="name" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                  <Legend />
                  <Line type="monotone" dataKey="velocity" stroke="#3b82f6" strokeWidth={2} name="Velocity" />
                  <Line type="monotone" dataKey="risk" stroke="#ef4444" strokeWidth={2} name="Risk Trend" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Sprint Forecast */}
        {sprintPlan && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Sprint Forecast</h2>
            <div className="space-y-4 text-sm">
              <p><strong>Rec. Capacity:</strong> {sprintPlan.recommended_capacity_points} pts</p>
              <p><strong>Suggested Tasks:</strong> {sprintPlan.suggested_tasks?.length || 0}</p>
              <p><strong>Excluded Tasks:</strong> {sprintPlan.excluded_tasks?.length || 0}</p>
              {Object.keys(sprintPlan.reasons_for_exclusions || {}).length > 0 && (
                <div className="bg-gray-700 p-2 rounded mt-2">
                  <p className="font-bold mb-1">Exclusions (Sample)</p>
                  <p className="text-xs text-gray-400">Tasks were excluded to prevent overallocation based on priority sorting.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Task Priorities */}
      {taskPriorities.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Critical Tasks Priority Engine</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="py-2">Key</th>
                  <th className="py-2">Score</th>
                  <th className="py-2">Level</th>
                  <th className="py-2">AI Reason</th>
                </tr>
              </thead>
              <tbody>
                {taskPriorities.slice(0, 5).map(tp => (
                  <tr key={tp.task_id} className="border-b border-gray-700">
                    <td className="py-2">{tp.task_key}</td>
                    <td className="py-2">{tp.score}</td>
                    <td className="py-2 font-bold text-blue-400">{tp.priority_level}</td>
                    <td className="py-2 text-xs text-gray-400">{tp.reasons?.join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
