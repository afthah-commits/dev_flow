import React from 'react';

export const Workflows: React.FC = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Workflows</h1>
      <div className="bg-white shadow rounded-lg border">
        <div className="px-4 py-5 sm:px-6 border-b">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Business Processes</h3>
        </div>
        <div className="p-6">
          <p className="text-gray-500">Manage organizational workflows here.</p>
        </div>
      </div>
    </div>
  );
};

export default Workflows;
