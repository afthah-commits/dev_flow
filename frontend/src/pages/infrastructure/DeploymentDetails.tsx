import React from 'react';
import { DeploymentTimeline } from '../../components/infrastructure/DeploymentTimeline';

export default function DeploymentDetails() {
  return (
    <div className="p-6 text-white">
      <h1 className="text-2xl mb-4">Deployment Details</h1>
      <DeploymentTimeline />
    </div>
  );
}
