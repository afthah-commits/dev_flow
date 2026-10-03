import React, { useState, useEffect } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { organizationApi } from '../lib/organizationApi';
import { Organization } from '../types/organization';

export function OrganizationSettings() {
  const { currentOrganization, setCurrentOrganization, refreshOrganizations } = useOrganization();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [createName, setCreateName] = useState('');

  useEffect(() => {
    if (currentOrganization) {
      setName(currentOrganization.name);
      setDescription(currentOrganization.description || '');
    }
  }, [currentOrganization]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization) return;
    setIsSaving(true);
    try {
      const updated = await organizationApi.update(currentOrganization.id, { name, description });
      setCurrentOrganization(updated);
      await refreshOrganizations();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to update organization');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const org = await organizationApi.create({ name: createName });
      await refreshOrganizations();
      setCurrentOrganization(org);
      setIsCreating(false);
      setCreateName('');
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to create organization');
    } finally {
      setIsSaving(false);
    }
  };

  if (!currentOrganization && !isCreating) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">No Organizations</h2>
        <button 
          onClick={() => setIsCreating(true)}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white"
        >
          Create Organization
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {isCreating ? (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-bold mb-4">Create Organization</h2>
          <form onSubmit={handleCreate} className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name</label>
              <input
                type="text"
                required
                value={createName}
                onChange={e => setCreateName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white"
              />
            </div>
            <div className="flex space-x-3">
              <button 
                type="submit" 
                disabled={isSaving}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white"
              >
                Create
              </button>
              <button 
                type="button" 
                onClick={() => setIsCreating(false)}
                className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-white"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Organization Settings</h2>
            <button 
              onClick={() => setIsCreating(true)}
              className="bg-gray-800 hover:bg-gray-700 px-3 py-1 text-sm rounded text-white"
            >
              New Organization
            </button>
          </div>
          <form onSubmit={handleUpdate} className="space-y-4 max-w-md">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded p-2 text-white"
                rows={3}
              />
            </div>
            <button 
              type="submit" 
              disabled={isSaving}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white"
            >
              Save Changes
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
