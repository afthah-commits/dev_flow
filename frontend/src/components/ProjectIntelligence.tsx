import React, { useState, useEffect } from 'react';
import { aiApi } from '../lib/aiApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function ProjectIntelligence({ project }: { project: any }) {
  const [forecast, setForecast] = useState<any>(null);
  const [riskEngine, setRiskEngine] = useState<any>(null);
  const [sprintPlan, setSprintPlan] = useState<any>(null);
  const [healthReport, setHealthReport] = useState<any>(null);
  const [taskPriorities, setTaskPriorities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadInsights = async () => {
    if (!project?.id) return;
    setLoading(true);
    try {
      const [fc, rsk, sp, hr, tp] = await Promise.all([
        aiApi.getForecast(project.id).catch(() => null),
        aiApi.getRiskEngine(project.id).catch(() => null),
        aiApi.getSmartSprintPlan(project.id).catch(() => null),
        aiApi.getHealthReport(project.id).catch(() => null),
        aiApi.getTaskPriorities(project.id).catch(() => [])
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
  }, [project?.id]);

  if (loading) return <div className="p-4 text-center">Loading AI Intelligence...</div>;

  const mockChartData = [
    { name: 'Week 1', velocity: 3, risk: 20 },
    { name: 'Week 2', velocity: 5, risk: 15 },
    { name: 'Week 3', velocity: forecast?.velocity || 4, risk: riskEngine?.overall_risk_score || 30 },
  ];

  return (
    <div className="space-y-6">
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
            <h2 className="text-xl font-bold mb-4">Sprint Recommendation</h2>
            <div className="space-y-4 text-sm">
              <p><strong>Rec. Capacity:</strong> {sprintPlan.recommended_capacity_points} pts</p>
              <p><strong>Suggested Tasks:</strong> {sprintPlan.suggested_tasks?.length || 0}</p>
              <p><strong>Excluded Tasks:</strong> {sprintPlan.excluded_tasks?.length || 0}</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Task Priorities */}
      {taskPriorities.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Task Priorities</h2>
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
