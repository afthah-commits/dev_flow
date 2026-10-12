import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { DailyReport } from '../types/dailyReport';
import { ArrowLeft, Edit, Download, Calendar, CheckCircle2, ListTodo, AlertTriangle } from 'lucide-react';

export default function DailyReportDetails() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { currentOrganization } = useOrganization();
    const [report, setReport] = useState<DailyReport | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id || !currentOrganization) return;
        const fetchReport = async () => {
            try {
                const data = await dailyReportApi.get(id, currentOrganization.id);
                setReport(data);
            } catch (err) {
                setError('Failed to load report');
            }
        };
        fetchReport();
    }, [id, currentOrganization]);

    const handleExport = async () => {
        if (!id || !currentOrganization) return;
        try {
            const blob = await dailyReportApi.export(id, 'csv', currentOrganization.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `report_${report?.report_date}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Failed to export:', err);
        }
    };

    if (error) {
        return (
            <div className="max-w-4xl mx-auto p-8">
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center space-y-4">
                    <p className="text-red-400 font-medium">{error}</p>
                    <button
                        onClick={() => navigate('/daily-reports')}
                        className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-sm transition-colors"
                    >
                        Back to Daily Reports
                    </button>
                </div>
            </div>
        );
    }

    if (!report) {
        return (
            <div className="max-w-4xl mx-auto p-12 text-center text-gray-400 space-y-3">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-sm">Loading report details...</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-gray-800">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/daily-reports')}
                        className="p-2 hover:bg-gray-800 text-gray-400 hover:text-white rounded-lg transition-colors border border-gray-800"
                        title="Back to Reports"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                            <Calendar className="w-6 h-6 text-blue-400" />
                            Daily Standup Report
                        </h1>
                        <p className="text-sm text-gray-400">Date: {report.report_date}</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-3.5 py-2 bg-gray-900 border border-gray-800 hover:bg-gray-800 text-gray-200 text-sm font-medium rounded-lg transition-colors shadow-sm"
                    >
                        <Download className="w-4 h-4 text-gray-400" />
                        Export CSV
                    </button>
                    <button
                        onClick={() => navigate(`/daily-reports/${id}/edit`)}
                        className="flex items-center gap-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
                    >
                        <Edit className="w-4 h-4" />
                        Edit Report
                    </button>
                </div>
            </div>

            <div className="bg-gray-900 p-6 sm:p-8 rounded-xl border border-gray-800 shadow-sm space-y-8">
                <div>
                    <h2 className="text-base font-semibold border-b border-gray-800 pb-3 mb-4 text-emerald-400 flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5" />
                        Completed Tasks
                    </h2>
                    {report.completed_tasks.length === 0 ? (
                        <p className="text-gray-500 text-sm italic">None recorded</p>
                    ) : (
                        <ul className="space-y-2">
                            {report.completed_tasks.map((task, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                                    <span className="text-emerald-500 mt-1">•</span>
                                    <span>{task}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h2 className="text-base font-semibold border-b border-gray-800 pb-3 mb-4 text-blue-400 flex items-center gap-2">
                        <ListTodo className="w-5 h-5" />
                        Next Plan
                    </h2>
                    {report.next_plan.length === 0 ? (
                        <p className="text-gray-500 text-sm italic">None recorded</p>
                    ) : (
                        <ul className="space-y-2">
                            {report.next_plan.map((plan, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-gray-200">
                                    <span className="text-blue-500 mt-1">•</span>
                                    <span>{plan}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h2 className="text-base font-semibold border-b border-gray-800 pb-3 mb-4 text-amber-400 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5" />
                        Blockers & Impediments
                    </h2>
                    {report.blockers.length === 0 || (report.blockers.length === 1 && report.blockers[0] === 'None') ? (
                        <p className="text-gray-500 text-sm italic">No blockers reported</p>
                    ) : (
                        <ul className="space-y-2">
                            {report.blockers.map((blocker, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-amber-200/90 bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/20">
                                    <span>{blocker}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}
