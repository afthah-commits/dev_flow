import React from 'react';
import { useParams } from 'react-router-dom';

export const WorkflowBuilder: React.FC = () => {
  const { id } = useParams();
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Workflow Builder</h1>
      <div className="bg-white shadow rounded-lg border">
        <div className="px-4 py-5 sm:px-6 border-b">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Workflow Settings {id}</h3>
        </div>
        <div className="p-6">
          <div className="flex space-x-4">
            <div className="w-1/3 border p-4 rounded bg-gray-50">
              <h3 className="font-semibold mb-2">States</h3>
              <ul className="list-disc pl-5">
                <li>To Do</li>
                <li>In Progress</li>
                <li>Done</li>
              </ul>
            </div>
            <div className="w-2/3 border p-4 rounded bg-white">
              <h3 className="font-semibold mb-2">Canvas</h3>
              <div className="p-10 text-center text-gray-400 border-2 border-dashed">
                Visual State Machine Editor (Coming Soon)
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowBuilder;
