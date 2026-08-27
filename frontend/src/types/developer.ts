/**
 * ElevateIQ Developer API Gateway & Webhook Marketplace — TypeScript Definitions
 */

export interface APIKeyItem {
  id: string;
  key_name: string;
  key_prefix: string;
  rate_limit: number;
  is_active: boolean;
  created_at: string;
  raw_api_key?: string;
}

export interface WebhookItem {
  id: string;
  target_url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
  secret_token?: string;
}

export interface WebhookLogItem {
  id: string;
  subscription_id: string;
  event_type: string;
  status_code?: number;
  attempts: number;
  is_success: boolean;
  delivered_at: string;
}
