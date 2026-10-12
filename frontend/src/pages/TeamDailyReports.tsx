import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { TeamDailyReportResponse, DailyReportSummaryResponse } from '../types/dailyReport';
import { Users, AlertCircle, CheckCircle } from 'lucide-react';

export default function TeamDailyReports() {
    const { currentOrganization } = useOrganization();
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [reports, setReports] = useState<TeamDailyReportResponse[]>([]);
    const [summary, setSummary] = useState<DailyReportSummaryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!currentOrganization) return;
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const [reportsData, summaryData] = await Promise.all([
                    dailyReportApi.getTeamReports(date, currentOrganization.id),
                    dailyReportApi.getDailySummary(date, currentOrganization.id)
                ]);
                setReports(reportsData);
                setSummary(summaryData);
            } catch (err: any) {
                setError(err.message || 'Failed to fetch team reports. Ensure you are an Admin/Owner.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [date, currentOrganization]);

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
                        <Users className="w-7 h-7 text-indigo-400" />
                        Team Daily Reports
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">View and audit daily progress across all team members.</p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400">Date:</span>
                    <input
                        type="date"
                        className="bg-gray-900 text-white border border-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
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
                    className="px-3 py-1.5 rounded-md font-medium bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
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
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    Blockers Tracker
                </Link>
            </div>

            {error && <div className="p-4 bg-red-900/50 text-red-200 rounded-md mb-6">{error}</div>}

            {summary && !error && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-gray-800 p-4 rounded-md border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Total Reports</div>
                        <div className="text-2xl font-bold text-white">{summary.total_reports}</div>
                        <div className="text-xs text-red-400 mt-1">{summary.missing_reports} missing</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-md border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Completed Tasks</div>
                        <div className="text-2xl font-bold text-white">{summary.completed_task_count}</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-md border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Next Plans</div>
                        <div className="text-2xl font-bold text-white">{summary.next_plan_count}</div>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-md border border-gray-700">
                        <div className="text-gray-400 text-sm mb-1">Total Blockers</div>
                        <div className="text-2xl font-bold text-white">{summary.blocker_count}</div>
                    </div>
                </div>
            )}

            {loading ? (
                <div className="text-gray-400">Loading team reports...</div>
            ) : !error && reports.length === 0 ? (
                <div className="text-center p-12 bg-gray-800 rounded-md border border-gray-700 text-gray-400">
                    <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No reports submitted for this date.</p>
                </div>
            ) : !error && (
                <div className="space-y-6">
                    {reports.map((report) => (
                        <div key={report.id} className="bg-gray-800 p-6 rounded-md border border-gray-700">
                            <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-700">
                                <h3 className="font-bold text-lg text-white">{report.author_name}</h3>
                                <span className="text-sm text-gray-400">Submitted at {new Date(report.created_at).toLocaleTimeString()}</span>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div>
                                    <h4 className="flex items-center gap-2 font-semibold text-green-400 mb-2">
                                        <CheckCircle className="w-4 h-4" /> Completed
                                    </h4>
                                    <ul className="list-disc pl-5 text-sm text-gray-300 space-y-1">
                                        {report.completed_tasks.map((t, i) => <li key={i}>{t}</li>)}
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="flex items-center gap-2 font-semibold text-blue-400 mb-2">
                                        Next Plan
                                    </h4>
                                    <ul className="list-disc pl-5 text-sm text-gray-300 space-y-1">
                                        {report.next_plan.map((t, i) => <li key={i}>{t}</li>)}
                                    </ul>
                                </div>
                                <div>
                                    <h4 className="flex items-center gap-2 font-semibold text-red-400 mb-2">
                                        <AlertCircle className="w-4 h-4" /> Blockers
                                    </h4>
                                    {report.blockers.length === 0 || report.blockers[0] === 'None' ? (
                                        <span className="text-sm text-gray-500 italic">None</span>
                                    ) : (
                                        <ul className="list-disc pl-5 text-sm text-red-300 space-y-1">
                                            {report.blockers.map((t, i) => <li key={i}>{t}</li>)}
                                        </ul>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
