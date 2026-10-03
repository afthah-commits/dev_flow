import React from 'react';
import { Users, MessageSquare, Activity, Zap } from 'lucide-react';

export default function CollaborationAnalytics() {
  return (
    <div className="p-6 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-6">
          <Users className="w-6 h-6 text-indigo-400" />
          Collaboration Intelligence
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <MetricCard title="Active Contributors" value="12" icon={<Users className="w-5 h-5 text-blue-400" />} />
          <MetricCard title="Comments Created" value="342" icon={<MessageSquare className="w-5 h-5 text-emerald-400" />} />
          <MetricCard title="Avg Response Time" value="45m" icon={<Zap className="w-5 h-5 text-amber-400" />} />
          <MetricCard title="Discussions" value="28" icon={<Activity className="w-5 h-5 text-purple-400" />} />
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 text-center">
        <h3 className="text-xl font-bold text-white mb-2">Collaboration Trends</h3>
        <p className="text-gray-400 mb-6">Visualizations for collaboration metrics.</p>
        <div className="h-64 flex items-center justify-center bg-gray-800/50 rounded border border-gray-800 border-dashed">
          <span className="text-gray-500">Charts placeholder (Recharts)</span>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon }: { title: string, value: string, icon: React.ReactNode }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex items-start justify-between">
      <div>
        <div className="text-gray-400 text-sm mb-1">{title}</div>
        <div className="text-2xl font-bold text-white">{value}</div>
      </div>
      <div className="p-2 bg-gray-800 rounded-lg">
        {icon}
      </div>
    </div>
  );
}
