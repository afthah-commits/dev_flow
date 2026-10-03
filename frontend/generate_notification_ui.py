import os

content_pref = """import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
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

  if (!prefs) return <DashboardLayout title="Notification Settings"><div className="p-6">Loading...</div></DashboardLayout>;

  return (
    <DashboardLayout title="Notification Settings">
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
    </DashboardLayout>
  );
}
"""

content_center = """import React, { useState, useEffect, useRef } from 'react';
import { notificationApi } from '../lib/notificationApi';
import { Notification } from '../types/notification';
import { Link } from 'react-router-dom';

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadCount();
    const interval = setInterval(loadCount, 60000); // Check every minute
    
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      clearInterval(interval);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (open) {
      loadNotifications();
    }
  }, [open]);

  const loadCount = () => {
    notificationApi.getUnreadCount().then(res => setUnread(res.count)).catch(() => {});
  };

  const loadNotifications = () => {
    notificationApi.getNotifications().then(setNotifications).catch(() => {});
  };

  const handleMarkRead = async (id: string) => {
    await notificationApi.markRead(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    loadCount();
  };

  const handleMarkAllRead = async () => {
    await notificationApi.markAllRead();
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnread(0);
  };

  return (
    <div className="relative" ref={ref}>
      <button 
        onClick={() => setOpen(!open)}
        className="p-2 text-gray-400 hover:text-white relative focus:outline-none"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405C18.21 14.79 18 13.42 18 12V8a6 6 0 10-12 0v4c0 1.42-.21 2.79-.595 3.595L4 17h5m6 0a3 3 0 11-6 0h6z" />
        </svg>
        {unread > 0 && (
          <span className="absolute top-1 right-1 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center">
            {unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl z-50 overflow-hidden flex flex-col max-h-96">
          <div className="p-3 border-b border-gray-700 flex justify-between items-center bg-gray-800">
            <h3 className="font-bold text-white text-sm">Notifications</h3>
            <div className="space-x-3 text-xs">
              <button onClick={handleMarkAllRead} className="text-blue-400 hover:text-blue-300">Mark all read</button>
              <Link to="/settings/notifications" onClick={() => setOpen(false)} className="text-gray-400 hover:text-white">Settings</Link>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-sm text-gray-500">
                No notifications right now.
              </div>
            ) : (
              notifications.map(n => (
                <div key={n.id} className={`p-4 border-b border-gray-800 last:border-b-0 hover:bg-gray-800/50 transition-colors ${n.read ? 'opacity-60' : 'bg-gray-800/20'}`}>
                  <div className="flex justify-between items-start">
                    <h4 className="text-sm font-semibold text-white">{n.title}</h4>
                    {!n.read && (
                      <button onClick={() => handleMarkRead(n.id)} className="text-[10px] text-blue-400 hover:text-blue-300">Mark read</button>
                    )}
                  </div>
                  <p className="text-xs text-gray-300 mt-1">{n.message}</p>
                  <div className="text-[10px] text-gray-500 mt-2">
                    {new Date(n.created_at).toLocaleString()}
                    {n.project_id && <Link to={`/projects/${n.project_id}`} onClick={() => setOpen(false)} className="ml-2 text-blue-500 hover:underline">View Project</Link>}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
"""

with open("c:/personal_projects/devflow/frontend/src/pages/NotificationPreferences.tsx", "w", encoding="utf-8") as f: f.write(content_pref)
with open("c:/personal_projects/devflow/frontend/src/components/NotificationCenter.tsx", "w", encoding="utf-8") as f: f.write(content_center)

print("Notification UI created")
