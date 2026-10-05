import React, { useEffect, useState } from 'react';
import { releaseApi } from '../lib/releaseApi';
import { ReleaseReadiness as ReleaseReadinessType } from '../types/release';
import { CheckCircle2, AlertTriangle, XCircle, Activity } from 'lucide-react';

export default function ReleaseReadiness({ releaseId }: { releaseId: string }) {
  const [readiness, setReadiness] = useState<ReleaseReadinessType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    releaseApi.getReadiness(releaseId)
      .then(setReadiness)
      .finally(() => setLoading(false));
  }, [releaseId]);

  if (loading) return <div className="text-gray-500 animate-pulse">Calculating readiness...</div>;
  if (!readiness) return null;

  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-400';
    if (s >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-white flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Release Readiness {readiness.ready ? "(READY)" : "(NOT READY)"}
        </h3>
        <div className={`text-3xl font-bold ${getScoreColor(readiness.score)}`}>
          {readiness.score}
        </div>
      </div>
      
      <div className="space-y-2">
        {readiness.checks.map((check, i) => (
          <div key={i} className="flex items-start gap-2 text-sm text-gray-300">
            {check.status === 'WARNING' ? (
              <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
            ) : check.status === 'PASS' ? (
              <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            )}
            <div>
              <span className="font-medium">{check.name}:</span> {check.message}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
