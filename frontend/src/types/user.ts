/**
 * User, Role & Permission Entities
 * Aligned with Neon PostgreSQL database schema
 */

export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending_verification';

export interface Role {
  id: string;
  name: string;
  description?: string;
  is_system?: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  avatar_url: string | null;
  bio?: string | null;
  status: UserStatus;
  email_verified: boolean;
  roles?: string[];
  created_at: string;
  updated_at: string;
}

export interface UserProfile extends User {
  hosted_count?: number;
  joined_count?: number;
}
