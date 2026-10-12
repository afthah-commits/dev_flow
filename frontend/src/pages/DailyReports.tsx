import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { dailyReportApi } from '../lib/dailyReportApi';
import { DailyReport } from '../types/dailyReport';
import { useOrganization } from '../contexts/OrganizationContext';
import { Plus, FileText, Calendar, CheckCircle2, ListTodo, AlertTriangle, ArrowRight, RefreshCw, BarChart3 } from 'lucide-react';

export default function DailyReports() {
    const navigate = useNavigate();
    const { currentOrganization } = useOrganization();
    const [reports, setReports] = useState<DailyReport[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!currentOrganization) return;
        fetchReports();
    }, [currentOrganization]);

    const fetchReports = async () => {
        if (!currentOrganization) return;
        setLoading(true);
        setError(null);
        try {
            const data = await dailyReportApi.list(currentOrganization.id);
            const list = Array.isArray(data) ? data : ((data as any)?.items || []);
            setReports(list);
        } catch (err: any) {
            console.error('Failed to load daily reports:', err);
            setError(err?.response?.data?.detail || err.message || 'Failed to load daily reports.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2.5">
                        <Calendar className="w-7 h-7 text-blue-400" />
                        Daily Engineering Reports
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">Track your daily progress, upcoming plans, and blockers.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchReports}
                        className="p-2 text-gray-400 hover:text-white bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-colors"
                        title="Refresh daily reports"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <button
                        onClick={() => navigate('/daily-reports/new')}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 text-sm font-medium transition-colors shadow-sm"
                    >
                        <Plus className="w-4 h-4" />
                        New Report
                    </button>
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
                    className="px-3 py-1.5 rounded-md font-medium bg-blue-600/20 text-blue-300 border border-blue-500/30"
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
                    className="px-3 py-1.5 rounded-md font-medium text-gray-400 hover:text-white hover:bg-gray-900 transition-colors"
                >
                    Blockers Tracker
                </Link>
            </div>

            {/* Loading */}
            {loading && (
                <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-12 text-center text-gray-400 space-y-3">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <p className="text-sm font-medium text-gray-300">Loading your daily reports...</p>
                </div>
            )}

            {/* Error */}
            {!loading && error && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center space-y-4">
                    <p className="text-sm text-red-400">{error}</p>
                    <button
                        onClick={fetchReports}
                        className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* Content */}
            {!loading && !error && (
                <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden shadow-sm">
                    {reports.length === 0 ? (
                        <div className="p-12 text-center text-gray-400 space-y-3">
                            <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center mx-auto">
                                <FileText className="w-6 h-6" />
                            </div>
                            <h3 className="text-base font-semibold text-white">No daily reports recorded yet</h3>
                            <p className="text-sm max-w-sm mx-auto">
                                Record your completed work, upcoming tasks, and any active blockers for today.
                            </p>
                            <button
                                onClick={() => navigate('/daily-reports/new')}
                                className="inline-flex items-center gap-1.5 text-blue-400 hover:text-blue-300 text-sm font-medium pt-2 transition-colors"
                            >
                                <Plus className="w-4 h-4" />
                                Create your first report
                            </button>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-800">
                            {reports.map((report) => (
                                <div 
                                    key={report.id} 
                                    onClick={() => navigate(`/daily-reports/${report.id}`)}
                                    className="p-5 hover:bg-gray-800/50 cursor-pointer flex items-center justify-between transition-colors group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-lg border border-blue-500/20 group-hover:bg-blue-500/20 transition-colors">
                                            <Calendar className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <div className="font-semibold text-white text-base flex items-center gap-2">
                                                {report.report_date}
                                            </div>
                                            <div className="text-xs text-gray-400 flex flex-wrap items-center gap-4 mt-1.5">
                                                <span className="flex items-center gap-1 text-emerald-400">
                                                    <CheckCircle2 className="w-3.5 h-3.5" />
                                                    {report.completed_tasks?.length || 0} completed
                                                </span>
                                                <span className="flex items-center gap-1 text-blue-400">
                                                    <ListTodo className="w-3.5 h-3.5" />
                                                    {report.next_plan?.length || 0} planned
                                                </span>
                                                <span className={`flex items-center gap-1 ${(report.blockers?.length || 0) > 0 && report.blockers[0] !== 'None' ? 'text-amber-400' : 'text-gray-500'}`}>
                                                    <AlertTriangle className="w-3.5 h-3.5" />
                                                    {(report.blockers?.length || 0) > 0 && report.blockers[0] !== 'None' ? `${report.blockers.length} blockers` : 'No blockers'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="text-gray-500 group-hover:text-white transition-colors">
                                        <ArrowRight className="w-4 h-4" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
