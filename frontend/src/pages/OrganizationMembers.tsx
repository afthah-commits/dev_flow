import React, { useState, useEffect } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { organizationApi } from '../lib/organizationApi';
import { OrganizationMember, OrganizationRole } from '../types/organization';

export function OrganizationMembers() {
  const { currentOrganization } = useOrganization();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (currentOrganization) {
      loadMembers();
    }
  }, [currentOrganization]);

  const loadMembers = async () => {
    if (!currentOrganization) return;
    setIsLoading(true);
    try {
      const data = await organizationApi.listMembers(currentOrganization.id);
      setMembers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoleChange = async (memberId: string, role: OrganizationRole) => {
    if (!currentOrganization) return;
    try {
      await organizationApi.updateMemberRole(currentOrganization.id, memberId, role);
      loadMembers();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleRemove = async (memberId: string) => {
    if (!currentOrganization) return;
    try {
      await organizationApi.removeMember(currentOrganization.id, memberId);
      loadMembers();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to remove member');
    }
  };

  if (!currentOrganization) return null;
  if (isLoading) return <div>Loading members...</div>;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4">Organization Members</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              <th className="py-3 px-4">User ID</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Joined At</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map(member => (
              <tr key={member.id} className="border-b border-gray-800/50">
                <td className="py-3 px-4">{member.user_id}</td>
                <td className="py-3 px-4">
                  <select 
                    value={member.role}
                    onChange={(e) => handleRoleChange(member.id, e.target.value as OrganizationRole)}
                    className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white"
                  >
                    <option value="OWNER">Owner</option>
                    <option value="ADMIN">Admin</option>
                    <option value="MEMBER">Member</option>
                  </select>
                </td>
                <td className="py-3 px-4 text-sm text-gray-400">
                  {new Date(member.joined_at).toLocaleDateString()}
                </td>
                <td className="py-3 px-4 text-right">
                  <button 
                    onClick={() => handleRemove(member.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
