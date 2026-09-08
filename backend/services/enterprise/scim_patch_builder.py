"""
ElevateIQ — SCIM 2.0 PATCH Operation Evaluator & Builder (RFC 7644 §3.5.2)
=============================================================================
Implements standard RFC 7644 PATCH grammar for granular updates to user/group
resources without full object replacement. Supports 'add', 'remove', and 'replace'
operations, sub-attribute path traversal, and multi-valued attribute filtering.
"""

from __future__ import annotations

import copy
import enum
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

log = logging.getLogger("elevateiq.services.enterprise.scim.patch")


class PatchOp(str, enum.Enum):
    """RFC 7644 §3.5.2 Defined Patch Operations."""
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"


@dataclass
class SCIMPatchOperation:
    """Individual PATCH operation entry."""
    op: PatchOp
    path: Optional[str] = None
    value: Any = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SCIMPatchOperation":
        raw_op = str(data.get("op", "")).lower()
        if raw_op not in ("add", "remove", "replace"):
            raise ValueError(f"Invalid SCIM PATCH op: '{data.get('op')}'")
        return cls(
            op=PatchOp(raw_op),
            path=data.get("path"),
            value=data.get("value"),
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"op": self.op.value}
        if self.path is not None:
            d["path"] = self.path
        if self.value is not None:
            d["value"] = self.value
        return d


class SCIMPatchEvaluator:
    """
    Evaluates RFC 7644 PATCH operations against in-memory SCIM User/Group resource dictionaries.
    Applies transactional attribute changes with validation.
    """

    @classmethod
    def apply_patch(cls, resource: Dict[str, Any], operations: List[SCIMPatchOperation]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply a list of PATCH operations to a SCIM resource copy.
        Returns: (modified_resource, list_of_applied_modifications)
        """
        target = copy.deepcopy(resource)
        audit_log: List[str] = []

        for idx, operation in enumerate(operations):
            op = operation.op
            path = operation.path
            val = operation.value

            if op == PatchOp.ADD:
                cls._handle_add(target, path, val, audit_log)
            elif op == PatchOp.REPLACE:
                cls._handle_replace(target, path, val, audit_log)
            elif op == PatchOp.REMOVE:
                cls._handle_remove(target, path, audit_log)

        return target, audit_log

    # -------------------------------------------------------------------------
    # Internal Operation Handlers
    # -------------------------------------------------------------------------

    @classmethod
    def _handle_add(cls, target: Dict[str, Any], path: Optional[str], value: Any, audit: List[str]):
        """RFC 7644 Add semantics."""
        if not path:
            if isinstance(value, dict):
                for k, v in value.items():
                    target[k] = v
                    audit.append(f"ADD attribute '{k}'")
            return

        parts = cls._split_path(path)
        current = target

        for p in parts[:-1]:
            if p not in current or not isinstance(current[p], dict):
                current[p] = {}
            current = current[p]

        leaf = parts[-1]
        if leaf in current and isinstance(current[leaf], list) and isinstance(value, (list, tuple)):
            current[leaf].extend(value)
            audit.append(f"ADD appended to list at '{path}'")
        elif leaf in current and isinstance(current[leaf], list):
            current[leaf].append(value)
            audit.append(f"ADD appended item to '{path}'")
        else:
            current[leaf] = value
            audit.append(f"ADD set value at '{path}'")

    @classmethod
    def _handle_replace(cls, target: Dict[str, Any], path: Optional[str], value: Any, audit: List[str]):
        """RFC 7644 Replace semantics."""
        if not path:
            if isinstance(value, dict):
                for k, v in value.items():
                    target[k] = v
                    audit.append(f"REPLACE root attribute '{k}'")
            return

        # Check for filtered value path e.g. emails[type eq "work"].value
        filter_match = re.match(r"^(\w+)\[(\w+)\s+eq\s+[\"']?([^\"'\]]+)[\"']?\](?:\.(\w+))?$", path)
        if filter_match:
            attr_name, filter_key, filter_val, sub_attr = filter_match.groups()
            if attr_name in target and isinstance(target[attr_name], list):
                for item in target[attr_name]:
                    if isinstance(item, dict) and item.get(filter_key) == filter_val:
                        if sub_attr:
                            item[sub_attr] = value
                        else:
                            if isinstance(value, dict):
                                item.update(value)
                            else:
                                item["value"] = value
                        audit.append(f"REPLACE filtered entry in '{attr_name}' where {filter_key}={filter_val}")
                        return
                # If not found, add it
                new_entry = {filter_key: filter_val}
                if sub_attr:
                    new_entry[sub_attr] = value
                else:
                    if isinstance(value, dict):
                        new_entry.update(value)
                    else:
                        new_entry["value"] = value
                target[attr_name].append(new_entry)
                audit.append(f"REPLACE added new entry in '{attr_name}' where {filter_key}={filter_val}")
            return

        parts = cls._split_path(path)
        current = target

        for p in parts[:-1]:
            if p not in current or not isinstance(current[p], dict):
                current[p] = {}
            current = current[p]

        leaf = parts[-1]
        current[leaf] = value
        audit.append(f"REPLACE value at '{path}'")

    @classmethod
    def _handle_remove(cls, target: Dict[str, Any], path: Optional[str], audit: List[str]):
        """RFC 7644 Remove semantics."""
        if not path:
            raise ValueError("REMOVE operation requires a 'path' attribute")

        # Check for filtered removal e.g. members[value eq "usr_123"]
        filter_match = re.match(r"^(\w+)\[(\w+)\s+eq\s+[\"']?([^\"'\]]+)[\"']?\]$", path)
        if filter_match:
            attr_name, filter_key, filter_val = filter_match.groups()
            if attr_name in target and isinstance(target[attr_name], list):
                original_len = len(target[attr_name])
                target[attr_name] = [
                    item for item in target[attr_name]
                    if not (isinstance(item, dict) and item.get(filter_key) == filter_val)
                ]
                audit.append(f"REMOVE filtered {original_len - len(target[attr_name])} entries from '{attr_name}'")
            return

        parts = cls._split_path(path)
        current = target

        for p in parts[:-1]:
            if p not in current or not isinstance(current[p], dict):
                return  # Path does not exist, no-op
            current = current[p]

        leaf = parts[-1]
        if leaf in current:
            del current[leaf]
            audit.append(f"REMOVE attribute '{path}'")

    @staticmethod
    def _split_path(path: str) -> List[str]:
        """Split dot-separated SCIM path segments."""
        return [p.strip() for p in path.split(".") if p.strip()]


class SCIMPatchBuilder:
    """Fluent Builder for constructing RFC 7644 PATCH payloads."""

    def __init__(self):
        self._ops: List[SCIMPatchOperation] = []

    def add(self, path: Optional[str], value: Any) -> "SCIMPatchBuilder":
        self._ops.append(SCIMPatchOperation(op=PatchOp.ADD, path=path, value=value))
        return self

    def replace(self, path: Optional[str], value: Any) -> "SCIMPatchBuilder":
        self._ops.append(SCIMPatchOperation(op=PatchOp.REPLACE, path=path, value=value))
        return self

    def remove(self, path: str) -> "SCIMPatchBuilder":
        self._ops.append(SCIMPatchOperation(op=PatchOp.REMOVE, path=path))
        return self

    def build_payload(self) -> Dict[str, Any]:
        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [op.to_dict() for op in self._ops],
        }

    def build_operations(self) -> List[SCIMPatchOperation]:
        return list(self._ops)
