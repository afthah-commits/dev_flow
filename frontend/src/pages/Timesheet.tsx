import React, { useEffect, useState } from 'react';
import { timeApi } from '../lib/timeApi';
import { TimeEntry, TimeSummary } from '../types/time';
import { Play, Square, Plus, Trash2, Edit2, CheckCircle2 } from 'lucide-react';
import { projectApi } from '../lib/projectApi';

export default function Timesheet() {
  const [summary, setSummary] = useState<TimeSummary | null>(null);
  const [entries, setEntries] = useState<TimeEntry[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Timer state
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [timerDesc, setTimerDesc] = useState('');
  
  useEffect(() => {
    loadData();
    window.addEventListener('timer_stopped', loadData);
    return () => window.removeEventListener('timer_stopped', loadData);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sumData, entData, projData] = await Promise.all([
        timeApi.getMySummary(),
        timeApi.getEntries(),
        projectApi.list()
      ]);
      setSummary(sumData);
      setEntries(entData.items);
      setProjects(projData.items);
      
      if (projData.items.length > 0 && !selectedProject) {
        setSelectedProject(projData.items[0].id);
      }
    } catch (e: any) {
      setError('Failed to load timesheet data');
    } finally {
      setLoading(false);
    }
  };

  const handleStartTimer = async () => {
    if (!selectedProject) return;
    try {
      await timeApi.startTimer({ project_id: selectedProject, description: timerDesc });
      setTimerDesc('');
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to start timer');
    }
  };

  const handleStopTimer = async () => {
    try {
      await timeApi.stopTimer();
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to stop timer');
    }
  };
  
  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this time entry?')) return;
    try {
      await timeApi.deleteEntry(id);
      loadData();
    } catch (e: any) {
      alert('Failed to delete entry');
    }
  };

  const formatHours = (hours: number) => {
    return Math.round(hours * 10) / 10;
  };

  if (loading) return <div className="text-gray-400 p-8">Loading timesheet...</div>;
  if (error) return <div className="text-red-400 p-8">{error}</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Time Tracking</h1>
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">Today</div>
            <div className="text-2xl font-bold text-white">{formatHours(summary.today_hours)}h</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">This Week</div>
            <div className="text-2xl font-bold text-blue-400">{formatHours(summary.week_hours)}h</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">This Month</div>
            <div className="text-2xl font-bold text-white">{formatHours(summary.month_hours)}h</div>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="text-sm text-gray-400">Total Tracked</div>
            <div className="text-2xl font-bold text-gray-300">{formatHours(summary.tracked_hours)}h</div>
          </div>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Timer</h2>
        
        {summary?.active_timer ? (
          <div className="flex items-center gap-4 bg-gray-800 p-4 rounded-lg border border-blue-500/50">
            <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
            <div className="flex-1">
              <div className="font-medium text-white">{summary.active_timer.description || "Active Timer"}</div>
              <div className="text-sm text-gray-400">
                Started at {new Date(summary.active_timer.started_at).toLocaleTimeString()}
              </div>
            </div>
            <button 
              onClick={handleStopTimer}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md font-medium flex items-center gap-2"
            >
              <Square size={16} fill="currentColor" /> Stop Timer
            </button>
          </div>
        ) : (
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Project</label>
              <select 
                className="w-full bg-gray-950 border border-gray-700 rounded-md p-2 text-white"
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
              >
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="flex-2 min-w-[300px]">
              <label className="block text-sm text-gray-400 mb-1">What are you working on?</label>
              <input 
                type="text" 
                className="w-full bg-gray-950 border border-gray-700 rounded-md p-2 text-white"
                placeholder="Description"
                value={timerDesc}
                onChange={(e) => setTimerDesc(e.target.value)}
              />
            </div>
            <button 
              onClick={handleStartTimer}
              disabled={!selectedProject}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md font-medium flex items-center gap-2"
            >
              <Play size={16} fill="currentColor" /> Start
            </button>
          </div>
        )}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-gray-800">
          <h2 className="text-lg font-bold text-white">Recent Worklogs</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-800 text-gray-400 text-sm">
              <tr>
                <th className="p-4">Date</th>
                <th className="p-4">Description</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Source</th>
                <th className="p-4">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {entries.map(entry => {
                const proj = projects.find(p => p.id === entry.project_id);
                return (
                  <tr key={entry.id} className="hover:bg-gray-800/50">
                    <td className="p-4 text-gray-300">
                      {new Date(entry.started_at).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      <div className="text-white">{entry.description || "No description"}</div>
                      <div className="text-xs text-gray-500">{proj?.name}</div>
                    </td>
                    <td className="p-4 text-blue-400 font-medium">
                      {formatTime(entry.duration_seconds)}
                    </td>
                    <td className="p-4">
                      <span className={`text-xs px-2 py-1 rounded-full ${entry.source === 'TIMER' ? 'bg-blue-900/30 text-blue-400 border border-blue-800' : 'bg-gray-800 text-gray-400 border border-gray-700'}`}>
                        {entry.source}
                      </span>
                    </td>
                    <td className="p-4">
                      <button onClick={() => handleDelete(entry.id)} className="p-1 text-gray-500 hover:text-red-400">
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    No time entries found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function formatTime(secs: number) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}
