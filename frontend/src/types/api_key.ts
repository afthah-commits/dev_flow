export interface APIKey {
    id: string;
    organization_id: string;
    name: string;
    key_prefix: string;
    raw_key?: string; // Only populated on creation
    scopes: string[];
    last_used_at?: string;
    expires_at?: string;
    revoked_at?: string;
    created_at: string;
}
