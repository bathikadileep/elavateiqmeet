"""
ElevateIQ — SCIM 2.0 Group Resource & Team Membership Manager
==============================================================
Implements SCIM 2.0 /Groups endpoints for Okta, Azure AD, and PingFederate team role syncing.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

log = logging.getLogger("elevateiq.services.enterprise.scim_groups")


class SCIMGroupManager:
    """Enterprise SCIM 2.0 Group Resource Engine."""

    def __init__(self):
        self._groups: Dict[str, Dict[str, Any]] = {}

    def create_group(self, group_name: str, member_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new SCIM group resource."""
        group_id = f"scim_grp_{len(self._groups) + 1001}"
        now_iso = datetime.now(timezone.utc).isoformat()

        group = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": group_id,
            "displayName": group_name,
            "members": [{"value": m_id} for m_id in (member_ids or [])],
            "meta": {
                "resourceType": "Group",
                "created": now_iso,
                "lastModified": now_iso,
                "location": f"/api/scim/v2/Groups/{group_id}",
            },
        }

        self._groups[group_id] = group
        log.info("Created SCIM group '%s' (ID: %s, Members: %d)", group_name, group_id, len(member_ids or []))
        return group

    def add_member_to_group(self, group_id: str, member_id: str) -> Optional[Dict[str, Any]]:
        """Add user member to SCIM group."""
        grp = self._groups.get(group_id)
        if not grp:
            return None

        if not any(m["value"] == member_id for m in grp["members"]):
            grp["members"].append({"value": member_id})
            grp["meta"]["lastModified"] = datetime.now(timezone.utc).isoformat()

        log.info("Added member %s to SCIM group %s", member_id, group_id)
        return grp
