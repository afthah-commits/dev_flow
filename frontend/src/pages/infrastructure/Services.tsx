import React, { useEffect, useState } from 'react';
import { ServiceHealthCard } from '../../components/infrastructure/ServiceHealthCard';
import { ServiceHealth } from '../../types/infrastructure';
import { infrastructureApi } from '../../lib/infrastructureApi';

export default function Services() {
  const [health, setHealth] = useState<ServiceHealth[]>([]);
  useEffect(() => {
    infrastructureApi.getServiceHealth('1').then(setHealth).catch(() => {});
  }, []);
  return (
    <div className="p-6">
      <h1 className="text-2xl text-white mb-4">Service Health</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {health.map(h => <ServiceHealthCard key={h.id} health={h} />)}
      </div>
    </div>
  );
}
