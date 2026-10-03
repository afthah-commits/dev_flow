import React, { useState } from 'react';
import { OrganizationSettings } from './OrganizationSettings';
import { OrganizationMembers } from './OrganizationMembers';
import { OrganizationTeams } from './OrganizationTeams';
import { AuditLogs } from './AuditLogs';

export default function OrganizationLayout() {
  const [activeTab, setActiveTab] = useState<'settings' | 'members' | 'teams' | 'audit'>('settings');

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Organization</h1>
      
      <div className="flex border-b border-gray-800">
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'settings' 
              ? 'border-blue-500 text-white' 
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'members'
              ? 'border-blue-500 text-white' 
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
          onClick={() => setActiveTab('members')}
        >
          Members
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'teams' 
              ? 'border-blue-500 text-white' 
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
          onClick={() => setActiveTab('teams')}
        >
          Teams
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'audit' 
              ? 'border-blue-500 text-white' 
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
          onClick={() => setActiveTab('audit')}
        >
          Audit Logs
        </button>
      </div>

      <div className="pt-4">
        {activeTab === 'settings' && <OrganizationSettings />}
        {activeTab === 'members' && <OrganizationMembers />}
        {activeTab === 'teams' && <OrganizationTeams />}
        {activeTab === 'audit' && <AuditLogs />}
      </div>
    </div>
  );
}
