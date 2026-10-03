import React, { useState, useEffect } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { api } from '../lib/axios';
import { Team, TeamMember } from '../types/organization';

export function OrganizationTeams() {
  const { currentOrganization } = useOrganization();
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamSlug, setNewTeamSlug] = useState('');

  useEffect(() => {
    if (currentOrganization) {
      loadTeams();
    }
  }, [currentOrganization]);

  const loadTeams = async () => {
    if (!currentOrganization) return;
    setIsLoading(true);
    try {
      const res = await api.get<Team[]>(`/organizations/${currentOrganization.id}/teams`);
      setTeams(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization) return;
    try {
      await api.post(`/organizations/${currentOrganization.id}/teams`, {
        name: newTeamName,
        slug: newTeamSlug
      });
      setIsCreating(false);
      setNewTeamName('');
      setNewTeamSlug('');
      loadTeams();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to create team');
    }
  };

  const handleDelete = async (teamId: string) => {
    if (!confirm('Are you sure you want to delete this team?')) return;
    try {
      await api.delete(`/teams/${teamId}`);
      loadTeams();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to delete team');
    }
  };

  if (!currentOrganization) return null;
  if (isLoading) return <div>Loading teams...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Teams</h2>
          <button 
            onClick={() => setIsCreating(!isCreating)}
            className="bg-blue-600 hover:bg-blue-700 px-3 py-1 text-sm rounded text-white"
          >
            {isCreating ? 'Cancel' : 'New Team'}
          </button>
        </div>

        {isCreating && (
          <form onSubmit={handleCreate} className="mb-6 space-y-4 max-w-md bg-gray-800 p-4 rounded">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name</label>
              <input
                type="text"
                required
                value={newTeamName}
                onChange={e => setNewTeamName(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Slug</label>
              <input
                type="text"
                required
                value={newTeamSlug}
                onChange={e => setNewTeamSlug(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
              />
            </div>
            <button 
              type="submit" 
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-white"
            >
              Create
            </button>
          </form>
        )}

        <div className="space-y-3">
          {teams.map(team => (
            <div key={team.id} className="border border-gray-800 rounded p-4 flex justify-between items-center bg-gray-800/50">
              <div>
                <h3 className="font-semibold text-lg">{team.name}</h3>
                <p className="text-gray-400 text-sm">@{team.slug}</p>
              </div>
              <button 
                onClick={() => handleDelete(team.id)}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                Delete
              </button>
            </div>
          ))}
          {teams.length === 0 && !isCreating && (
            <div className="text-gray-500 text-center py-4">No teams created yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
