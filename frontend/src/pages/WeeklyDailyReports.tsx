import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { WeeklySummaryResponse } from '../types/dailyReport';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { BarChart2 } from 'lucide-react';

export default function WeeklyDailyReports() {
    const { currentOrganization } = useOrganization();
    
    // Default to last 7 days start
    const defaultStart = new Date();
    defaultStart.setDate(defaultStart.getDate() - 6);
    const [startDate, setStartDate] = useState(defaultStart.toISOString().split('T')[0]);
    
    const [summary, setSummary] = useState<WeeklySummaryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!currentOrganization) return;
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await dailyReportApi.getWeeklySummary(startDate, currentOrganization.id);
                setSummary(data);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch weekly summary.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [startDate, currentOrganization]);

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
                        <BarChart2 className="w-7 h-7 text-emerald-400" />
                        Weekly Engineering Summary
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">Aggregated completion rates, workload, and trends for a 7-day period.</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-xs">Start Date:</span>
                    <input
                        type="date"
                        className="bg-gray-900 text-white border border-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                    />
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
                    className="px-3 py-1.5 rounded-md font-medium bg-emerald-600/20 text-emerald-300 border border-emerald-500/30"
                >
                    Weekly Summary
                </Link>
                <Link
                    to="/daily-reports/blockers"
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    Blockers Tracker
                </Link>
            </div>

            {error && <div className="p-4 bg-red-900/50 text-red-200 rounded-md mb-6">{error}</div>}

            {loading ? (
                <div className="text-gray-400">Loading weekly summary...</div>
            ) : summary && !error ? (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-gray-800 p-6 rounded-md border border-gray-700">
                            <div className="text-gray-400 mb-2">Total Reports</div>
                            <div className="text-3xl font-bold text-white">{summary.total_reports}</div>
                        </div>
                        <div className="bg-gray-800 p-6 rounded-md border border-gray-700">
                            <div className="text-gray-400 mb-2">Tasks Completed</div>
                            <div className="text-3xl font-bold text-green-400">{summary.completed_tasks}</div>
                        </div>
                        <div className="bg-gray-800 p-6 rounded-md border border-gray-700">
                            <div className="text-gray-400 mb-2">Blockers Raised</div>
                            <div className="text-3xl font-bold text-red-400">{summary.blockers}</div>
                        </div>
                    </div>

                    <div className="bg-gray-800 p-6 rounded-md border border-gray-700 mt-8">
                        <h3 className="font-bold text-white mb-6">Submission Trend</h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={summary.trend}>
                                    <XAxis dataKey="date" stroke="#9ca3af" />
                                    <YAxis stroke="#9ca3af" />
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '4px', color: '#f3f4f6' }}
                                        itemStyle={{ color: '#f3f4f6' }}
                                    />
                                    <Bar dataKey="reports_submitted" fill="#3b82f6" name="Reports" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="completed_tasks" fill="#10b981" name="Completed Tasks" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            ) : null}
        </div>
    );
}
