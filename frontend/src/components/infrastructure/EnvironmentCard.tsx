import React from 'react';
import { Environment } from '../../types/infrastructure';

export const EnvironmentCard: React.FC<{ environment: Environment }> = ({ environment }) => {
  return (
    <div className="bg-gray-800 p-4 rounded shadow">
      <h3 className="text-white text-lg">{environment.name}</h3>
      <p className="text-gray-400">{environment.type}</p>
    </div>
  );
};
