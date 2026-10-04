export interface Integration {
  id: string;
  organization_id: string;
  provider: string;
  name: string;
  status: string;
  enabled: boolean;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string | null;
  last_sync_at: string | null;
  last_error: string | null;
}

export interface WebhookEndpoint {
  id: string;
  organization_id: string;
  name: string;
  url: string;
  active: boolean;
  subscribed_events: string[];
  created_at: string;
}

export interface ApiUsage {
  total_requests: number;
  webhook_deliveries: number;
  failed_deliveries: number;
  integration_events: number;
}
