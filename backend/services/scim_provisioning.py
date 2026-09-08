"""
ElevateIQ — SCIM 2.0 Identity Provisioning Protocol Handler
============================================================
Implements RFC 7644 SCIM 2.0 User & Group provisioning protocol handlers for
Okta, Microsoft Azure AD / Entra ID, and OneLogin automated SSO user lifecycle management.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.scim")


class SCIMProvisioningEngine:
    """Enterprise SCIM 2.0 Protocol Handler Engine."""

    def __init__(self):
        self._scim_users: Dict[str, Dict[str, Any]] = {}
        self._scim_groups: Dict[str, Dict[str, Any]] = {}

    def create_user(self, scim_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process SCIM POST /Users payload to provision enterprise user account.
        """
        user_name = scim_payload.get("userName")
        emails = scim_payload.get("emails", [])
        primary_email = emails[0].get("value") if emails else user_name
        name_meta = scim_payload.get("name", {})
        display_name = scim_payload.get("displayName") or f"{name_meta.get('givenName', '')} {name_meta.get('familyName', '')}".strip()

        scim_id = f"scim_usr_{len(self._scim_users) + 1001}"
        now_iso = datetime.now(timezone.utc).isoformat()

        user_resource = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": scim_id,
            "userName": user_name,
            "name": name_meta,
            "displayName": display_name,
            "emails": [{"value": primary_email, "type": "work", "primary": True}],
            "active": scim_payload.get("active", True),
            "meta": {
                "resourceType": "User",
                "created": now_iso,
                "lastModified": now_iso,
                "location": f"/api/scim/v2/Users/{scim_id}",
            },
        }

        self._scim_users[scim_id] = user_resource
        log.info("Provisioned SCIM user: %s (ID: %s, Email: %s)", user_name, scim_id, primary_email)
        return user_resource

    def update_user_status(self, scim_id: str, active: bool) -> Optional[Dict[str, Any]]:
        """Process SCIM PATCH or PUT user activation status change."""
        user = self._scim_users.get(scim_id)
        if not user:
            return None

        user["active"] = active
        user["meta"]["lastModified"] = datetime.now(timezone.utc).isoformat()
        log.info("Updated SCIM user status: %s -> Active=%s", scim_id, active)
        return user

    def delete_user(self, scim_id: str) -> bool:
        """Process SCIM DELETE /Users/{id} deprivisioning request."""
        if scim_id in self._scim_users:
            del self._scim_users[scim_id]
            log.info("Deprovisioned SCIM user: %s", scim_id)
            return True
        return False

    def list_users(self, start_index: int = 1, count: int = 100) -> Dict[str, Any]:
        """Process SCIM GET /Users list query."""
        all_users = list(self._scim_users.values())
        slice_users = all_users[start_index - 1 : start_index - 1 + count]

        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(all_users),
            "startIndex": start_index,
            "itemsPerPage": len(slice_users),
            "Resources": slice_users,
        }
