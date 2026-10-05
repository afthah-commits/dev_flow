import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useOrganization } from '../contexts/OrganizationContext';
import { dailyReportApi } from '../lib/dailyReportApi';
import { Plus, Trash2, ArrowLeft } from 'lucide-react';

export default function DailyReportForm() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { currentOrganization } = useOrganization();
    
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [completedTasks, setCompletedTasks] = useState<string[]>(['']);
    const [nextPlan, setNextPlan] = useState<string[]>(['']);
    const [blockers, setBlockers] = useState<string[]>(['None']);
    
    const [loading, setLoading] = useState(id ? true : false);
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
            setError(err.message || 'Failed to save report');
        }
    };

    const ListInput = ({ title, items, setItems }: { title: string, items: string[], setItems: (i: string[]) => void }) => (
        <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">{title}</h3>
            {items.map((item, idx) => (
                <div key={idx} className="flex gap-2 mb-2">
                    <input
                        type="text"
                        className="flex-1 border rounded-md px-3 py-2 text-sm"
                        value={item}
                        onChange={(e) => {
                            const newItems = [...items];
                            newItems[idx] = e.target.value;
                            setItems(newItems);
                        }}
                        placeholder={`Enter ${title.toLowerCase()}`}
                    />
                    <button
                        onClick={() => setItems(items.filter((_, i) => i !== idx))}
                        className="p-2 text-gray-400 hover:text-red-600 rounded-md hover:bg-red-50"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            ))}
            <button
                onClick={() => setItems([...items, ''])}
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium mt-2"
            >
                <Plus className="w-4 h-4" /> Add Item
            </button>
        </div>
    );

    if (loading) return <div className="p-8">Loading...</div>;

    return (
        <div className="p-8 max-w-3xl mx-auto">
            <div className="mb-6 flex items-center gap-4">
                <button onClick={() => navigate('/daily-reports')} className="p-2 hover:bg-gray-100 rounded-md">
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <h1 className="text-2xl font-bold">{id ? 'Edit Daily Report' : 'New Daily Report'}</h1>
            </div>

            {error && <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-md">{error}</div>}

            <div className="bg-white p-6 rounded-md border shadow-sm">
                <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Date</label>
                    <input
                        type="date"
                        className="border rounded-md px-3 py-2"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                    />
                </div>

                <ListInput title="Completed Tasks" items={completedTasks} setItems={setCompletedTasks} />
                <ListInput title="Next Plan" items={nextPlan} setItems={setNextPlan} />
                <ListInput title="Blockers" items={blockers} setItems={setBlockers} />

                <div className="mt-8 flex justify-end gap-3 pt-6 border-t">
                    <button
                        onClick={() => navigate('/daily-reports')}
                        className="px-4 py-2 border rounded-md hover:bg-gray-50 text-sm font-medium"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                    >
                        Save Report
                    </button>
                </div>
            </div>
        </div>
    );
}
