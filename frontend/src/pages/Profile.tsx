import React from "react";
import { useAuth } from "../hooks/useAuth";

export default function Profile() {
  const { user } = useAuth();
  
  return (
    <div className="max-w-3xl mx-auto py-6">
      <h1 className="text-3xl font-bold text-white mb-6">Profile</h1>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">Name</label>
            <div className="text-lg text-gray-100">{user?.name}</div>
          </div>
          <div>
            <label className="text-sm text-gray-400">Email</label>
            <div className="text-lg text-gray-100">{user?.email}</div>
          </div>
          <div>
            <label className="text-sm text-gray-400">Member since</label>
            <div className="text-lg text-gray-100">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
