import { api } from './axios';
import { Organization, OrganizationMember, OrganizationRole } from '../types/organization';

export const organizationApi = {
    create: async (data: { name: string; description?: string }) => {
        const response = await api.post<Organization>('/organizations', data);
        return response.data;
    },
    list: async () => {
        const response = await api.get<Organization[]>('/organizations');
        return response.data;
    },
    get: async (id: string) => {
        const response = await api.get<Organization>(`/organizations/${id}`);
        return response.data;
    },
    update: async (id: string, data: Partial<Organization>) => {
        const response = await api.patch<Organization>(`/organizations/${id}`, data);
        return response.data;
    },
    delete: async (id: string) => {
        const response = await api.delete(`/organizations/${id}`);
        return response.data;
    },
    listMembers: async (orgId: string) => {
        const response = await api.get<OrganizationMember[]>(`/organizations/${orgId}/members`);
        return response.data;
    },
    updateMemberRole: async (orgId: string, memberId: string, role: OrganizationRole) => {
        const response = await api.patch<OrganizationMember>(`/organizations/${orgId}/members/${memberId}`, { role });
        return response.data;
    },
    removeMember: async (orgId: string, memberId: string) => {
        const response = await api.delete(`/organizations/${orgId}/members/${memberId}`);
        return response.data;
    }
};
