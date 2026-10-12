import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { aiApi } from '../lib/aiApi';
import { projectApi } from '../lib/projectApi';
import { Project } from '../types/project';
import { ProjectAIPlanning } from '../components/ProjectAIPlanning';
import { ProjectAI } from '../components/ProjectAI';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

export default function AICommandCenter() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'insights' | 'planning' | 'assistant'>('insights');
  
  const [orgBrief, setOrgBrief] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [riskEngine, setRiskEngine] = useState<any>(null);
  const [sprintPlan, setSprintPlan] = useState<any>(null);
  const [healthReport, setHealthReport] = useState<any>(null);
  const [taskPriorities, setTaskPriorities] = useState<any[]>([]);
  
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load project list and org brief on mount
  useEffect(() => {
    let isMounted = true;
    setLoadingProjects(true);

    projectApi.list()
      .then((data: any) => {
        if (!isMounted) return;
        const items: Project[] = Array.isArray(data) ? data : (data?.items || []);
        setProjects(items);
        if (items.length > 0) {
          setSelectedProjectId(items[0].id);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        console.error('Failed to load projects for AI center:', err);
        setError('Failed to fetch projects. Please verify your workspace connection.');
      })
      .finally(() => {
        if (isMounted) setLoadingProjects(false);
      });

    aiApi.getOrgDailyBrief()
      .then((brief) => {
        if (isMounted) setOrgBrief(brief);
      })
      .catch((err) => {
        console.error('Failed to load org daily brief:', err);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const loadInsights = async () => {
    if (!selectedProjectId) return;
    setLoadingInsights(true);
    setError(null);
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
    } catch (e: any) {
      console.error('Error loading AI insights:', e);
      setError('Some AI analytics could not be retrieved.');
    } finally {
      setLoadingInsights(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      loadInsights();
    }
  }, [selectedProjectId]);

  const selectedProject = projects.find(p => p.id === selectedProjectId);

  const mockChartData = [
    { name: 'Week 1', velocity: 3, risk: 20 },
    { name: 'Week 2', velocity: 5, risk: 15 },
    { name: 'Current', velocity: forecast?.velocity || 4, risk: riskEngine?.overall_risk_score || 30 },
  ];

  if (loadingProjects) {
    return (
      <div className="p-8 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-[60vh] text-gray-400 space-y-4">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium">Loading Predictive AI Command Center...</p>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        <div className="text-center py-16 px-6 bg-gray-900 border border-gray-800 rounded-xl space-y-4">
          <div className="w-16 h-16 mx-auto bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-2xl flex items-center justify-center text-2xl font-bold">
            AI
          </div>
          <h2 className="text-2xl font-bold text-white">No Projects Available</h2>
          <p className="text-gray-400 max-w-md mx-auto text-sm leading-relaxed">
            The Predictive AI Command Center requires at least one project to deliver forecasts, engineering health reports, and sprint risk assessments.
          </p>
          <div className="pt-2">
            <Link to="/projects/new">
              <Button>+ Create First Project</Button>
            </Link>
          </div>
        </div>

        {orgBrief && (
          <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-3">Organization Overview</h3>
            <p className="text-sm text-gray-400">
              {orgBrief.recommended_focus_for_today?.length 
                ? 'Your organization is configured and ready for projects.' 
                : 'Workspace bootstrap complete. Add projects to begin.'}
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto text-gray-100">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-gray-800">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              Advisory Intelligence
            </span>
            <span className="text-xs text-gray-400">Phase 50 Production</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mt-1">
            Predictive AI Command Center
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-0.5">
            Real-time delivery forecasts, sprint risk telemetry, and AI planning assistance.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select 
            aria-label="Select Project"
            className="flex-1 sm:flex-initial bg-gray-900 border border-gray-700 hover:border-gray-600 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <Button 
            variant="secondary"
            onClick={loadInsights} 
            disabled={loadingInsights}
          >
            {loadingInsights ? 'Analyzing...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-900/30 border border-red-800 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xs text-red-400 hover:text-red-200">Dismiss</button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('insights')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === 'insights'
              ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
          }`}
        >
          Engineering Insights & Risks
        </button>
        <button
          onClick={() => setActiveTab('planning')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === 'planning'
              ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
          }`}
        >
          AI Planning & Breakdown
        </button>
        <button
          onClick={() => setActiveTab('assistant')}
          className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
            activeTab === 'assistant'
              ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
          }`}
        >
          AI Assistant & Actions
        </button>
      </div>

      {/* Tab 1: Engineering Insights & Health */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          {/* Org Brief Banner */}
          {orgBrief && (
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-5 border-l-4 border-l-indigo-500">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base font-semibold text-white">Daily Organization Engineering Brief</h2>
                <span className="text-xs text-gray-400">Org-wide telemetry</span>
              </div>
              <div className="space-y-2">
                {orgBrief.recommended_focus_for_today?.map((r: any, i: number) => (
                  <div key={i} className="text-sm bg-gray-800/70 p-3 rounded-lg border border-gray-700/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <strong className="text-white">{r.title}</strong>
                      <span className="text-xs text-gray-400 ml-2">{r.reason}</span>
                    </div>
                    <span className="px-2 py-0.5 text-xs font-semibold rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 self-start sm:self-auto">
                      {r.priority}
                    </span>
                  </div>
                ))}
                {(!orgBrief.recommended_focus_for_today || orgBrief.recommended_focus_for_today.length === 0) && (
                  <p className="text-sm text-gray-400">All organization streams running smoothly.</p>
                )}
                <div className="flex flex-wrap gap-4 pt-1 text-xs">
                  {orgBrief.overdue_tasks?.length > 0 && (
                    <span className="text-red-400 font-medium">⚠️ {orgBrief.overdue_tasks.length} overdue tasks</span>
                  )}
                  {orgBrief.blocked_tasks?.length > 0 && (
                    <span className="text-amber-400 font-medium">🛑 {orgBrief.blocked_tasks.length} blocked tasks</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Health Report */}
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-base font-semibold text-white">Overall Engineering Health</h2>
                  {healthReport?.project_health && (
                    <span className="px-2.5 py-0.5 text-xs font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      {healthReport.project_health}
                    </span>
                  )}
                </div>
                {healthReport ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between text-gray-300 border-b border-gray-800 pb-2">
                      <span className="text-gray-400">Delivery Status</span>
                      <span className="font-medium text-white">{healthReport.delivery_status || 'On Track'}</span>
                    </div>
                    <div className="flex justify-between text-gray-300 border-b border-gray-800 pb-2">
                      <span className="text-gray-400">Deployment Health</span>
                      <span className="font-medium text-white">{healthReport.deployment_health || 'Passing'}</span>
                    </div>
                    <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/40 text-xs text-gray-300 leading-relaxed mt-3">
                      <strong className="block text-gray-200 mb-1">Executive Summary:</strong>
                      {healthReport.executive_summary}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-400 py-6 text-center">
                    {loadingInsights ? 'Analyzing project telemetry...' : 'No health evaluation available yet.'}
                  </div>
                )}
              </div>
            </div>

            {/* Risk Overview */}
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-base font-semibold text-white">Project Risk Overview</h2>
                  {riskEngine && (
                    <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${
                      riskEngine.overall_risk_score > 50 
                        ? 'bg-red-500/20 text-red-400 border-red-500/30' 
                        : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    }`}>
                      Score: {riskEngine.overall_risk_score}
                    </span>
                  )}
                </div>
                {riskEngine?.risks?.length > 0 ? (
                  <ul className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                    {riskEngine.risks.map((risk: any, i: number) => (
                      <li key={i} className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/40 text-sm">
                        <div className="flex justify-between items-center">
                          <strong className="text-white text-xs">{risk.title}</strong>
                          <span className="text-[11px] text-amber-400 font-semibold uppercase">{risk.severity}</span>
                        </div>
                        <p className="text-xs text-gray-400 mt-1 leading-relaxed">{risk.evidence}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-gray-400 py-6 text-center">
                    {loadingInsights ? 'Assessing delivery risks...' : 'No active risks identified for this project.'}
                  </div>
                )}
              </div>
            </div>

            {/* Delivery Forecast */}
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6 min-w-0">
              <h2 className="text-base font-semibold text-white mb-4">Delivery Forecast</h2>
              {forecast ? (
                <div>
                  <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                    <div className="bg-gray-800/70 p-3 rounded-lg border border-gray-700/40">
                      <p className="text-xs text-gray-400">Est. Completion</p>
                      <p className="font-bold text-white text-base mt-0.5">
                        {forecast.estimated_completion_date ? new Date(forecast.estimated_completion_date).toLocaleDateString() : 'Active'}
                      </p>
                    </div>
                    <div className="bg-gray-800/70 p-3 rounded-lg border border-gray-700/40">
                      <p className="text-xs text-gray-400">Velocity (tasks/wk)</p>
                      <p className="font-bold text-indigo-400 text-base mt-0.5">{forecast.velocity}</p>
                    </div>
                    <div className="bg-gray-800/70 p-3 rounded-lg border border-gray-700/40">
                      <p className="text-xs text-gray-400">Remaining Tasks</p>
                      <p className="font-bold text-white text-base mt-0.5">{forecast.remaining_tasks}</p>
                    </div>
                    <div className="bg-gray-800/70 p-3 rounded-lg border border-gray-700/40">
                      <p className="text-xs text-gray-400">Confidence</p>
                      <p className="font-bold text-emerald-400 text-base mt-0.5">{forecast.confidence}</p>
                    </div>
                  </div>

                  <div className="h-44 w-full min-w-0 mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={mockChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} />
                        <YAxis stroke="#9ca3af" fontSize={11} />
                        <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#fff' }} />
                        <Legend wrapperStyle={{ fontSize: '11px' }} />
                        <Line type="monotone" dataKey="velocity" stroke="#6366f1" strokeWidth={2} name="Velocity" />
                        <Line type="monotone" dataKey="risk" stroke="#ef4444" strokeWidth={2} name="Risk Trend" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-400 py-6 text-center">
                  {loadingInsights ? 'Calculating velocity forecast...' : 'No forecast metrics available.'}
                </div>
              )}
            </div>

            {/* Sprint Plan Recommendation */}
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
              <h2 className="text-base font-semibold text-white mb-4">Sprint Capacity Recommendation</h2>
              {sprintPlan ? (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span className="text-gray-400">Recommended Capacity</span>
                    <span className="font-bold text-indigo-400">{sprintPlan.recommended_capacity_points} pts</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span className="text-gray-400">Suggested Tasks</span>
                    <span className="font-medium text-white">{sprintPlan.suggested_tasks?.length || 0}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-800 pb-2">
                    <span className="text-gray-400">Excluded Tasks</span>
                    <span className="font-medium text-white">{sprintPlan.excluded_tasks?.length || 0}</span>
                  </div>
                  {Object.keys(sprintPlan.reasons_for_exclusions || {}).length > 0 && (
                    <div className="bg-gray-800/60 p-3 rounded-lg border border-gray-700/40 text-xs text-gray-400 mt-2">
                      <strong className="block text-gray-200 mb-1">Prioritization Note:</strong>
                      Excluded tasks deferred to protect sprint focus based on team capacity.
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-gray-400 py-6 text-center">
                  {loadingInsights ? 'Evaluating sprint capacity...' : 'No active sprint recommendation.'}
                </div>
              )}
            </div>
          </div>

          {/* Task Priorities Engine Table */}
          {taskPriorities.length > 0 && (
            <div className="bg-gray-900/80 border border-gray-800 rounded-xl p-6">
              <h2 className="text-base font-semibold text-white mb-4">Task Priority Engine</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wider">
                      <th className="py-2.5 px-3">Key</th>
                      <th className="py-2.5 px-3">Score</th>
                      <th className="py-2.5 px-3">Level</th>
                      <th className="py-2.5 px-3">AI Rationale</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800/50">
                    {taskPriorities.slice(0, 8).map(tp => (
                      <tr key={tp.task_id} className="hover:bg-gray-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-indigo-400">{tp.task_key}</td>
                        <td className="py-2.5 px-3 text-white font-medium">{tp.score}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 text-xs font-semibold rounded ${
                            tp.priority_level === 'HIGH' 
                              ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                              : tp.priority_level === 'MEDIUM'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          }`}>
                            {tp.priority_level}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-xs text-gray-400">{tp.reasons?.join(', ') || 'Optimized based on dependencies'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: AI Planning & Progressive Breakdown */}
      {activeTab === 'planning' && selectedProject && (
        <div className="space-y-4">
          <ProjectAIPlanning project={selectedProject} onChanged={loadInsights} />
        </div>
      )}

      {/* Tab 3: AI Assistant & Quick Actions */}
      {activeTab === 'assistant' && selectedProject && (
        <div className="space-y-4">
          <ProjectAI project={selectedProject} />
        </div>
      )}
    </div>
  );
}
