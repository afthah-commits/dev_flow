import React, { useState, useEffect, useCallback } from 'react';
import { notificationApi } from '../lib/notificationApi';
import { useRealtimeEvent } from '../hooks/useRealtime';
import { ActionItem, NotificationSummary } from '../types/notification';
import { Link, useNavigate } from 'react-router-dom';

const ACTION_TYPE_ICONS: Record<string, string> = {
  WORKFLOW_APPROVAL: '📋',
  RELEASE_APPROVAL: '🚀',
  JOB_FAILURE: '❌',
  DEPLOYMENT_FAILURE: '💥',
  DAILY_REPORT_BLOCKER: '🚧',
  NOTIFICATION: '🔔',
};

const ACTION_TYPE_COLORS: Record<string, string> = {
  WORKFLOW_APPROVAL: 'border-l-purple-500 bg-purple-900/10',
  RELEASE_APPROVAL: 'border-l-blue-500 bg-blue-900/10',
  JOB_FAILURE: 'border-l-red-500 bg-red-900/10',
  DEPLOYMENT_FAILURE: 'border-l-red-500 bg-red-900/10',
  DAILY_REPORT_BLOCKER: 'border-l-yellow-500 bg-yellow-900/10',
  NOTIFICATION: 'border-l-gray-500 bg-gray-800/20',
};

const PRIORITY_BADGE: Record<string, string> = {
  URGENT: 'bg-red-900/40 text-red-300',
  HIGH: 'bg-orange-900/40 text-orange-300',
  NORMAL: 'bg-blue-900/30 text-blue-300',
  LOW: 'bg-gray-800 text-gray-400',
};

export default function ActionCenter() {
  const [items, setItems] = useState<ActionItem[]>([]);
  const [summary, setSummary] = useState<NotificationSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [actionItems, sum] = await Promise.all([
        notificationApi.getActionCenter(),
        notificationApi.getSummary(),
      ]);
      setItems(actionItems);
      setSummary(sum);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  useRealtimeEvent('action_item.created', useCallback(() => {
    loadAll();
  }, [loadAll]));

  useRealtimeEvent('notification.created', useCallback(() => {
    loadAll();
  }, [loadAll]));

  const groupedItems = items.reduce<Record<string, ActionItem[]>>((acc, item) => {
    if (!acc[item.type]) acc[item.type] = [];
    acc[item.type].push(item);
    return acc;
  }, {});

  const typeOrder = ['WORKFLOW_APPROVAL', 'RELEASE_APPROVAL', 'JOB_FAILURE', 'DEPLOYMENT_FAILURE', 'DAILY_REPORT_BLOCKER', 'NOTIFICATION'];
  const orderedTypes = [
    ...typeOrder.filter(t => groupedItems[t]),
    ...Object.keys(groupedItems).filter(t => !typeOrder.includes(t)),
  ];

  const typeLabel = (type: string) => {
    const map: Record<string, string> = {
      WORKFLOW_APPROVAL: 'Workflow Approvals',
      RELEASE_APPROVAL: 'Release Approvals',
      JOB_FAILURE: 'Failed Jobs',
      DEPLOYMENT_FAILURE: 'Deployment Failures',
      DAILY_REPORT_BLOCKER: 'Daily Report Blockers',
      NOTIFICATION: 'Action Notifications',
    };
    return map[type] || type.replace(/_/g, ' ');
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">⚡ Action Center</h1>
          <p className="text-sm text-gray-400 mt-1">Items requiring your attention</p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/notifications"
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
          >
            All Notifications
          </Link>
          <button
            onClick={loadAll}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Summary counts */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
          {[
            { label: 'Unread', value: summary.unread, color: 'blue' },
            { label: 'Important', value: summary.important, color: 'yellow' },
            { label: 'Action Required', value: summary.action_required, color: 'orange' },
            { label: 'Pending Approvals', value: summary.pending_approvals, color: 'purple' },
            { label: 'Failed Jobs', value: summary.failed_jobs, color: 'red' },
          ].map(s => (
            <div key={s.label} className={`bg-gray-900 border border-gray-700 rounded-lg p-3 text-center`}>
              <p className={`text-2xl font-bold text-${s.color}-400`}>{s.value}</p>
              <p className="text-xs text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Action items */}
      {loading && items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">Loading action items...</div>
      ) : items.length === 0 ? (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-12 text-center">
          <div className="text-5xl mb-4">✅</div>
          <h3 className="text-lg font-semibold text-white mb-2">All clear!</h3>
          <p className="text-gray-500">No action items requiring your attention right now.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {orderedTypes.map(type => (
            <div key={type} className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
              <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center gap-2">
                <span className="text-lg">{ACTION_TYPE_ICONS[type] || '📌'}</span>
                <h2 className="font-semibold text-white text-sm">{typeLabel(type)}</h2>
                <span className="ml-auto text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full">
                  {groupedItems[type].length}
                </span>
              </div>
              <div>
                {groupedItems[type].map(item => (
                  <div
                    key={item.id}
                    className={`px-4 py-3 border-b border-gray-800 last:border-b-0 border-l-2 ${ACTION_TYPE_COLORS[item.type] || ''} flex gap-3 hover:bg-gray-800/20 transition-colors`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${PRIORITY_BADGE[item.priority] || PRIORITY_BADGE.NORMAL}`}>
                          {item.priority}
                        </span>
                        <h4 className="text-sm font-semibold text-white">{item.title}</h4>
                      </div>
                      <p className="text-xs text-gray-300">{item.description}</p>
                      <p className="text-[10px] text-gray-500 mt-1">
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                    {item.action_url && (
                      <div className="shrink-0 flex items-center">
                        <button
                          onClick={() => navigate(item.action_url!)}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded transition-colors whitespace-nowrap"
                        >
                          Open →
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
