import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Organization } from '../types/organization';
import { organizationApi } from '../lib/organizationApi';
import { api } from '../lib/axios';

interface OrganizationContextType {
    currentOrganization: Organization | null;
    organizations: Organization[];
    setCurrentOrganization: (org: Organization) => void;
    refreshOrganizations: () => Promise<void>;
    isLoading: boolean;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const OrganizationProvider = ({ children }: { children: ReactNode }) => {
    const [currentOrganization, setCurrentOrganizationState] = useState<Organization | null>(null);
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const refreshOrganizations = async () => {
        try {
            const orgs = await organizationApi.list();
            setOrganizations(orgs);
            if (orgs.length > 0) {
                // if no current org, or current org not in list, set first
                if (!currentOrganization || !orgs.find((o: Organization) => o.id === currentOrganization.id)) {
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
    };

    const setCurrentOrganization = (org: Organization) => {
        setCurrentOrganizationState(org);
        localStorage.setItem('devflow_current_org', org.id);
        // set header for future requests
        api.defaults.headers.common['X-Organization-Id'] = org.id;
    };

    useEffect(() => {
        const loadInitial = async () => {
            setIsLoading(true);
            try {
                const orgs = await organizationApi.list();
                setOrganizations(orgs);
                
                const savedOrgId = localStorage.getItem('devflow_current_org');
                if (savedOrgId) {
                    const savedOrg = orgs.find((o: Organization) => o.id === savedOrgId);
                    if (savedOrg) {
                        setCurrentOrganization(savedOrg);
                        return;
                    }
                }
                
                if (orgs.length > 0) {
                    setCurrentOrganization(orgs[0]);
                }
            } catch (error) {
                console.error('Init orgs failed', error);
            } finally {
                setIsLoading(false);
            }
        };
        
        loadInitial();
    }, []);

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
