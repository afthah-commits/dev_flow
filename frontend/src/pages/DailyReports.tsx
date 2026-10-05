import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { dailyReportApi } from '../lib/dailyReportApi';
import { DailyReport } from '../types/dailyReport';
import { useOrganization } from '../contexts/OrganizationContext';
import { Plus, FileText, Calendar } from 'lucide-react';

export default function DailyReports() {
    const navigate = useNavigate();
    const { currentOrganization } = useOrganization();
    const [reports, setReports] = useState<DailyReport[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!currentOrganization) return;
        const fetchReports = async () => {
            try {
                const data = await dailyReportApi.list(currentOrganization.id);
                setReports(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchReports();
    }, [currentOrganization]);

    if (loading) {
        return <div className="p-8">Loading daily reports...</div>;
    }

    return (
        <div className="p-8">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold">Daily Reports</h1>
                    <p className="text-gray-500 text-sm mt-1">Track your daily progress and plans.</p>
                </div>
                <button
                    onClick={() => navigate('/daily-reports/new')}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                    <Plus className="w-4 h-4" />
                    New Report
                </button>
            </div>

            <div className="bg-white rounded-md border">
                {reports.length === 0 ? (
                    <div className="p-8 text-center text-gray-500">
                        <FileText className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                        <p>No daily reports found.</p>
                        <button
                            onClick={() => navigate('/daily-reports/new')}
                            className="text-blue-600 hover:underline mt-2 inline-block"
                        >
                            Create your first report
                        </button>
                    </div>
                ) : (
                    <div className="divide-y">
                        {reports.map((report) => (
                            <div 
                                key={report.id} 
                                onClick={() => navigate(`/daily-reports/${report.id}`)}
                                className="p-4 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-blue-50 text-blue-600 rounded-md">
                                        <Calendar className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <div className="font-medium text-gray-900">
                                            {report.report_date}
                                        </div>
                                        <div className="text-sm text-gray-500 flex gap-4">
                                            <span>{report.completed_tasks.length} completed</span>
                                            <span>{report.next_plan.length} planned</span>
                                            <span>{report.blockers.length} blockers</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
