import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { Organization } from '../types/organization';
import { organizationApi } from '../lib/organizationApi';
import { api } from '../lib/axios';
import { useAuth } from '../hooks/useAuth';

interface OrganizationContextType {
    currentOrganization: Organization | null;
    organizations: Organization[];
    setCurrentOrganization: (org: Organization) => void;
    refreshOrganizations: () => Promise<void>;
    isLoading: boolean;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const OrganizationProvider = ({ children }: { children: ReactNode }) => {
    const { user, isAuthenticated } = useAuth();
    const [currentOrganization, setCurrentOrganizationState] = useState<Organization | null>(null);
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const setCurrentOrganization = useCallback((org: Organization) => {
        setCurrentOrganizationState(org);
        if (typeof window !== 'undefined') {
            localStorage.setItem('devflow_current_org', org.id);
        }
        api.defaults.headers.common['X-Organization-Id'] = org.id;
    }, []);

    const refreshOrganizations = useCallback(async () => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        if (!token) {
            setOrganizations([]);
            setCurrentOrganizationState(null);
            setIsLoading(false);
            return;
        }

        setIsLoading(true);
        try {
            let orgs = await organizationApi.list();
            // If user has no organizations (e.g. legacy/edge cases), bootstrap a default workspace
            if (orgs.length === 0) {
                const orgName = user?.name ? `${user.name}'s Workspace` : 'My Workspace';
                try {
                    const newOrg = await organizationApi.create({ name: orgName });
                    orgs = [newOrg];
                } catch {
                    // Organization creation may fail if backend already bootstrapped in parallel
                    orgs = await organizationApi.list();
                }
            }
            setOrganizations(orgs);

            if (orgs.length > 0) {
                const savedOrgId = typeof window !== 'undefined' ? localStorage.getItem('devflow_current_org') : null;
                const savedOrg = savedOrgId ? orgs.find((o: Organization) => o.id === savedOrgId) : null;
                if (savedOrg) {
                    setCurrentOrganization(savedOrg);
                } else {
                    setCurrentOrganization(orgs[0]);
                }
            } else {
                setCurrentOrganizationState(null);
            }
        } catch (error) {
            console.error('Failed to load organizations', error);
        } finally {
            setIsLoading(false);
        }
    }, [user, setCurrentOrganization]);

    useEffect(() => {
        if (isAuthenticated) {
            refreshOrganizations();
        } else {
            setOrganizations([]);
            setCurrentOrganizationState(null);
            setIsLoading(false);
        }
    }, [isAuthenticated, refreshOrganizations]);

    return (
        <OrganizationContext.Provider value={{
            currentOrganization,
            organizations,
            setCurrentOrganization,
            refreshOrganizations,
            isLoading
        }}>
            {children}
        </OrganizationContext.Provider>
    );
};

export const useOrganization = () => {
    const context = useContext(OrganizationContext);
    if (context === undefined) {
        throw new Error('useOrganization must be used within an OrganizationProvider');
    }
    return context;
};
