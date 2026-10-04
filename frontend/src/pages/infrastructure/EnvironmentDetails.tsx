import React from 'react';
import { EnvironmentVariableManager } from '../../components/infrastructure/EnvironmentVariableManager';

export default function EnvironmentDetails() {
  return (
    <div className="p-6 text-white">
      <h1 className="text-2xl mb-4">Environment Details</h1>
      <EnvironmentVariableManager />
    </div>
  );
}
