import React, { useEffect, useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { WeeklySummaryResponse } from '../types/dailyReport';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

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
        <div className="p-8 max-w-6xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white">Weekly Summary</h1>
                    <p className="text-gray-400">Aggregated metrics for a 7-day period.</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-gray-400 text-sm">Start Date:</span>
                    <input
                        type="date"
                        className="bg-gray-800 text-white border-gray-700 rounded-md px-4 py-2"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                    />
                </div>
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
