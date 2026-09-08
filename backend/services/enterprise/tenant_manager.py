"""
ElevateIQ — Multi-Tenant Enterprise Organization & Workspace Service
=====================================================================
Manages enterprise organization hierarchy, domain validation, custom branding,
custom SSL certificates, IP whitelist policies, and sub-tenant isolation.
"""

import re
import json
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

log = logging.getLogger("elevateiq.services.tenant")


class TenantOrganization:
    """Enterprise Organization Domain Model."""

    def __init__(self, org_id: str, name: str, domain: str, max_users: int = 500, max_concurrent_meetings: int = 50):
        self.org_id = org_id
        self.name = name
        self.domain = domain.lower().strip()
        self.max_users = max_users
        self.max_concurrent_meetings = max_concurrent_meetings
        self.allowed_ip_cidrs: List[str] = []
        self.custom_logo_url: Optional[str] = None
        self.custom_theme_json: Dict[str, str] = {
            "primaryColor": "#00f2fe",
            "backgroundColor": "#080911",
            "accentColor": "#7928ca"
        }
        self.is_active = True
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "org_id": self.org_id,
            "name": self.name,
            "domain": self.domain,
            "max_users": self.max_users,
            "max_concurrent_meetings": self.max_concurrent_meetings,
            "allowed_ip_cidrs": self.allowed_ip_cidrs,
            "custom_logo_url": self.custom_logo_url,
            "custom_theme": self.custom_theme_json,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


class TenantManagerService:
    """Multi-Tenant Isolation & Policy Management Engine."""

    def __init__(self):
        self._organizations: Dict[str, TenantOrganization] = {}
        self._domain_map: Dict[str, str] = {}

    def create_organization(self, name: str, domain: str, max_users: int = 500, max_concurrent_meetings: int = 50) -> TenantOrganization:
        """Create and register a new enterprise organization tenant."""
        cleaned_domain = domain.lower().strip()
        if cleaned_domain in self._domain_map:
            raise ValueError(f"Organization with domain '{cleaned_domain}' already registered.")

        org_id = f"org_{uuid.uuid4().hex[:12]}"
        org = TenantOrganization(org_id, name, cleaned_domain, max_users, max_concurrent_meetings)
        
        self._organizations[org_id] = org
        self._domain_map[cleaned_domain] = org_id
        log.info("Registered enterprise tenant '%s' (%s) with ID %s", name, cleaned_domain, org_id)
        return org

    def get_organization_by_domain(self, domain: str) -> Optional[TenantOrganization]:
        """Lookup organization tenant by email domain name."""
        cleaned_domain = domain.lower().strip()
        org_id = self._domain_map.get(cleaned_domain)
        if org_id:
            return self._organizations.get(org_id)
        return None

    def update_tenant_branding(self, org_id: str, logo_url: str, theme: Dict[str, str]) -> TenantOrganization:
        """Update enterprise custom logo and UI theme settings."""
        org = self._organizations.get(org_id)
        if not org:
            raise ValueError(f"Tenant organization '{org_id}' not found.")

        if logo_url:
            org.custom_logo_url = logo_url
        if theme:
            org.custom_theme_json.update(theme)

        log.info("Updated branding configuration for tenant %s", org_id)
        return org

    def set_ip_whitelist(self, org_id: str, cidr_list: List[str]) -> TenantOrganization:
        """Set IP CIDR whitelist restrictions for enterprise organization access."""
        org = self._organizations.get(org_id)
        if not org:
            raise ValueError(f"Tenant organization '{org_id}' not found.")

        valid_cidrs = [c.strip() for c in cidr_list if c and "/" in c]
        org.allowed_ip_cidrs = valid_cidrs
        log.info("Set %d IP whitelist rules for tenant %s", len(valid_cidrs), org_id)
        return org

    def validate_ip_access(self, org_id: str, client_ip: str) -> bool:
        """Verify client IP address against tenant whitelist rules."""
        import ipaddress
        org = self._organizations.get(org_id)
        if not org or not org.allowed_ip_cidrs:
            return True # No restriction if whitelist is empty

        try:
            ip_obj = ipaddress.ip_address(client_ip)
            for cidr in org.allowed_ip_cidrs:
                network = ipaddress.ip_network(cidr, strict=False)
                if ip_obj in network:
                    return True
        except Exception:
            pass

        return False


_GLOBAL_TENANT_MANAGER = TenantManagerService()

def get_tenant_manager() -> TenantManagerService:
    return _GLOBAL_TENANT_MANAGER
