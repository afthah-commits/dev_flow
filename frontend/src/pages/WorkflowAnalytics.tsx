import React from 'react';

export const WorkflowAnalytics: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Workflow Analytics</h1>
      <div className="bg-white shadow rounded-lg border">
        <div className="px-4 py-5 sm:px-6 border-b">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Performance Metrics</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded border">
              <div className="text-sm text-gray-500">Active Workflows</div>
              <div className="text-2xl font-bold">12</div>
            </div>
            <div className="p-4 bg-gray-50 rounded border">
              <div className="text-sm text-gray-500">Total Executions</div>
              <div className="text-2xl font-bold">1,204</div>
            </div>
            <div className="p-4 bg-gray-50 rounded border">
              <div className="text-sm text-gray-500">Avg Completion Time</div>
              <div className="text-2xl font-bold">4.2 Days</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowAnalytics;
