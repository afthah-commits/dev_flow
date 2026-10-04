import CollaborationAnalytics from './pages/CollaborationAnalytics';
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import Automations from './pages/Automations';
import AutomationDetails from './pages/AutomationDetails';
import Integrations from './pages/settings/Integrations';
import Webhooks from './pages/settings/Webhooks';
import ApiKeys from './pages/settings/ApiKeys';
import Security from './pages/settings/Security';
import Usage from './pages/settings/Usage';
import AdminSystem from './pages/AdminSystem';

import Environments from './pages/infrastructure/Environments';
import EnvironmentDetails from './pages/infrastructure/EnvironmentDetails';
import Deployments from './pages/infrastructure/Deployments';
import DeploymentDetails from './pages/infrastructure/DeploymentDetails';
import Services from './pages/infrastructure/Services';
import Incidents from './pages/infrastructure/Incidents';
import InfrastructureAnalytics from './pages/infrastructure/InfrastructureAnalytics';

import Dashboards from './pages/Dashboards';
import Reports from './pages/Reports';
import AdminCompliance from './pages/AdminCompliance';
import PrivacySettings from './pages/settings/PrivacySettings';
import OrganizationSecurity from './pages/settings/OrganizationSecurity';
import Sessions from './pages/settings/Sessions';
import DeveloperSettings from './pages/settings/DeveloperSettings';
import SecurityCenter from './pages/settings/SecurityCenter';
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
import ReleaseDetails from "./pages/ReleaseDetails";
import DeliveryAnalytics from "./pages/DeliveryAnalytics";

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
            <Route path="/time" element={<Timesheet />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/new" element={<ProjectForm />} />
            <Route path="/projects/:projectId" element={<ProjectDetails />} />
              <Route path="/dashboards" element={<Dashboards />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/admin/compliance" element={<AdminCompliance />} />
              <Route path="/settings/privacy" element={<PrivacySettings />} />
              <Route path="/settings/organization/security" element={<OrganizationSecurity />} />
              <Route path="/settings/sessions" element={<Sessions />} />
              <Route path="/settings/developer" element={<DeveloperSettings />} />
              <Route path="/settings/security-center" element={<SecurityCenter />} />
            <Route path="/projects/:projectId/edit" element={<ProjectForm />} />
            <Route path="/projects/:projectId/releases/:releaseId" element={<ReleaseDetails />} />
            <Route path="/settings/integrations" element={<GitHubSettings />} />
            <Route path="/settings/integrations/github/callback" element={<GitHubCallback />} />
            <Route path="/settings/notifications" element={<NotificationPreferences />} />
            <Route path="/organization" element={<OrganizationLayout />} />
            <Route path="/analytics/productivity" element={<ProductivityAnalytics />} />
            <Route path="/analytics/delivery" element={<DeliveryAnalytics />} />
            <Route path="/analytics/collaboration" element={<CollaborationAnalytics />} />
              <Route path="/automations" element={<Automations />} />
              <Route path="/automations/:id" element={<AutomationDetails />} />
              <Route path="/settings/integrations" element={<Integrations />} />
              <Route path="/settings/webhooks" element={<Webhooks />} />
              <Route path="/settings/api-keys" element={<ApiKeys />} />
              <Route path="/settings/security" element={<Security />} />
              <Route path="/settings/usage" element={<Usage />} />
              <Route path="/admin/system" element={<AdminSystem />} />

              <Route path="/infrastructure/environments" element={<Environments />} />
              <Route path="/infrastructure/environments/:id" element={<EnvironmentDetails />} />
              <Route path="/infrastructure/deployments" element={<Deployments />} />
              <Route path="/infrastructure/deployments/:id" element={<DeploymentDetails />} />
              <Route path="/infrastructure/services" element={<Services />} />
              <Route path="/infrastructure/incidents" element={<Incidents />} />
              <Route path="/infrastructure/analytics" element={<InfrastructureAnalytics />} />


          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}



