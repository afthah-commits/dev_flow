import React from 'react';
import { Deployment } from '../../types/infrastructure';

export const DeploymentCard: React.FC<{ deployment: Deployment }> = ({ deployment }) => {
  return (
    <div className="bg-gray-800 p-4 rounded shadow">
      <h3 className="text-white text-lg">{deployment.version}</h3>
      <p className="text-gray-400">{deployment.status}</p>
    </div>
  );
};
