import React, { useEffect, useState } from 'react';
import { useOrganization } from '../../contexts/OrganizationContext';
import { governanceApi } from '../../lib/governanceApi';
import { OrganizationSecurityPolicy } from '../../types/governance';

export default function OrganizationSecurity() {
  const { currentOrganization } = useOrganization();
  const [policy, setPolicy] = useState<OrganizationSecurityPolicy | null>(null);

  useEffect(() => {
    if (currentOrganization) {
      governanceApi.getSecurityPolicy(currentOrganization.id).then(setPolicy).catch(console.error);
    }
  }, [currentOrganization]);

  const toggleMfa = async () => {
    if (!currentOrganization || !policy) return;
    try {
      const updated = await governanceApi.updateSecurityPolicy(currentOrganization.id, { require_mfa: !policy.require_mfa });
      setPolicy(updated);
    } catch (e) {
      console.error(e);
    }
  };

  if (!policy) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Organization Security Policies</h1>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Access Controls</h3>
        </div>
        <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
          <dl className="sm:divide-y sm:divide-gray-200">
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Require MFA</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2 flex justify-between">
                <span>{policy.require_mfa ? 'Enabled' : 'Disabled'}</span>
                <button onClick={toggleMfa} className="text-indigo-600 hover:text-indigo-900 font-medium">Toggle</button>
              </dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Session Timeout (Minutes)</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {policy.session_timeout_minutes}
              </dd>
            </div>
            <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
              <dt className="text-sm font-medium text-gray-500">Max Active Sessions</dt>
              <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                {policy.max_active_sessions}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
