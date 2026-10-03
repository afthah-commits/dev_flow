import React from "react";
import { Outlet, Navigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useOrganization } from "../contexts/OrganizationContext";
import { NotificationCenter } from "../components/NotificationCenter";

export default function DashboardLayout() {
  const { user, isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const { currentOrganization, organizations, setCurrentOrganization, isLoading: isOrgLoading } = useOrganization();

  if (isAuthLoading || isOrgLoading) {
    return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-200">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col text-gray-100">
      <nav className="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="text-xl font-bold text-white">DevFlow</div>
          <select 
            className="bg-gray-800 text-white text-sm rounded border border-gray-700 p-1"
            value={currentOrganization?.id || ""}
            onChange={(e) => {
              const org = organizations.find(o => o.id === e.target.value);
              if (org) setCurrentOrganization(org);
            }}
          >
            {organizations.map(org => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center space-x-6">
          <Link to="/" className="hover:text-white transition-colors">Dashboard</Link>
          <Link to="/projects" className="hover:text-white transition-colors">Projects</Link>
          <Link to="/organization" className="hover:text-white transition-colors">Organization</Link>
          <Link to="/profile" className="hover:text-white transition-colors">Profile</Link>
          <div className="flex items-center space-x-3 ml-4 border-l border-gray-700 pl-4">
            <NotificationCenter />
            <span className="text-sm ml-2">{user?.name}</span>
            <button onClick={logout} className="text-sm text-gray-400 hover:text-white">Logout</button>
          </div>
        </div>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
