import { GlobalSearch } from '../components/GlobalSearch';
import React from "react";
import { Outlet, Navigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useOrganization } from "../contexts/OrganizationContext";
import { NotificationCenter } from "../components/NotificationCenter";
import { TimerWidget } from "../components/TimerWidget";

import { useRealtimeConnection } from "../hooks/useRealtime";

export default function DashboardLayout() {
  const { user, isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const { currentOrganization, organizations, setCurrentOrganization, isLoading: isOrgLoading } = useOrganization();
  useRealtimeConnection(currentOrganization?.id);

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
          <Link to="/ai" className="hover:text-white transition-colors">AI Intelligence</Link>
          <Link to="/projects" className="hover:text-white transition-colors">Projects</Link>
          <div className="relative group">
            <span className="hover:text-white transition-colors cursor-pointer">Infrastructure</span>
            <div className="absolute hidden group-hover:block bg-gray-800 p-2 rounded shadow-lg z-10 w-40">
              <Link to="/infrastructure/environments" className="block text-sm py-1 hover:text-white">Environments</Link>
              <Link to="/infrastructure/deployments" className="block text-sm py-1 hover:text-white">Deployments</Link>
              <Link to="/infrastructure/services" className="block text-sm py-1 hover:text-white">Services</Link>
              <Link to="/infrastructure/incidents" className="block text-sm py-1 hover:text-white">Incidents</Link>
              <Link to="/infrastructure/analytics" className="block text-sm py-1 hover:text-white">Analytics</Link>
            </div>
          </div>
          <Link to="/organization" className="hover:text-white transition-colors">Organization</Link>
          <Link to="/time" className="hover:text-white transition-colors">Time</Link>
          <Link to="/analytics/productivity" className="hover:text-white transition-colors">Productivity</Link>
          <div className="relative group">
            <span className="hover:text-white transition-colors cursor-pointer">Daily Reports</span>
            <div className="absolute hidden group-hover:block bg-gray-800 p-2 rounded shadow-lg z-10 w-40">
              <Link to="/daily-reports" className="block text-sm py-1 hover:text-white">My Reports</Link>
              <Link to="/daily-reports/team" className="block text-sm py-1 hover:text-white">Team Reports</Link>
              <Link to="/daily-reports/weekly" className="block text-sm py-1 hover:text-white">Weekly Summary</Link>
              <Link to="/daily-reports/blockers" className="block text-sm py-1 hover:text-white">Blockers</Link>
            </div>
          </div>
          <Link to="/profile" className="hover:text-white transition-colors">Profile</Link>
          <div className="flex items-center space-x-3 ml-4 border-l border-gray-700 pl-4">
            <Link to="/notifications" className="text-sm text-gray-400 hover:text-white transition-colors hidden sm:inline">Notifications</Link>
            <Link to="/action-center" className="text-sm text-orange-400 hover:text-orange-300 transition-colors hidden sm:inline">⚡ Actions</Link>
            <NotificationCenter />
            <span className="text-sm ml-2">{user?.name}</span>
            <button onClick={logout} className="text-sm text-gray-400 hover:text-white">Logout</button>
          </div>
        </div>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
        <TimerWidget />
      </main>
    </div>
  );
}

// Note: Timer listener would go here or inside TimerWidget. Let us put it in TimerWidget!

