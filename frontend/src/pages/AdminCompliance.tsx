import React, { useEffect, useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { governanceApi } from '../lib/governanceApi';

export default function AdminCompliance() {
  const { currentOrganization } = useOrganization();
  const [overview, setOverview] = useState<any>(null);

  useEffect(() => {
    if (currentOrganization) {
      governanceApi.getComplianceOverview(currentOrganization.id).then(setOverview).catch(console.error);
    }
  }, [currentOrganization]);

  if (!overview) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Compliance & Governance Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 truncate">Organization Security Score</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{overview.security_score}/100</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 truncate">Total Members</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{overview.total_members}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 truncate">MFA Adoption</h3>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{overview.mfa_adoption}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 truncate">Recent Failed Logins</h3>
          <p className="mt-2 text-3xl font-semibold text-red-600">{overview.recent_failed_logins}</p>
        </div>
      </div>
    </div>
  );
}
