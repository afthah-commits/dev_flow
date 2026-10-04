import React from 'react';

export const DeploymentStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  return <span className="px-2 py-1 bg-blue-900 text-blue-200 rounded text-xs">{status}</span>;
};
