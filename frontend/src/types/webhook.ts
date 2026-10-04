export interface WebhookEndpoint {
    id: string;
    organization_id: string;
    name: string;
    url: string;
    active: boolean;
    subscribed_events: string[];
    created_at: string;
}
