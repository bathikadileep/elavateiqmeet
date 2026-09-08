"""
SCIM 2.0 Bulk Resource Processor & Transactional Rollback Engine
================================================================
Implements RFC 7644 Section 3.7 ("Bulk Operations") for enterprise identity
synchronization (Okta, Azure AD, PingIdentity, OneLogin).

Features:
- RFC 7644 BulkRequest parsing and validation.
- Circular dependency detection and topological ordering for bulkId references.
- Dynamic temporary ID resolution (bulkId -> created entity ID).
- Atomic transaction simulation with failOnErrors threshold handling.
- Two-phase commit / compensation rollback ledger for partial failures.
- RFC 7644 Section 3.5.2 Patch operations (add, replace, remove).
- Comprehensive SCIM BulkResponse formatting with standard error structures.
"""

from __future__ import annotations

import copy
import enum
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("elevateiq.services.enterprise.scim")

SCIM_BULK_REQUEST_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:BulkRequest"
SCIM_BULK_RESPONSE_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:BulkResponse"
SCIM_ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"
SCIM_USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"


class ScimMethod(str, enum.Enum):
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ScimResourceType(str, enum.Enum):
    USER = "Users"
    GROUP = "Groups"


@dataclass
class BulkOperation:
    """Represents a single SCIM bulk operation in a batch."""
    method: ScimMethod
    path: str
    bulk_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    op_index: int = 0
    resource_type: Optional[ScimResourceType] = None
    resource_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], index: int) -> "BulkOperation":
        raw_method = data.get("method", "").upper()
        try:
            method = ScimMethod(raw_method)
        except ValueError:
            raise ValueError(f"Unsupported SCIM bulk method: {raw_method}")

        path = data.get("path", "").strip()
        bulk_id = data.get("bulkId")
        op_data = data.get("data")
        version = data.get("version")

        clean_path = path.lstrip("/")
        parts = clean_path.split("/")
        r_type = None
        r_id = None
        if parts:
            if parts[0].lower() == "users":
                r_type = ScimResourceType.USER
            elif parts[0].lower() == "groups":
                r_type = ScimResourceType.GROUP
            if len(parts) > 1:
                r_id = parts[1]

        return cls(
            method=method,
            path=path,
            bulk_id=bulk_id,
            data=op_data,
            version=version,
            op_index=index,
            resource_type=r_type,
            resource_id=r_id,
        )


@dataclass
class CompensationAction:
    """Record of an inverse action required to revert a committed operation."""
    action_type: str  # 'DELETE_CREATED', 'RESTORE_PREVIOUS', 'REAPPLY_GROUP'
    resource_type: ScimResourceType
    resource_id: str
    snapshot_state: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class BulkOperationResult:
    """Outcome of an individual bulk operation conforming to RFC 7644."""
    method: str
    bulk_id: Optional[str]
    status: int
    location: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "method": self.method,
            "status": str(self.status),
        }
        if self.bulk_id:
            res["bulkId"] = self.bulk_id
        if self.location:
            res["location"] = self.location
        if self.version:
            res["version"] = self.version
        if self.response:
            res["response"] = self.response
        return res


class ScimStorageRepository:
    """In-memory enterprise SCIM directory database mock for tests & routing."""

    def __init__(self) -> None:
        self.users: Dict[str, Dict[str, Any]] = {}
        self.groups: Dict[str, Dict[str, Any]] = {}

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = self.users.get(user_id)
        return copy.deepcopy(user) if user else None

    def save_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        clone = copy.deepcopy(data)
        clone["id"] = user_id
        clone.setdefault("meta", {})
        clone["meta"]["lastModified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        clone["meta"]["version"] = f'W/"{uuid.uuid4().hex[:12]}"'
        self.users[user_id] = clone
        return copy.deepcopy(clone)

    def delete_user(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            for group in self.groups.values():
                members = group.get("members", [])
                group["members"] = [m for m in members if m.get("value") != user_id]
            return True
        return False

    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        grp = self.groups.get(group_id)
        return copy.deepcopy(grp) if grp else None

    def save_group(self, group_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        clone = copy.deepcopy(data)
        clone["id"] = group_id
        clone.setdefault("meta", {})
        clone["meta"]["lastModified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        clone["meta"]["version"] = f'W/"{uuid.uuid4().hex[:12]}"'
        self.groups[group_id] = clone
        return copy.deepcopy(clone)

    def delete_group(self, group_id: str) -> bool:
        if group_id in self.groups:
            del self.groups[group_id]
            return True
        return False

    def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        for u in self.users.values():
            if u.get("userName", "").lower() == username.lower():
                return copy.deepcopy(u)
        return None


class ScimBulkProcessor:
    """
    High-throughput SCIM 2.0 Bulk Request Processor (RFC 7644 Section 3.7).
    Handles dependency ordering, bulkId variable interpolation,
    atomic transaction rollbacks, and RFC-compliant payload formatting.
    """

    MAX_OPERATIONS_LIMIT = 1000
    DEFAULT_FAIL_ON_ERRORS = 1

    def __init__(self, repository: Optional[ScimStorageRepository] = None, base_url: str = "https://elevateiq-backend.onrender.com/scim/v2") -> None:
        self.repo = repository or ScimStorageRepository()
        self.base_url = base_url.rstrip("/")
        self.bulk_id_map: Dict[str, str] = {}
        self.compensation_stack: List[CompensationAction] = []

    def process_bulk_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: validate request, sort operations, execute sequentially,
        track rollback ledger, and return RFC 7644 BulkResponse.
        """
        t0 = time.time()
        schemas = payload.get("schemas", [])
        if SCIM_BULK_REQUEST_SCHEMA not in schemas:
            return self._build_scim_error(
                status=400,
                scim_type="invalidSyntax",
                detail=f"Payload missing required schema '{SCIM_BULK_REQUEST_SCHEMA}'"
            )

        raw_ops = payload.get("Operations", [])
        if not isinstance(raw_ops, list):
            return self._build_scim_error(status=400, scim_type="invalidSyntax", detail="'Operations' must be an array")

        if len(raw_ops) > self.MAX_OPERATIONS_LIMIT:
            return self._build_scim_error(
                status=413,
                scim_type="tooMany",
                detail=f"Operations count {len(raw_ops)} exceeds server maximum limit of {self.MAX_OPERATIONS_LIMIT}"
            )

        fail_on_errors = payload.get("failOnErrors", self.DEFAULT_FAIL_ON_ERRORS)
        try:
            fail_on_errors = int(fail_on_errors)
        except (ValueError, TypeError):
            fail_on_errors = self.DEFAULT_FAIL_ON_ERRORS

        parsed_ops: List[BulkOperation] = []
        for idx, op_dict in enumerate(raw_ops):
            try:
                op = BulkOperation.from_dict(op_dict, index=idx)
                parsed_ops.append(op)
            except Exception as e:
                return self._build_scim_error(status=400, scim_type="invalidValue", detail=f"Operation at index {idx} invalid: {str(e)}")

        try:
            sorted_ops = self._topological_sort_operations(parsed_ops)
        except ValueError as err:
            return self._build_scim_error(status=400, scim_type="invalidValue", detail=f"Circular bulkId dependency detected: {str(err)}")

        results: List[BulkOperationResult] = []
        error_count = 0
        self.bulk_id_map.clear()
        self.compensation_stack.clear()
        aborted = False

        for op in sorted_ops:
            if error_count >= fail_on_errors:
                aborted = True
                break

            interpolated_op = self._interpolate_bulk_ids(op)
            res, compensation = self._execute_single_op(interpolated_op)
            results.append(res)

            if compensation:
                self.compensation_stack.append(compensation)

            if op.bulk_id and res.status in (200, 201):
                created_id = res.response.get("id") if res.response else None
                if created_id:
                    self.bulk_id_map[op.bulk_id] = created_id

            if res.status >= 400:
                error_count += 1
                if error_count >= fail_on_errors:
                    logger.warning(
                        "SCIM bulk operations error threshold reached (%d errors >= failOnErrors %d). Aborting batch.",
                        error_count, fail_on_errors
                    )
                    aborted = True
                    break

        if aborted and fail_on_errors <= 1:
            self._execute_rollback()

        elapsed_ms = round((time.time() - t0) * 1000, 2)
        logger.info(
            "SCIM bulk request completed in %sms. Executed: %d, Errors: %d, Aborted: %s",
            elapsed_ms, len(results), error_count, aborted
        )

        return {
            "schemas": [SCIM_BULK_RESPONSE_SCHEMA],
            "Operations": [r.to_dict() for r in results],
        }

    def _execute_single_op(self, op: BulkOperation) -> Tuple[BulkOperationResult, Optional[CompensationAction]]:
        """Executes a single SCIM operation against repository and tracks undo action."""
        if not op.resource_type:
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=400,
                response=self._scim_error_payload(400, "invalidPath", f"Unrecognized resource path '{op.path}'"),
            ), None

        if op.method == ScimMethod.POST:
            return self._handle_post(op)
        elif op.method == ScimMethod.PUT:
            return self._handle_put(op)
        elif op.method == ScimMethod.PATCH:
            return self._handle_patch(op)
        elif op.method == ScimMethod.DELETE:
            return self._handle_delete(op)
        else:
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=405,
                response=self._scim_error_payload(405, "invalidValue", f"Unsupported method {op.method}"),
            ), None

    def _handle_post(self, op: BulkOperation) -> Tuple[BulkOperationResult, Optional[CompensationAction]]:
        """Handles POST (Resource Creation)."""
        data = copy.deepcopy(op.data or {})
        assigned_id = str(uuid.uuid4())

        if op.resource_type == ScimResourceType.USER:
            user_name = data.get("userName")
            if not user_name:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=400,
                    response=self._scim_error_payload(400, "invalidValue", "Missing required field 'userName'"),
                ), None

            existing = self.repo.find_user_by_username(user_name)
            if existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=409,
                    response=self._scim_error_payload(409, "uniqueness", f"User with userName '{user_name}' already exists"),
                ), None

            data["schemas"] = [SCIM_USER_SCHEMA]
            saved = self.repo.save_user(assigned_id, data)
            loc = f"{self.base_url}/Users/{assigned_id}"
            comp = CompensationAction(
                action_type="DELETE_CREATED",
                resource_type=ScimResourceType.USER,
                resource_id=assigned_id,
                description=f"Delete created user {assigned_id}"
            )
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=201,
                location=loc,
                response=saved,
                version=saved.get("meta", {}).get("version"),
            ), comp

        elif op.resource_type == ScimResourceType.GROUP:
            display_name = data.get("displayName")
            if not display_name:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=400,
                    response=self._scim_error_payload(400, "invalidValue", "Missing required field 'displayName'"),
                ), None

            data["schemas"] = [SCIM_GROUP_SCHEMA]
            data.setdefault("members", [])
            saved = self.repo.save_group(assigned_id, data)
            loc = f"{self.base_url}/Groups/{assigned_id}"
            comp = CompensationAction(
                action_type="DELETE_CREATED",
                resource_type=ScimResourceType.GROUP,
                resource_id=assigned_id,
                description=f"Delete created group {assigned_id}"
            )
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=201,
                location=loc,
                response=saved,
                version=saved.get("meta", {}).get("version"),
            ), comp

        return BulkOperationResult(method=op.method.value, bulk_id=op.bulk_id, status=400), None

    def _handle_put(self, op: BulkOperation) -> Tuple[BulkOperationResult, Optional[CompensationAction]]:
        """Handles PUT (Full Resource Replacement)."""
        target_id = op.resource_id
        if not target_id:
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=400,
                response=self._scim_error_payload(400, "invalidPath", "PUT requires resource ID in path"),
            ), None

        data = copy.deepcopy(op.data or {})

        if op.resource_type == ScimResourceType.USER:
            existing = self.repo.get_user(target_id)
            if not existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=404,
                    response=self._scim_error_payload(404, "noTarget", f"User '{target_id}' not found"),
                ), None

            if op.version and existing.get("meta", {}).get("version") != op.version:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=412,
                    response=self._scim_error_payload(412, "failedPrecondition", "Version mismatch / concurrency conflict"),
                ), None

            data["schemas"] = [SCIM_USER_SCHEMA]
            saved = self.repo.save_user(target_id, data)
            comp = CompensationAction(
                action_type="RESTORE_PREVIOUS",
                resource_type=ScimResourceType.USER,
                resource_id=target_id,
                snapshot_state=existing,
                description=f"Restore user {target_id} to pre-PUT state"
            )
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=200,
                location=f"{self.base_url}/Users/{target_id}",
                response=saved,
                version=saved.get("meta", {}).get("version"),
            ), comp

        elif op.resource_type == ScimResourceType.GROUP:
            existing = self.repo.get_group(target_id)
            if not existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=404,
                    response=self._scim_error_payload(404, "noTarget", f"Group '{target_id}' not found"),
                ), None

            data["schemas"] = [SCIM_GROUP_SCHEMA]
            saved = self.repo.save_group(target_id, data)
            comp = CompensationAction(
                action_type="RESTORE_PREVIOUS",
                resource_type=ScimResourceType.GROUP,
                resource_id=target_id,
                snapshot_state=existing,
                description=f"Restore group {target_id} to pre-PUT state"
            )
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=200,
                location=f"{self.base_url}/Groups/{target_id}",
                response=saved,
                version=saved.get("meta", {}).get("version"),
            ), comp

        return BulkOperationResult(method=op.method.value, bulk_id=op.bulk_id, status=400), None

    def _handle_patch(self, op: BulkOperation) -> Tuple[BulkOperationResult, Optional[CompensationAction]]:
        """Handles PATCH (Incremental updates: RFC 7644 Section 3.5.2)."""
        target_id = op.resource_id
        if not target_id:
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=400,
                response=self._scim_error_payload(400, "invalidPath", "PATCH requires resource ID in path"),
            ), None

        if op.resource_type == ScimResourceType.USER:
            existing = self.repo.get_user(target_id)
            if not existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=404,
                    response=self._scim_error_payload(404, "noTarget", f"User '{target_id}' not found"),
                ), None

            patched_data, err = self._apply_scim_patch(existing, op.data or {})
            if err:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=400,
                    response=self._scim_error_payload(400, "invalidSyntax", err),
                ), None

            saved = self.repo.save_user(target_id, patched_data)
            comp = CompensationAction(
                action_type="RESTORE_PREVIOUS",
                resource_type=ScimResourceType.USER,
                resource_id=target_id,
                snapshot_state=existing,
                description=f"Restore user {target_id} to pre-PATCH state"
            )
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=200,
                location=f"{self.base_url}/Users/{target_id}",
                response=saved,
                version=saved.get("meta", {}).get("version"),
            ), comp

        elif op.resource_type == ScimResourceType.GROUP:
            existing = self.repo.get_group(target_id)
            if not existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=404,
                    response=self._scim_error_payload(404, "noTarget", f"Group '{target_id}' not found"),
                ), None

            patched_data, err = self._apply_scim_patch(existing, op.data or {})
            if err:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=400,
                    response=self._scim_error_payload(400, "invalidSyntax", err),
                ), None

            saved = self.repo.save_group(target_id, patched_data)
            comp = CompensationAction(
                action_type="RESTORE_PREVIOUS",
                resource_type=ScimResourceType.GROUP,
                resource_id=target_id,
                snapshot_state=existing,
                description=f"Restore group {target_id} to pre-PATCH state"
            )
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=200,
                location=f"{self.base_url}/Groups/{target_id}",
                response=saved,
                version=saved.get("meta", {}).get("version"),
            ), comp

        return BulkOperationResult(method=op.method.value, bulk_id=op.bulk_id, status=400), None

    def _handle_delete(self, op: BulkOperation) -> Tuple[BulkOperationResult, Optional[CompensationAction]]:
        """Handles DELETE."""
        target_id = op.resource_id
        if not target_id:
            return BulkOperationResult(
                method=op.method.value,
                bulk_id=op.bulk_id,
                status=400,
                response=self._scim_error_payload(400, "invalidPath", "DELETE requires resource ID in path"),
            ), None

        if op.resource_type == ScimResourceType.USER:
            existing = self.repo.get_user(target_id)
            if not existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=404,
                    response=self._scim_error_payload(404, "noTarget", f"User '{target_id}' not found"),
                ), None

            self.repo.delete_user(target_id)
            comp = CompensationAction(
                action_type="RESTORE_PREVIOUS",
                resource_type=ScimResourceType.USER,
                resource_id=target_id,
                snapshot_state=existing,
                description=f"Re-create deleted user {target_id}"
            )
            return BulkOperationResult(method=op.method.value, bulk_id=op.bulk_id, status=204), comp

        elif op.resource_type == ScimResourceType.GROUP:
            existing = self.repo.get_group(target_id)
            if not existing:
                return BulkOperationResult(
                    method=op.method.value,
                    bulk_id=op.bulk_id,
                    status=404,
                    response=self._scim_error_payload(404, "noTarget", f"Group '{target_id}' not found"),
                ), None

            self.repo.delete_group(target_id)
            comp = CompensationAction(
                action_type="RESTORE_PREVIOUS",
                resource_type=ScimResourceType.GROUP,
                resource_id=target_id,
                snapshot_state=existing,
                description=f"Re-create deleted group {target_id}"
            )
            return BulkOperationResult(method=op.method.value, bulk_id=op.bulk_id, status=204), comp

        return BulkOperationResult(method=op.method.value, bulk_id=op.bulk_id, status=400), None

    def _apply_scim_patch(self, resource: Dict[str, Any], patch_body: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Applies SCIM 2.0 Patch operations (add, replace, remove)."""
        target = copy.deepcopy(resource)
        patch_ops = patch_body.get("Operations", [])
        if not isinstance(patch_ops, list):
            return target, "'Operations' must be a list in PATCH body"

        for p_op in patch_ops:
            op_name = p_op.get("op", "").lower()
            path = p_op.get("path")
            val = p_op.get("value")

            if op_name == "add":
                if path:
                    if path == "members" and isinstance(val, list):
                        target.setdefault("members", [])
                        target["members"].extend(val)
                    else:
                        target[path] = val
                elif isinstance(val, dict):
                    target.update(val)

            elif op_name == "replace":
                if path:
                    target[path] = val
                elif isinstance(val, dict):
                    target.update(val)

            elif op_name == "remove":
                if not path:
                    return target, "Remove operation requires a path"
                member_match = re.match(r'members\[value\s+eq\s+"?([^"\]]+)"?\]', path)
                if member_match:
                    target_member_id = member_match.group(1)
                    target["members"] = [m for m in target.get("members", []) if m.get("value") != target_member_id]
                elif path in target:
                    del target[path]

        return target, None

    def _interpolate_bulk_ids(self, op: BulkOperation) -> BulkOperation:
        """Deeply resolves bulkId:identifier into created UUIDs."""
        new_op = copy.deepcopy(op)

        if "bulkId:" in new_op.path:
            for b_id, real_id in self.bulk_id_map.items():
                new_op.path = new_op.path.replace(f"bulkId:{b_id}", real_id)
            if new_op.resource_id and new_op.resource_id.startswith("bulkId:"):
                raw_ref = new_op.resource_id[7:]
                if raw_ref in self.bulk_id_map:
                    new_op.resource_id = self.bulk_id_map[raw_ref]

        if new_op.data:
            new_op.data = self._replace_bulk_id_recursive(new_op.data)

        return new_op

    def _replace_bulk_id_recursive(self, item: Any) -> Any:
        if isinstance(item, str):
            if item.startswith("bulkId:"):
                ref = item[7:]
                return self.bulk_id_map.get(ref, item)
            return item
        elif isinstance(item, list):
            return [self._replace_bulk_id_recursive(x) for x in item]
        elif isinstance(item, dict):
            return {k: self._replace_bulk_id_recursive(v) for k, v in item.items()}
        return item

    def _topological_sort_operations(self, operations: List[BulkOperation]) -> List[BulkOperation]:
        """
        Orders operations to ensure bulkId definitions run before bulkId consumers.
        Detects cycles.
        """
        bulk_producers: Dict[str, BulkOperation] = {}
        for op in operations:
            if op.bulk_id:
                bulk_producers[op.bulk_id] = op

        graph: Dict[int, Set[int]] = {op.op_index: set() for op in operations}

        for op in operations:
            deps = self._extract_bulk_id_references(op)
            for d in deps:
                if d in bulk_producers:
                    producer_idx = bulk_producers[d].op_index
                    if producer_idx != op.op_index:
                        graph[op.op_index].add(producer_idx)

        in_degree = {i: len(deps) for i, deps in graph.items()}
        queue = [i for i, deg in in_degree.items() if deg == 0]
        sorted_indices: List[int] = []

        dependents: Dict[int, Set[int]] = {op.op_index: set() for op in operations}
        for consumer, producers in graph.items():
            for p in producers:
                dependents[p].add(consumer)

        while queue:
            node = queue.pop(0)
            sorted_indices.append(node)
            for consumer in dependents[node]:
                in_degree[consumer] -= 1
                if in_degree[consumer] == 0:
                    queue.append(consumer)

        if len(sorted_indices) != len(operations):
            raise ValueError("Cycle detected in bulkId dependency relationships")

        op_map = {op.op_index: op for op in operations}
        return [op_map[idx] for idx in sorted_indices]

    def _extract_bulk_id_references(self, op: BulkOperation) -> Set[str]:
        """Scans operation path and data for bulkId: references."""
        refs: Set[str] = set()
        if "bulkId:" in op.path:
            matches = re.findall(r'bulkId:([A-Za-z0-9_\-]+)', op.path)
            refs.update(matches)

        def walk(val: Any) -> None:
            if isinstance(val, str) and val.startswith("bulkId:"):
                refs.add(val[7:])
            elif isinstance(val, list):
                for elem in val:
                    walk(elem)
            elif isinstance(val, dict):
                for v in val.values():
                    walk(v)

        if op.data:
            walk(op.data)
        return refs

    def _execute_rollback(self) -> None:
        """Executes compensation stack in reverse chronological order."""
        logger.warning("Executing SCIM Bulk compensation rollback stack (%d actions)...", len(self.compensation_stack))
        while self.compensation_stack:
            action = self.compensation_stack.pop()
            try:
                if action.action_type == "DELETE_CREATED":
                    if action.resource_type == ScimResourceType.USER:
                        self.repo.delete_user(action.resource_id)
                    elif action.resource_type == ScimResourceType.GROUP:
                        self.repo.delete_group(action.resource_id)
                elif action.action_type == "RESTORE_PREVIOUS" and action.snapshot_state:
                    if action.resource_type == ScimResourceType.USER:
                        self.repo.save_user(action.resource_id, action.snapshot_state)
                    elif action.resource_type == ScimResourceType.GROUP:
                        self.repo.save_group(action.resource_id, action.snapshot_state)
                logger.info("Compensated action: %s", action.description)
            except Exception as e:
                logger.error("Failed to execute rollback action %s: %s", action.description, str(e))

    def _scim_error_payload(self, status: int, scim_type: str, detail: str) -> Dict[str, Any]:
        return {
            "schemas": [SCIM_ERROR_SCHEMA],
            "status": str(status),
            "scimType": scim_type,
            "detail": detail,
        }

    def _build_scim_error(self, status: int, scim_type: str, detail: str) -> Dict[str, Any]:
        return self._scim_error_payload(status, scim_type, detail)
