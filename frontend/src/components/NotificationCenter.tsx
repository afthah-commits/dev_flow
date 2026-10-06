import React, { useState, useEffect, useRef, useCallback } from 'react';
import { notificationApi } from '../lib/notificationApi';
import { useRealtimeEvent } from '../hooks/useRealtime';
import { Notification } from '../types/notification';
import { Link } from 'react-router-dom';

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  const [filter, setFilter] = useState<{
    priority?: string;
    unread_only?: boolean;
    entity_type?: string;
    important?: boolean;
    action_required?: boolean;
  }>({});

  const loadCount = useCallback(() => {
    notificationApi.getUnreadCount().then(res => setUnread(res.count)).catch(() => {});
  }, []);

  const loadNotifications = useCallback(() => {
    notificationApi.getNotifications({ ...filter, limit: 30 }).then(setNotifications).catch(() => {});
  }, [filter]);

  useEffect(() => {
    loadCount();
    const interval = setInterval(loadCount, 60000);
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      clearInterval(interval);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [loadCount]);

  useEffect(() => {
    if (open) loadNotifications();
  }, [open, loadNotifications]);

  // Phase 36: realtime updates via WebSocket
  useRealtimeEvent('notification.created', useCallback(() => {
    loadCount();
    if (open) loadNotifications();
  }, [open, loadCount, loadNotifications]));

  const refreshBadge = useCallback(() => {
    loadCount();
    if (open) loadNotifications();
  }, [open, loadCount, loadNotifications]);

  useRealtimeEvent('notification.read', refreshBadge);
  useRealtimeEvent('notification.updated', refreshBadge);
  useRealtimeEvent('notification.deleted', refreshBadge);
  useRealtimeEvent('notification.read_all', refreshBadge);

  const handleMarkRead = async (id: string) => {
    await notificationApi.markRead(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    loadCount();
  };

  const handleMarkUnread = async (id: string) => {
    await notificationApi.markUnread(id);
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: false } : n));
    loadCount();
  };

  const handleToggleImportant = async (id: string, currentImportant: boolean) => {
    if (currentImportant) {
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
    loadCount();
  };

  const handleMarkAllRead = async () => {
    await notificationApi.markAllRead();
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnread(0);
  };

  const priorityColors: Record<string, string> = {
    LOW: 'text-gray-400 bg-gray-900',
    NORMAL: 'text-blue-400 bg-blue-900/30',
    HIGH: 'text-orange-400 bg-orange-900/30',
    URGENT: 'text-red-400 bg-red-900/30',
  };

  const filterBtnClass = (active: boolean, color = 'gray') =>
    `text-xs px-2 py-1 rounded-full border transition-colors ${
      active
        ? `bg-${color}-700 text-white border-${color}-600`
        : 'bg-transparent text-gray-400 border-gray-700 hover:bg-gray-800'
    }`;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="p-2 text-gray-400 hover:text-white relative focus:outline-none"
        aria-label="Open notifications"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
            d="M15 17h5l-1.405-1.405C18.21 14.79 18 13.42 18 12V8a6 6 0 10-12 0v4c0 1.42-.21 2.79-.595 3.595L4 17h5m6 0a3 3 0 11-6 0h6z" />
        </svg>
        {unread > 0 && (
          <span className="absolute top-1 right-1 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center leading-none">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-96 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl z-50 overflow-hidden flex flex-col max-h-[36rem]">
          {/* Header */}
          <div className="p-3 border-b border-gray-700 flex justify-between items-center bg-gray-800 shrink-0">
            <h3 className="font-bold text-white text-sm">Notifications</h3>
            <div className="flex items-center gap-3 text-xs">
              <button onClick={handleMarkAllRead} className="text-blue-400 hover:text-blue-300">Mark all read</button>
              <Link to="/notifications" onClick={() => setOpen(false)} className="text-gray-400 hover:text-white">View all</Link>
              <Link to="/settings/notifications" onClick={() => setOpen(false)} className="text-gray-400 hover:text-white">Settings</Link>
            </div>
          </div>

          {/* Filters */}
          <div className="px-3 py-2 bg-gray-800 border-b border-gray-700 shrink-0 overflow-x-auto">
            <div className="flex gap-2 min-w-max">
              <button onClick={() => setFilter({})} className={filterBtnClass(Object.keys(filter).length === 0)}>All</button>
              <button onClick={() => setFilter({ unread_only: true })} className={filterBtnClass(!!filter.unread_only)}>Unread</button>
              <button onClick={() => setFilter({ important: true })} className={filterBtnClass(filter.important === true, 'yellow')}>⭐ Important</button>
              <button onClick={() => setFilter({ action_required: true })} className={filterBtnClass(filter.action_required === true, 'orange')}>⚡ Action</button>
              <button onClick={() => setFilter({ priority: 'HIGH' })} className={filterBtnClass(filter.priority === 'HIGH', 'orange')}>High Priority</button>
            </div>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">No notifications matching filters.</div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-3 border-b border-gray-800 last:border-b-0 hover:bg-gray-800/50 transition-colors ${n.read ? 'opacity-60' : 'bg-gray-800/20'}`}
                >
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                        {!n.read && <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />}
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${priorityColors[n.priority] || priorityColors.NORMAL}`}>
                          {n.priority}
                        </span>
                        {n.action_required && (
                          <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-orange-900/40 text-orange-300">ACTION</span>
                        )}
                        <h4 className="text-sm font-semibold text-white truncate">{n.title}</h4>
                      </div>
                      <p className="text-xs text-gray-300 line-clamp-2">{n.message}</p>
                    </div>

                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <div className="flex gap-1 text-[10px]">
                        <button
                          onClick={() => handleToggleImportant(n.id, n.important)}
                          className={`hover:text-yellow-300 transition-colors ${n.important ? 'text-yellow-400' : 'text-gray-600'}`}
                          title={n.important ? 'Unmark important' : 'Mark important'}
                        >⭐</button>
                        {!n.read ? (
                          <button onClick={() => handleMarkRead(n.id)} className="text-blue-400 hover:text-blue-300">Read</button>
                        ) : (
                          <button onClick={() => handleMarkUnread(n.id)} className="text-gray-500 hover:text-gray-300">Unread</button>
                        )}
                        <button onClick={() => handleDelete(n.id)} className="text-red-400/70 hover:text-red-400">×</button>
                      </div>
                      <span className="text-[10px] text-gray-500">
                        {new Date(n.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-700 bg-gray-800 p-2 flex justify-between text-xs shrink-0">
            <Link to="/notifications" onClick={() => setOpen(false)} className="text-blue-400 hover:text-blue-300">
              All notifications →
            </Link>
            <Link to="/action-center" onClick={() => setOpen(false)} className="text-orange-400 hover:text-orange-300">
              ⚡ Action Center
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
