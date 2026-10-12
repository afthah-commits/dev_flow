import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { Plus, Trash2, ArrowLeft, Calendar, Save } from 'lucide-react';

export default function DailyReportForm() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { currentOrganization } = useOrganization();
    
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [completedTasks, setCompletedTasks] = useState<string[]>(['']);
    const [nextPlan, setNextPlan] = useState<string[]>(['']);
    const [blockers, setBlockers] = useState<string[]>(['None']);
    
    const [loading, setLoading] = useState(id ? true : false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id || !currentOrganization) return;
        const fetchReport = async () => {
            try {
                const data = await dailyReportApi.get(id, currentOrganization.id);
                setDate(data.report_date);
                setCompletedTasks(data.completed_tasks.length > 0 ? data.completed_tasks : ['']);
                setNextPlan(data.next_plan.length > 0 ? data.next_plan : ['']);
                setBlockers(data.blockers.length > 0 ? data.blockers : ['']);
            } catch (err) {
                setError('Failed to load report');
            } finally {
                setLoading(false);
            }
        };
        fetchReport();
    }, [id, currentOrganization]);

    const handleSave = async () => {
        if (!currentOrganization) return;
        setError(null);
        setSaving(true);
        try {
            const data = {
                report_date: date,
                completed_tasks: completedTasks.filter(t => t.trim()),
                next_plan: nextPlan.filter(t => t.trim()),
                blockers: blockers.filter(t => t.trim())
            };
            
            if (id) {
                await dailyReportApi.update(id, data, currentOrganization.id);
                navigate(`/daily-reports/${id}`);
            } else {
                const created = await dailyReportApi.create(data, currentOrganization.id);
                navigate(`/daily-reports/${created.id}`);
            }
        } catch (err: any) {
            setError(err?.response?.data?.detail || err.message || 'Failed to save daily report');
        } finally {
            setSaving(false);
        }
    };

    const ListInput = ({ title, items, setItems, placeholder }: { title: string, items: string[], setItems: (i: string[]) => void, placeholder: string }) => (
        <div className="space-y-2">
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider">{title}</label>
            {items.map((item, idx) => (
                <div key={idx} className="flex gap-2">
                    <input
                        type="text"
                        className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                        value={item}
                        onChange={(e) => {
                            const newItems = [...items];
                            newItems[idx] = e.target.value;
                            setItems(newItems);
                        }}
                        placeholder={placeholder}
                    />
                    <button
                        type="button"
                        onClick={() => setItems(items.length > 1 ? items.filter((_, i) => i !== idx) : [''])}
                        className="p-2 text-gray-400 hover:text-red-400 rounded-lg hover:bg-gray-800 transition-colors"
                        title="Remove item"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            ))}
            <button
                type="button"
                onClick={() => setItems([...items, ''])}
                className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 font-medium py-1 transition-colors"
            >
                <Plus className="w-3.5 h-3.5" /> Add another
            </button>
        </div>
    );

    if (loading) {
        return (
            <div className="max-w-3xl mx-auto p-12 text-center text-gray-400 space-y-3">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-sm">Loading report editor...</p>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex items-center gap-3 pb-2 border-b border-gray-800">
                <button
                    onClick={() => navigate('/daily-reports')}
                    className="p-2 hover:bg-gray-800 text-gray-400 hover:text-white rounded-lg transition-colors border border-gray-800"
                    title="Cancel"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Calendar className="w-6 h-6 text-blue-400" />
                        {id ? 'Edit Daily Report' : 'New Daily Report'}
                    </h1>
                    <p className="text-xs text-gray-400">Record your daily standup updates and commitments.</p>
                </div>
            </div>

            {error && (
                <div className="p-4 bg-red-900/40 border border-red-800/60 text-red-200 text-sm rounded-xl">
                    {error}
                </div>
            )}

            <div className="bg-gray-900 p-6 sm:p-8 rounded-xl border border-gray-800 shadow-sm space-y-6">
                <div>
                    <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Report Date</label>
                    <input
                        type="date"
                        className="bg-gray-950 border border-gray-800 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 transition-colors"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                    />
                </div>

                <ListInput
                    title="Completed Tasks"
                    items={completedTasks}
                    setItems={setCompletedTasks}
                    placeholder="e.g. Implemented OAuth callback, resolved PR reviews"
                />

                <ListInput
                    title="Next Plan"
                    items={nextPlan}
                    setItems={setNextPlan}
                    placeholder="e.g. Finish database migration, add integration tests"
                />

                <ListInput
                    title="Blockers & Dependencies"
                    items={blockers}
                    setItems={setBlockers}
                    placeholder="e.g. Waiting on API credentials, or None"
                />

                <div className="pt-6 border-t border-gray-800 flex items-center justify-end gap-3">
                    <button
                        type="button"
                        onClick={() => navigate('/daily-reports')}
                        className="px-4 py-2 border border-gray-800 rounded-lg hover:bg-gray-800 text-sm font-medium text-gray-300 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
                    >
                        <Save className="w-4 h-4" />
                        {saving ? 'Saving...' : 'Save Report'}
                    </button>
                </div>
            </div>
        </div>
    );
}
