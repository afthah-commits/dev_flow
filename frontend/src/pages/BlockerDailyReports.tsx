import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
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
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
                        <AlertTriangle className="w-7 h-7 text-amber-400" />
                        Blocker & Impediment Intelligence
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">Track recurring obstacles, dependencies, and blockers across sprints.</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-xs">Timeframe:</span>
                    <select
                        className="bg-gray-900 text-white border border-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
                        value={days}
                        onChange={(e) => setDays(Number(e.target.value))}
                    >
                        <option value={7}>Last 7 Days</option>
                        <option value={14}>Last 14 Days</option>
                        <option value={30}>Last 30 Days</option>
                    </select>
                </div>
            </div>

            {/* Reports Navigation Tabs */}
            <div className="flex flex-wrap items-center gap-2 text-sm border-b border-gray-800 pb-3">
                <Link
                    to="/reports"
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    Executive & Overview Reports
                </Link>
                <Link
                    to="/daily-reports"
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    My Daily Reports
                </Link>
                <Link
                    to="/daily-reports/team"
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    Team Reports
                </Link>
                <Link
                    to="/daily-reports/weekly"
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    Weekly Summary
                </Link>
                <Link
                    to="/daily-reports/blockers"
                    className="px-3 py-1.5 rounded-md font-medium bg-amber-600/20 text-amber-300 border border-amber-500/30"
                >
                    Blockers Tracker
                </Link>
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
