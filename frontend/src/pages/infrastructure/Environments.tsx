import React, { useEffect, useState } from 'react';
import { EnvironmentCard } from '../../components/infrastructure/EnvironmentCard';
import { Environment } from '../../types/infrastructure';
import { environmentApi } from '../../lib/environmentApi';

export default function Environments() {
  const [envs, setEnvs] = useState<Environment[]>([]);
  useEffect(() => {
    environmentApi.getEnvironments('1').then(setEnvs).catch(() => {});
  }, []);
  return (
    <div className="p-6">
      <h1 className="text-2xl text-white mb-4">Environments</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {envs.map(env => <EnvironmentCard key={env.id} environment={env} />)}
      </div>
    </div>
  );
}
