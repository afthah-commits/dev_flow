import React, { useState, useEffect } from "react";
import { roadmapApi } from "../lib/backlogApi";
import { Project } from "../types/project";
import { Button } from "./ui/Button";
import { MilestoneForm } from "./MilestoneForm";

export function Roadmap({ project }: { project: Project }) {
  const [data, setData] = useState<{ milestones: any[], sprints: any[] }>({ milestones: [], sprints: [] });
  const [loading, setLoading] = useState(true);
  const [showMilestoneForm, setShowMilestoneForm] = useState(false);
  const [editingMilestone, setEditingMilestone] = useState<any>(null);

  useEffect(() => {
    loadRoadmap();
  }, [project.id]);

  const loadRoadmap = async () => {
    setLoading(true);
    try {
      const res = await roadmapApi.get(project.id);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-auto h-full p-1 text-gray-200 space-y-6">
      <div className="flex justify-between items-center shrink-0">
        <h2 className="text-xl font-bold">Project Roadmap</h2>
        <Button onClick={() => { setEditingMilestone(null); setShowMilestoneForm(true); }}>Add Milestone</Button>
      </div>

      {loading ? (
        <div className="text-gray-500">Loading roadmap...</div>
      ) : (
        <div className="space-y-8">
          <section>
            <h3 className="text-lg font-semibold mb-4 border-b border-gray-800 pb-2">Milestones</h3>
            {data.milestones.length === 0 ? (
              <p className="text-sm text-gray-500">No milestones planned.</p>
            ) : (
              <div className="space-y-4 relative border-l-2 border-gray-800 ml-3 pl-6">
                {data.milestones.map(m => (
                  <div key={m.id} className="relative bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div className="absolute w-3 h-3 bg-blue-500 rounded-full -left-[31px] top-5 border-4 border-gray-950"></div>
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white">{m.name}</h4>
                        {m.description && <p className="text-sm text-gray-400 mt-1">{m.description}</p>}
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full border ${m.status === 'ACTIVE' ? 'bg-blue-900/50 text-blue-300 border-blue-800' : 'bg-gray-800 text-gray-300 border-gray-700'}`}>
                        {m.status}
                      </span>
                    </div>
                    <div className="mt-4 flex gap-4 text-xs text-gray-500">
                      <span>Start: {m.start_date ? new Date(m.start_date).toLocaleDateString() : 'TBD'}</span>
                      <span>Due: {m.due_date ? new Date(m.due_date).toLocaleDateString() : 'TBD'}</span>
                      <button onClick={() => { setEditingMilestone(m); setShowMilestoneForm(true); }} className="text-blue-400 hover:underline ml-auto">Edit</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section>
            <h3 className="text-lg font-semibold mb-4 border-b border-gray-800 pb-2">Sprints Timeline</h3>
            {data.sprints.length === 0 ? (
              <p className="text-sm text-gray-500">No sprints planned.</p>
            ) : (
              <div className="space-y-4">
                {data.sprints.map(s => (
                  <div key={s.id} className="bg-gray-900/50 border border-gray-800 rounded p-3 flex justify-between items-center">
                    <div>
                      <span className="font-bold mr-3">{s.name}</span>
                      <span className="text-xs text-gray-500 font-mono">{s.key}</span>
                    </div>
                    <div className="text-sm text-gray-400">
                      {s.start_date ? new Date(s.start_date).toLocaleDateString() : '?'} &rarr; {s.end_date ? new Date(s.end_date).toLocaleDateString() : '?'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {showMilestoneForm && (
        <MilestoneForm 
          projectId={project.id}
          initialData={editingMilestone}
          onClose={() => { setShowMilestoneForm(false); setEditingMilestone(null); }}
          onSuccess={() => { setShowMilestoneForm(false); loadRoadmap(); }}
        />
      )}
    </div>
  );
}
