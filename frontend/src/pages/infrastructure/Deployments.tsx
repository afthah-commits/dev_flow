import React, { useEffect, useState } from 'react';
import { DeploymentCard } from '../../components/infrastructure/DeploymentCard';
import { Deployment } from '../../types/infrastructure';
import { deploymentApi } from '../../lib/deploymentApi';

export default function Deployments() {
  const [deps, setDeps] = useState<Deployment[]>([]);
  useEffect(() => {
    deploymentApi.list('1').then(setDeps).catch(() => {});
  }, []);
  return (
    <div className="p-6">
      <h1 className="text-2xl text-white mb-4">Deployments</h1>
      <div className="space-y-4">
        {deps.map(dep => <DeploymentCard key={dep.id} deployment={dep} />)}
      </div>
    </div>
  );
}
