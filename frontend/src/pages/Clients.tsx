import React, { useState } from 'react';
import { Users, Building, Plus, Search, Mail, Phone, Settings, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Clients() {
  const navigate = useNavigate();
  const [clients] = useState([
    { id: '1', name: 'Acme Corp', company_name: 'Acme Corporation', email: 'contact@acme.com', status: 'ACTIVE' }
  ]);
  const [search, setSearch] = useState('');

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Building className="w-6 h-6 text-indigo-400" />
            Client Management
          </h1>
          <p className="text-gray-400 mt-1">Manage external clients, their projects, and portal access.</p>
        </div>
        <button className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-medium">
          <Plus className="w-4 h-4" />
          Add Client
        </button>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 flex items-center mb-6">
        <Search className="w-5 h-5 text-gray-500 mr-3" />
        <input 
          type="text"
          placeholder="Search clients by name or company..."
          className="bg-transparent border-none text-white outline-none flex-1"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clients.map(client => (
          <div key={client.id} className="bg-gray-800 border border-gray-700 rounded-lg p-6 flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-lg text-white">{client.name}</h3>
                <div className="text-sm text-gray-400">{client.company_name}</div>
              </div>
              <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded font-medium">
                {client.status}
              </span>
            </div>
            
            <div className="space-y-2 mb-6 flex-1">
              <div className="flex items-center text-sm text-gray-300 gap-3">
                <Mail className="w-4 h-4 text-gray-500" /> {client.email}
              </div>
              <div className="flex items-center text-sm text-gray-300 gap-3">
                <Phone className="w-4 h-4 text-gray-500" /> N/A
              </div>
              <div className="flex items-center text-sm text-gray-300 gap-3 mt-3">
                <AlertCircle className="w-4 h-4 text-orange-400" /> 0 Open Requests
              </div>
            </div>

            <div className="flex justify-end gap-2 border-t border-gray-700 pt-4">
              <button className="p-2 hover:bg-gray-700 text-gray-400 hover:text-white rounded">
                <Settings className="w-4 h-4" />
              </button>
              <button className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-sm font-medium rounded text-white">
                View Portal
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
