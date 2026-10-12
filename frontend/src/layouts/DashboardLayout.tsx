import React, { useState } from "react";
import { Outlet, Navigate, Link, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useOrganization } from "../contexts/OrganizationContext";
import { NotificationCenter } from "../components/NotificationCenter";
import { TimerWidget } from "../components/TimerWidget";
import { GlobalSearch } from "../components/GlobalSearch";
import { useRealtimeConnection } from "../hooks/useRealtime";

export default function DashboardLayout() {
  const { user, isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
  const { currentOrganization, organizations, setCurrentOrganization, isLoading: isOrgLoading } = useOrganization();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  useRealtimeConnection(currentOrganization?.id);

  if (isAuthLoading || isOrgLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center text-gray-300 space-y-3">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium">Loading DevFlow...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!currentOrganization) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center text-gray-300 space-y-3">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium">Setting up your workspace...</p>
      </div>
    );
  }

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const navLinkClass = (path: string) => `text-sm font-medium transition-colors px-2.5 py-1.5 rounded-md ${
    isActive(path)
      ? 'text-white bg-gray-800/80 font-semibold'
      : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800/40'
  }`;

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col text-gray-100 selection:bg-indigo-500/30">
      {/* Top Main Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-gray-800 bg-gray-900/95 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-4">
            {/* Brand & Org Switcher */}
            <div className="flex items-center gap-3 sm:gap-4 shrink-0">
              <Link to="/" className="flex items-center gap-2 group">
                <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-lg shadow-sm group-hover:bg-indigo-500 transition-colors">
                  D
                </div>
                <span className="text-lg font-bold tracking-tight text-white hidden sm:inline">
                  DevFlow
                </span>
              </Link>

              <div className="relative">
                <select 
                  aria-label="Current Workspace"
                  className="bg-gray-800/90 text-gray-200 text-xs sm:text-sm rounded-lg border border-gray-700/80 px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors font-medium cursor-pointer max-w-[150px] sm:max-w-[200px] truncate"
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
            </div>

            {/* Desktop Navigation Links */}
            <nav className="hidden xl:flex items-center space-x-1 shrink-0">
              <Link to="/" className={navLinkClass("/")}>Dashboard</Link>
              <Link to="/ai" className={navLinkClass("/ai")}>AI Intelligence</Link>
              <Link to="/projects" className={navLinkClass("/projects")}>Projects</Link>
              <Link to="/templates" className={navLinkClass("/templates")}>Templates</Link>
              
              {/* Infrastructure Dropdown */}
              <div className="relative group">
                <button 
                  type="button"
                  className={`flex items-center gap-1 ${navLinkClass("/infrastructure")}`}
                >
                  <span>Infra</span>
                  <svg className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div className="absolute left-0 mt-1 hidden group-hover:block bg-gray-900 border border-gray-800 p-1.5 rounded-lg shadow-2xl z-50 w-44 backdrop-blur-xl">
                  <Link to="/infrastructure/environments" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Environments</Link>
                  <Link to="/infrastructure/deployments" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Deployments</Link>
                  <Link to="/infrastructure/services" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Services</Link>
                  <Link to="/infrastructure/incidents" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Incidents</Link>
                  <Link to="/infrastructure/analytics" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Analytics</Link>
                </div>
              </div>

              <Link to="/organization" className={navLinkClass("/organization")}>Org</Link>
              <Link to="/time" className={navLinkClass("/time")}>Time</Link>
              <Link to="/analytics/productivity" className={navLinkClass("/analytics")}>Analytics</Link>

              {/* Reports Dropdown */}
              <div className="relative group">
                <button 
                  type="button"
                  className={`flex items-center gap-1 ${navLinkClass("/daily-reports")}`}
                >
                  <span>Reports</span>
                  <svg className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                <div className="absolute left-0 mt-1 hidden group-hover:block bg-gray-900 border border-gray-800 p-1.5 rounded-lg shadow-2xl z-50 w-44 backdrop-blur-xl">
                  <Link to="/daily-reports" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">My Reports</Link>
                  <Link to="/daily-reports/team" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Team Reports</Link>
                  <Link to="/daily-reports/weekly" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Weekly Summary</Link>
                  <Link to="/daily-reports/blockers" className="block text-xs text-gray-300 hover:text-white hover:bg-gray-800/80 px-3 py-2 rounded-md transition-colors">Blockers</Link>
                </div>
              </div>
            </nav>

            {/* Right Action Icons & User */}
            <div className="flex items-center gap-3 shrink-0">
              <Link 
                to="/action-center" 
                className="text-xs font-semibold px-2.5 py-1.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors hidden sm:flex items-center gap-1"
                title="Action Center"
              >
                <span>⚡</span>
                <span className="hidden md:inline">Actions</span>
              </Link>

              <Link 
                to="/notifications" 
                className="text-xs text-gray-400 hover:text-gray-100 transition-colors hidden sm:inline px-1.5 py-1"
              >
                Inbox
              </Link>

              <div className="shrink-0">
                <NotificationCenter />
              </div>

              {/* User Menu / Logout */}
              <div className="flex items-center gap-2 pl-2 border-l border-gray-800">
                <Link to="/profile" className="text-xs font-medium text-gray-300 hover:text-white truncate max-w-[100px] hidden sm:inline" title={user?.name}>
                  {user?.name}
                </Link>
                <button 
                  onClick={logout} 
                  className="text-xs text-gray-400 hover:text-red-400 px-2 py-1 rounded transition-colors font-medium"
                >
                  Logout
                </button>
              </div>

              {/* Mobile Hamburger Button */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="xl:hidden p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                aria-label="Toggle navigation menu"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="xl:hidden border-t border-gray-800 bg-gray-900/95 px-4 pt-3 pb-5 space-y-1 backdrop-blur-xl">
            <Link to="/" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/")}>Dashboard</Link>
            <Link to="/ai" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/ai")}>AI Intelligence</Link>
            <Link to="/projects" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/projects")}>Projects</Link>
            <Link to="/templates" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/templates")}>Templates</Link>
            <Link to="/time" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/time")}>Time Tracking</Link>
            <Link to="/analytics/productivity" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/analytics/productivity")}>Productivity Analytics</Link>
            <Link to="/daily-reports" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/daily-reports")}>Daily Reports</Link>
            <Link to="/infrastructure/environments" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/infrastructure/environments")}>Infrastructure</Link>
            <Link to="/organization" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/organization")}>Organization Settings</Link>
            <Link to="/profile" onClick={() => setMobileMenuOpen(false)} className={navLinkClass("/profile")}>Profile</Link>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
        <TimerWidget />
      </main>

      {/* Global Quick Search modal */}
      <GlobalSearch />
    </div>
  );
}
