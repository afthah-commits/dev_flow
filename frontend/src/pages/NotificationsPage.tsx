import React, { useState, useEffect, useCallback } from 'react';
import { notificationApi } from '../lib/notificationApi';
import { useRealtimeEvent } from '../hooks/useRealtime';
import { Notification } from '../types/notification';
import { Link } from 'react-router-dom';

type TabKey = 'all' | 'unread' | 'important' | 'action_required';

const NOTIFICATION_TYPES = [
  'TASK_OVERDUE', 'TASK_DUE_SOON', 'PROJECT_DEADLINE', 'PROJECT_AT_RISK',
  'DAILY_REPORT_REMINDER', 'DAILY_REPORT_BLOCKER',
  'RELEASE_APPROVAL_REQUESTED', 'RELEASE_APPROVED', 'RELEASE_REJECTED', 'RELEASE_PROMOTED', 'RELEASE_ROLLBACK',
  'DEPLOYMENT_STARTED', 'DEPLOYMENT_SUCCESS', 'DEPLOYMENT_FAILED', 'DEPLOYMENT_ROLLBACK',
  'JOB_FAILURE', 'AUTOMATION_FAILURE',
  'WORKFLOW_APPROVAL_REQUESTED', 'WORKFLOW_APPROVED', 'WORKFLOW_REJECTED',
  'CLIENT_REQUEST_CREATED', 'CLIENT_REQUEST_UPDATED',
  'TEAM_ACTIVITY', 'GITHUB_PR', 'GITHUB_ISSUE', 'GITHUB_ACTIVITY', 'AI_INSIGHT',
];

const priorityColors: Record<string, string> = {
  LOW: 'text-gray-400 bg-gray-800',
  NORMAL: 'text-blue-400 bg-blue-900/30',
  HIGH: 'text-orange-400 bg-orange-900/30',
  URGENT: 'text-red-400 bg-red-900/30',
};

const typeColors: Record<string, string> = {
  JOB_FAILURE: 'bg-red-900/40 text-red-300',
  AUTOMATION_FAILURE: 'bg-red-900/40 text-red-300',
  DEPLOYMENT_FAILED: 'bg-red-900/40 text-red-300',
  WORKFLOW_APPROVAL_REQUESTED: 'bg-purple-900/40 text-purple-300',
  RELEASE_APPROVAL_REQUESTED: 'bg-purple-900/40 text-purple-300',
  DAILY_REPORT_BLOCKER: 'bg-yellow-900/40 text-yellow-300',
};

export default function NotificationsPage() {
  const [tab, setTab] = useState<TabKey>('all');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const LIMIT = 30;

  const buildParams = useCallback((offset: number) => {
    const p: Parameters<typeof notificationApi.getNotifications>[0] = { skip: offset, limit: LIMIT };
    if (tab === 'unread') p.unread_only = true;
    if (tab === 'important') p.important = true;
    if (tab === 'action_required') p.action_required = true;
    if (typeFilter) p.notification_type = typeFilter;
    if (dateFrom) p.date_from = new Date(`${dateFrom}T00:00:00`).toISOString();
    if (dateTo) p.date_to = new Date(`${dateTo}T23:59:59`).toISOString();
    return p;
  }, [tab, typeFilter, dateFrom, dateTo]);

  const load = useCallback(async (reset = false) => {
    setLoading(true);
    const offset = reset ? 0 : skip;
    try {
      const data = await notificationApi.getNotifications(buildParams(offset));
      if (reset) {
        setNotifications(data);
        setSkip(data.length);
      } else {
        setNotifications(prev => [...prev, ...data]);
        setSkip(prev => prev + data.length);
      }
      setHasMore(data.length === LIMIT);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [skip, buildParams]);

  useEffect(() => {
    setSkip(0);
    setHasMore(true);
    load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, typeFilter, dateFrom, dateTo]);

  useRealtimeEvent('notification.created', useCallback(() => {
    load(true);
  }, [load]));

  const handleMarkRead = async (id: string) => {
    await notificationApi.markRead(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const handleMarkUnread = async (id: string) => {
    await notificationApi.markUnread(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: false } : n));
  };

  const handleToggleImportant = async (id: string, important: boolean) => {
    if (important) {
      await notificationApi.markUnimportant(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, important: false } : n));
    } else {
      await notificationApi.markImportant(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, important: true } : n));
    }
  };

  const handleDelete = async (id: string) => {
    await notificationApi.delete(id);
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleMarkAllRead = async () => {
    await notificationApi.markAllRead();
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'unread', label: 'Unread' },
    { key: 'important', label: '⭐ Important' },
    { key: 'action_required', label: '⚡ Action Required' },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Notifications</h1>
          <p className="text-sm text-gray-400 mt-1">Manage your notifications across all systems</p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/action-center"
            className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white text-sm rounded-lg transition-colors"
          >
            ⚡ Action Center
          </Link>
          <button
            onClick={handleMarkAllRead}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
          >
            Mark all read
          </button>
        </div>
      </div>

      {/* Tabs + Filters */}
      <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
        <div className="flex border-b border-gray-700 overflow-x-auto">
          {tabs.map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                tab === t.key
                  ? 'border-b-2 border-blue-500 text-blue-400 bg-gray-800'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Type filter */}
        <div className="px-4 py-2 border-b border-gray-700 bg-gray-800/50 flex items-center gap-3">
          <label htmlFor="notification-type-filter" className="text-xs text-gray-400 shrink-0">Filter by type:</label>
          <select
            id="notification-type-filter"
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            className="bg-gray-800 text-gray-200 text-xs border border-gray-600 rounded px-2 py-1 focus:outline-none focus:border-blue-500"
          >
            <option value="">All types</option>
            {NOTIFICATION_TYPES.map(t => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>
          {typeFilter && (
            <button onClick={() => setTypeFilter('')} className="text-xs text-gray-500 hover:text-white">✕ Clear</button>
          )}
        </div>

        {/* Date range filter */}
        <div className="px-4 py-2 border-b border-gray-700 bg-gray-800/50 flex items-center gap-3">
          <label className="text-xs text-gray-400 shrink-0">Date range:</label>
          <input
            type="date"
            aria-label="Date from"
            value={dateFrom}
            onChange={e => setDateFrom(e.target.value)}
            className="bg-gray-800 text-gray-200 text-xs border border-gray-600 rounded px-2 py-1 focus:outline-none focus:border-blue-500"
          />
          <span className="text-xs text-gray-500">→</span>
          <input
            type="date"
            aria-label="Date to"
            value={dateTo}
            onChange={e => setDateTo(e.target.value)}
            className="bg-gray-800 text-gray-200 text-xs border border-gray-600 rounded px-2 py-1 focus:outline-none focus:border-blue-500"
          />
          {(dateFrom || dateTo) && (
            <button
              onClick={() => { setDateFrom(''); setDateTo(''); }}
              className="text-xs text-gray-500 hover:text-white"
            >✕ Clear</button>
          )}
        </div>

        {/* Notification list */}
        <div>
          {loading && notifications.length === 0 ? (
            <div className="p-12 text-center text-gray-500">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500 text-lg">No notifications</p>
              <p className="text-gray-600 text-sm mt-1">You're all caught up!</p>
            </div>
          ) : (
            <>
              {notifications.map(n => (
                <div
                  key={n.id}
                  className={`px-4 py-3 border-b border-gray-800 last:border-b-0 transition-colors hover:bg-gray-800/30 ${
                    !n.read ? 'bg-gray-800/20 border-l-2 border-l-blue-500' : ''
                  }`}
                >
                  <div className="flex gap-3">
                    {/* Unread indicator */}
                    <div className="shrink-0 mt-1">
                      {!n.read
                        ? <span className="w-2 h-2 rounded-full bg-blue-500 block" />
                        : <span className="w-2 h-2 block" />
                      }
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-1.5 mb-1">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${priorityColors[n.priority] || priorityColors.NORMAL}`}>
                          {n.priority}
                        </span>
                        <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${typeColors[n.type] || 'bg-gray-800 text-gray-400'}`}>
                          {n.type.replace(/_/g, ' ')}
                        </span>
                        {n.action_required && (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-orange-900/40 text-orange-300">⚡ ACTION</span>
                        )}
                        {n.important && (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-yellow-900/40 text-yellow-300">⭐ IMPORTANT</span>
                        )}
                        <h4 className="text-sm font-semibold text-white">{n.title}</h4>
                      </div>
                      <p className="text-xs text-gray-300">{n.message}</p>
                      <p className="text-[10px] text-gray-500 mt-1">
                        {new Date(n.created_at).toLocaleString()}
                        {n.read_at && ` · Read ${new Date(n.read_at).toLocaleDateString()}`}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="shrink-0 flex flex-col gap-1 items-end">
                      <button
                        onClick={() => handleToggleImportant(n.id, n.important)}
                        className={`text-sm transition-colors ${n.important ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-400'}`}
                        title={n.important ? 'Unmark important' : 'Mark important'}
                      >⭐</button>
                      <div className="flex gap-2 text-xs">
                        {!n.read ? (
                          <button onClick={() => handleMarkRead(n.id)} className="text-blue-400 hover:text-blue-300">Read</button>
                        ) : (
                          <button onClick={() => handleMarkUnread(n.id)} className="text-gray-500 hover:text-gray-300">Unread</button>
                        )}
                        <button onClick={() => handleDelete(n.id)} className="text-red-500/60 hover:text-red-400">Delete</button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* Load more */}
              {hasMore && (
                <div className="p-4 text-center">
                  <button
                    onClick={() => load(false)}
                    disabled={loading}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-gray-200 rounded-lg disabled:opacity-50"
                  >
                    {loading ? 'Loading...' : 'Load more'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
