import React from 'react';
import { Link } from 'react-router-dom';
import { Users, MessageSquare, Activity, Zap } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const mockTrendData = [
  { day: 'Mon', discussions: 4, comments: 45, reviews: 12 },
  { day: 'Tue', discussions: 7, comments: 62, reviews: 18 },
  { day: 'Wed', discussions: 5, comments: 55, reviews: 15 },
  { day: 'Thu', discussions: 9, comments: 80, reviews: 24 },
  { day: 'Fri', discussions: 6, comments: 68, reviews: 20 },
  { day: 'Sat', discussions: 2, comments: 18, reviews: 5 },
  { day: 'Sun', discussions: 1, comments: 14, reviews: 4 },
];

export default function CollaborationAnalytics() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-gray-800">
        <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
          <Users className="w-7 h-7 text-indigo-400" />
          Collaboration Intelligence
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Team communication velocity, peer review activity, and discussion engagement.
        </p>
      </div>

      {/* Analytics Sub-tabs */}
      <div className="flex flex-wrap items-center gap-2 text-sm border-b border-gray-800 pb-3">
        <Link
          to="/analytics/productivity"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Productivity
        </Link>
        <Link
          to="/analytics/delivery"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Delivery & DORA
        </Link>
        <Link
          to="/analytics/collaboration"
          className="px-3 py-1.5 rounded-md font-medium bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
        >
          Collaboration
        </Link>
        <Link
          to="/analytics/knowledge"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Knowledge Base
        </Link>
        <Link
          to="/analytics/workflows"
          className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
        >
          Workflows
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard title="Active Contributors" value="12" icon={<Users className="w-5 h-5 text-blue-400" />} />
        <MetricCard title="Comments Created" value="342" icon={<MessageSquare className="w-5 h-5 text-emerald-400" />} />
        <MetricCard title="Avg Response Time" value="45m" icon={<Zap className="w-5 h-5 text-amber-400" />} />
        <MetricCard title="Discussions" value="28" icon={<Activity className="w-5 h-5 text-purple-400" />} />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-sm space-y-4">
        <div>
          <h3 className="text-base font-semibold text-white">Weekly Communication Trends</h3>
          <p className="text-xs text-gray-400">Activity volume across pull request reviews, discussions, and task comments.</p>
        </div>

        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mockTrendData}>
              <defs>
                <linearGradient id="colorComments" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
              <XAxis dataKey="day" stroke="#9ca3af" fontSize={12} tickLine={false} />
              <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#fff' }}
              />
              <Area type="monotone" dataKey="comments" stroke="#6366f1" fillOpacity={1} fill="url(#colorComments)" name="Comments" />
              <Area type="monotone" dataKey="reviews" stroke="#10b981" fillOpacity={0.2} fill="#10b981" name="Reviews" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon }: { title: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-start justify-between shadow-sm">
      <div className="space-y-1">
        <div className="text-gray-400 text-xs font-medium">{title}</div>
        <div className="text-xl sm:text-2xl font-bold text-white">{value}</div>
      </div>
      <div className="p-2 bg-gray-800 rounded-lg">
        {icon}
      </div>
    </div>
  );
}
