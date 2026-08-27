/**
 * ElevateIQ Enterprise Security Suite — TypeScript Definitions
 */

export interface AuditLogItem {
  id: string;
  event_type: string;
  actor_id?: string;
  ip_address?: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface IPRuleItem {
  id: string;
  cidr_range: string;
  description: string;
  is_allowed: boolean;
  created_at: string;
}

export interface DLPOffenseItem {
  id: string;
  user_id?: string;
  offense_type: string;
  detected_in: string;
  snippet: string;
  action_taken: string;
  timestamp: string;
}

export interface SSOProviderItem {
  provider_name: string;
  display_name: string;
  is_enabled: boolean;
}
