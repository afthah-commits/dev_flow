import React, { useEffect, useState } from 'react';
import { DeploymentIncident } from '../../types/infrastructure';
import { incidentApi } from '../../lib/incidentApi';

export default function Incidents() {
  const [incidents, setIncidents] = useState<DeploymentIncident[]>([]);
  useEffect(() => {
    incidentApi.getAll().then(setIncidents).catch(() => {});
  }, []);
  return (
    <div className="p-6">
      <h1 className="text-2xl text-white mb-4">Incidents</h1>
      <ul className="text-gray-300">
        {incidents.map(inc => <li key={inc.id}>{inc.title} - {inc.status}</li>)}
      </ul>
    </div>
  );
}
