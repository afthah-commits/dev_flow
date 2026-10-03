export enum OrganizationRole {
    OWNER = "OWNER",
    ADMIN = "ADMIN",
    MEMBER = "MEMBER"
}

export interface Organization {
    id: string;
    name: string;
    slug: string;
    description?: string;
    logo_url?: string;
    created_by: string;
    created_at: string;
    updated_at?: string;
}

export interface OrganizationMember {
    id: string;
    organization_id: string;
    user_id: string;
    role: OrganizationRole;
    joined_at: string;
}

export interface Team {
    id: string;
    organization_id: string;
    name: string;
    slug: string;
    description?: string;
    created_by: string;
    created_at: string;
    updated_at?: string;
}

export interface TeamMember {
    id: string;
    team_id: string;
    user_id: string;
    joined_at: string;
}

export interface OrganizationInvitation {
    id: string;
    organization_id: string;
    email: string;
    role: OrganizationRole;
    invited_by: string;
    expires_at: string;
    accepted_at?: string;
    created_at: string;
}
