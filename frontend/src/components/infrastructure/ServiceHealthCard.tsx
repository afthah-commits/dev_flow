import React from 'react';
import { ServiceHealth } from '../../types/infrastructure';

export const ServiceHealthCard: React.FC<{ health: ServiceHealth }> = ({ health }) => {
  return (
    <div className="bg-gray-800 p-4 rounded shadow">
      <h3 className="text-white">{health.serviceName}</h3>
      <p className="text-gray-400">{health.status}</p>
    </div>
  );
};
