"""
ElevateIQ — Fine-Grained Role-Based Access Control (RBAC) Engine
=================================================================
Evaluates granular permission policies (meeting:create, meeting:record, meeting:mute_all,
summary:export, admin:user_manage, analytics:view) against user role matrices.
"""

import json
import logging
from typing import Dict, Any, List, Set, Optional

log = logging.getLogger("elevateiq.services.rbac")


DEFAULT_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "super_admin": {
        "meeting:create", "meeting:join", "meeting:end", "meeting:record", "meeting:mute_all",
        "meeting:kick", "meeting:whiteboard", "meeting:screen_share", "summary:generate",
        "summary:export", "compliance:export", "compliance:forget", "admin:user_manage",
        "admin:roles_manage", "analytics:view", "developer:keys_manage"
    },
    "host": {
        "meeting:create", "meeting:join", "meeting:end", "meeting:record", "meeting:mute_all",
        "meeting:kick", "meeting:whiteboard", "meeting:screen_share", "summary:generate",
        "summary:export", "analytics:view"
    },
    "co_host": {
        "meeting:join", "meeting:record", "meeting:mute_all", "meeting:kick",
        "meeting:whiteboard", "meeting:screen_share", "summary:generate"
    },
    "participant": {
        "meeting:join", "meeting:whiteboard", "meeting:screen_share", "chat:send"
    },
    "guest": {
        "meeting:join", "chat:send"
    }
}


class RBACPolicyEvaluator:
    """Enterprise Policy Decision Point (PDP)."""

    def __init__(self):
        self._role_matrix: Dict[str, Set[str]] = dict(DEFAULT_ROLE_PERMISSIONS)

    def grant_permission_to_role(self, role_name: str, permission: str) -> None:
        """Grant permission token to target role."""
        if role_name not in self._role_matrix:
            self._role_matrix[role_name] = set()
        self._role_matrix[role_name].add(permission)
        log.info("Granted permission '%s' to role '%s'", permission, role_name)

    def revoke_permission_from_role(self, role_name: str, permission: str) -> None:
        """Revoke permission token from target role."""
        if role_name in self._role_matrix and permission in self._role_matrix[role_name]:
            self._role_matrix[role_name].remove(permission)
            log.info("Revoked permission '%s' from role '%s'", permission, role_name)

    def evaluate_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Evaluate if user assigned roles hold the required permission token."""
        if not user_roles:
            return False

        for role in user_roles:
            permissions = self._role_matrix.get(role, set())
            if required_permission in permissions or "*" in permissions:
                return True
        return False

    def list_role_permissions(self, role_name: str) -> List[str]:
        """List all permission tokens assigned to a role."""
        return sorted(list(self._role_matrix.get(role_name, set())))


_GLOBAL_RBAC_EVALUATOR = RBACPolicyEvaluator()

def get_rbac_evaluator() -> RBACPolicyEvaluator:
    return _GLOBAL_RBAC_EVALUATOR
