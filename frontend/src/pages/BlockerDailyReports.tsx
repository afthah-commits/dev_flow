import React, { useEffect, useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { BlockerSummaryResponse } from '../types/dailyReport';
import { AlertTriangle } from 'lucide-react';

export default function BlockerDailyReports() {
    const { currentOrganization } = useOrganization();
    const [days, setDays] = useState(7);
    const [blockers, setBlockers] = useState<BlockerSummaryResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!currentOrganization) return;
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await dailyReportApi.getBlockers(days, currentOrganization.id);
                setBlockers(data);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch blockers.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [days, currentOrganization]);

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <AlertTriangle className="text-red-500" /> Blocker Intelligence
                    </h1>
                    <p className="text-gray-400 mt-1">Track and resolve frequent team blockers.</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-sm">Timeframe:</span>
                    <select
                        className="bg-gray-800 text-white border-gray-700 rounded-md px-3 py-2"
                        value={days}
                        onChange={(e) => setDays(Number(e.target.value))}
                    >
                        <option value={7}>Last 7 Days</option>
                        <option value={14}>Last 14 Days</option>
                        <option value={30}>Last 30 Days</option>
                    </select>
                </div>
            </div>

            {error && <div className="p-4 bg-red-900/50 text-red-200 rounded-md mb-6">{error}</div>}

            {loading ? (
                <div className="text-gray-400">Loading blockers...</div>
            ) : !error && blockers.length === 0 ? (
                <div className="text-center p-12 bg-gray-800 rounded-md border border-gray-700 text-gray-400">
                    <p>No blockers reported in the last {days} days. Great job!</p>
                </div>
            ) : !error && (
                <div className="grid grid-cols-1 gap-4">
                    {blockers.map((b, idx) => (
                        <div key={idx} className="bg-gray-800 p-5 rounded-md border border-gray-700 flex justify-between items-start">
                            <div>
                                <h3 className="text-lg font-medium text-red-400 mb-2">{b.blocker}</h3>
                                <div className="text-sm text-gray-400">
                                    <span className="text-white">Reporters:</span> {b.reporters.join(', ')}
                                </div>
                                <div className="text-sm text-gray-400 mt-1">
                                    <span className="text-white">Latest Report:</span> {b.latest_report_date}
                                </div>
                            </div>
                            <div className="bg-gray-700 px-3 py-1 rounded-full text-sm font-bold text-white">
                                {b.occurrences} {b.occurrences === 1 ? 'occurrence' : 'occurrences'}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
