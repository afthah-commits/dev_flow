import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { DailyReport } from '../types/dailyReport';
import { ArrowLeft, Edit, Download } from 'lucide-react';

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

    if (error) return <div className="p-8 text-red-600">{error}</div>;
    if (!report) return <div className="p-8">Loading...</div>;

    return (
        <div className="p-8 max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/daily-reports')} className="p-2 hover:bg-gray-100 rounded-md">
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-2xl font-bold">Daily Report</h1>
                        <p className="text-gray-500">Date: {report.report_date}</p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-gray-50 text-sm font-medium"
                    >
                        <Download className="w-4 h-4" /> Export CSV
                    </button>
                    <button
                        onClick={() => navigate(`/daily-reports/${id}/edit`)}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                    >
                        <Edit className="w-4 h-4" /> Edit Report
                    </button>
                </div>
            </div>

            <div className="bg-white p-8 rounded-md border shadow-sm space-y-8">
                <div>
                    <h2 className="text-lg font-bold border-b pb-2 mb-4 text-gray-800">Completed Tasks</h2>
                    {report.completed_tasks.length === 0 ? (
                        <p className="text-gray-500 italic">None</p>
                    ) : (
                        <ul className="list-disc pl-5 space-y-2">
                            {report.completed_tasks.map((task, i) => (
                                <li key={i} className="text-gray-700">{task}</li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h2 className="text-lg font-bold border-b pb-2 mb-4 text-gray-800">Next Plan</h2>
                    {report.next_plan.length === 0 ? (
                        <p className="text-gray-500 italic">None</p>
                    ) : (
                        <ul className="list-disc pl-5 space-y-2">
                            {report.next_plan.map((plan, i) => (
                                <li key={i} className="text-gray-700">{plan}</li>
                            ))}
                        </ul>
                    )}
                </div>

                <div>
                    <h2 className="text-lg font-bold border-b pb-2 mb-4 text-gray-800">Blockers</h2>
                    {report.blockers.length === 0 ? (
                        <p className="text-gray-500 italic">None</p>
                    ) : (
                        <ul className="list-disc pl-5 space-y-2">
                            {report.blockers.map((blocker, i) => (
                                <li key={i} className="text-gray-700">{blocker}</li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}
