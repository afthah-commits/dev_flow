import React, { useEffect, useState } from 'react';
import { notificationApi } from '../lib/notificationApi';
import { NotificationPreference } from '../types/notification';

export function NotificationPreferences() {
  const [prefs, setPrefs] = useState<NotificationPreference | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    notificationApi.getPreferences().then(setPrefs).catch(console.error);
  }, []);

  const handleChange = (key: keyof NotificationPreference, val: boolean) => {
    if (!prefs) return;
    setPrefs({ ...prefs, [key]: val });
  };

  const handleSave = async () => {
    if (!prefs) return;
    setSaving(true);
    try {
      await notificationApi.updatePreferences(prefs);
      alert('Preferences saved');
    } catch (e) {
      alert('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (!prefs) return <div className="p-6">Loading...</div>;

  return (
    <div className="max-w-2xl mx-auto p-6 bg-gray-900 border border-gray-800 rounded-lg mt-8">
      <h2 className="text-xl font-bold text-white mb-6">Notification Preferences</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Task Notifications</div>
            <div className="text-sm text-gray-400">Alerts for task changes and mentions.</div>
          </div>
          <input type="checkbox" checked={prefs.task_notifications} onChange={(e) => handleChange('task_notifications', e.target.checked)} className="w-5 h-5" />
        </div>
        
        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Deadline Notifications</div>
            <div className="text-sm text-gray-400">Alerts for due soon and overdue tasks.</div>
          </div>
          <input type="checkbox" checked={prefs.deadline_notifications} onChange={(e) => handleChange('deadline_notifications', e.target.checked)} className="w-5 h-5" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Project Health</div>
            <div className="text-sm text-gray-400">Alerts when projects go At Risk.</div>
          </div>
          <input type="checkbox" checked={prefs.project_health_notifications} onChange={(e) => handleChange('project_health_notifications', e.target.checked)} className="w-5 h-5" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">GitHub Activity</div>
            <div className="text-sm text-gray-400">Alerts for PRs and issues.</div>
          </div>
          <input type="checkbox" checked={prefs.github_notifications} onChange={(e) => handleChange('github_notifications', e.target.checked)} className="w-5 h-5" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">AI Insights</div>
            <div className="text-sm text-gray-400">Automated project insights from AI.</div>
          </div>
          <input type="checkbox" checked={prefs.ai_notifications} onChange={(e) => handleChange('ai_notifications', e.target.checked)} className="w-5 h-5" />
        </div>
        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Task Assignments</div>
            <div className="text-sm text-gray-400">Alerts when you are assigned to a task.</div>
          </div>
          <input type="checkbox" checked={prefs.task_assignments} onChange={(e) => handleChange('task_assignments', e.target.checked)} className="w-5 h-5 rounded border-gray-600 bg-gray-900" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Sprint Events</div>
            <div className="text-sm text-gray-400">Alerts for sprint starts and completions.</div>
          </div>
          <input type="checkbox" checked={prefs.sprint_events} onChange={(e) => handleChange('sprint_events', e.target.checked)} className="w-5 h-5 rounded border-gray-600 bg-gray-900" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Milestone Events</div>
            <div className="text-sm text-gray-400">Alerts for milestone changes.</div>
          </div>
          <input type="checkbox" checked={prefs.milestone_events} onChange={(e) => handleChange('milestone_events', e.target.checked)} className="w-5 h-5 rounded border-gray-600 bg-gray-900" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Security & Audit Events</div>
            <div className="text-sm text-gray-400">Alerts for organization role changes and critical settings.</div>
          </div>
          <input type="checkbox" checked={prefs.security_events} onChange={(e) => handleChange('security_events', e.target.checked)} className="w-5 h-5 rounded border-gray-600 bg-gray-900" />
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-800 rounded">
          <div>
            <div className="text-white font-medium">Email Digests</div>
            <div className="text-sm text-gray-400">Receive a daily summary email of missed notifications.</div>
          </div>
          <input type="checkbox" checked={prefs.digest_notifications} onChange={(e) => handleChange('digest_notifications', e.target.checked)} className="w-5 h-5 rounded border-gray-600 bg-gray-900" />
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button 
          onClick={handleSave} 
          disabled={saving}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </div>
    </div>
  );
}
