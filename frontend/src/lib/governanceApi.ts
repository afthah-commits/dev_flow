import { api } from './axios';
import { OrganizationSecurityPolicy, OrganizationDomain, DataExportJob } from '../types/governance';

export const governanceApi = {
  getSecurityPolicy: async (orgId: string) => {
    const res = await api.get<OrganizationSecurityPolicy>('/governance/security-policy', {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  updateSecurityPolicy: async (orgId: string, data: Partial<OrganizationSecurityPolicy>) => {
    const res = await api.patch<OrganizationSecurityPolicy>('/governance/security-policy', data, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  getDomains: async (orgId: string) => {
    const res = await api.get<OrganizationDomain[]>('/governance/domains', {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  addDomain: async (orgId: string, domain: string) => {
    const res = await api.post<OrganizationDomain>('/governance/domains', { domain }, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  verifyDomain: async (orgId: string, domainId: string) => {
    const res = await api.post(`/governance/domains/${domainId}/verify`, {}, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  deleteDomain: async (orgId: string, domainId: string) => {
    const res = await api.delete(`/governance/domains/${domainId}`, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  getExports: async (orgId: string) => {
    const res = await api.get<DataExportJob[]>('/governance/data-exports', {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  requestExport: async (orgId: string, export_type: string) => {
    const res = await api.post<DataExportJob>('/governance/data-exports', { export_type }, {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  },
  
  getComplianceOverview: async (orgId: string) => {
    const res = await api.get('/governance/compliance/overview', {
      headers: { 'X-Organization-Id': orgId }
    });
    return res.data;
  }
};

export const privacyApi = {
  getMyData: async () => {
    const res = await api.get('/privacy/me');
    return res.data;
  },
  requestExport: async () => {
    const res = await api.post('/privacy/export');
    return res.data;
  },
  requestDeletion: async () => {
    const res = await api.post('/privacy/delete-request');
    return res.data;
  }
};
