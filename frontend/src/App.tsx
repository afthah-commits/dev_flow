import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import Projects from "./pages/Projects";
import ProjectForm from "./pages/ProjectForm";
import ProjectDetails from "./pages/ProjectDetails";
import { GitHubSettings, GitHubCallback } from "./pages/GitHubIntegrations";
import { NotificationPreferences } from "./pages/NotificationPreferences";
import Timesheet from "./pages/Timesheet";
import ProductivityAnalytics from "./pages/ProductivityAnalytics";
import OrganizationLayout from "./pages/OrganizationLayout";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
          </Route>
          
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/new" element={<ProjectForm />} />
            <Route path="/projects/:projectId" element={<ProjectDetails />} />
            <Route path="/projects/:projectId/edit" element={<ProjectForm />} />
            <Route path="/settings/integrations" element={<GitHubSettings />} />
            <Route path="/settings/integrations/github/callback" element={<GitHubCallback />} />
            <Route path="/settings/notifications" element={<NotificationPreferences />} />
            <Route path="/organization" element={<OrganizationLayout />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
