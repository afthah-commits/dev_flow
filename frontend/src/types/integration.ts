export interface Integration {
    id: string;
    organization_id: string;
    provider: string;
    name: string;
    status: string;
    configuration?: any;
    created_at: string;
}
