"""
ElevateIQ — SCIM 2.0 Discovery & Schema Configuration Service (RFC 7643 §5-§6)
================================================================================
Implements RFC 7643 standard discovery specifications:
- /ServiceProviderConfig: Server capabilities (patch, bulk, filter, sort, changePassword, etag)
- /Schemas: Core User schema (RFC 7643 §4.1), Group schema (§4.2), and Enterprise User extension (§4.3)
- /ResourceTypes: Endpoint catalog for SCIM identity clients (Okta, Azure AD, PingFederate).
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger("elevateiq.services.enterprise.scim.config")


@dataclass
class BulkConfig:
    supported: bool = True
    max_operations: int = 1000
    max_payload_size_bytes: int = 10485760  # 10 MB


@dataclass
class FilterConfig:
    supported: bool = True
    max_results: int = 200


@dataclass
class ServiceProviderConfig:
    """RFC 7643 Section 5 ServiceProviderConfig Specification."""
    patch_supported: bool = True
    bulk: BulkConfig = field(default_factory=BulkConfig)
    filter_config: FilterConfig = field(default_factory=FilterConfig)
    change_password_supported: bool = False
    sort_supported: bool = True
    etag_supported: bool = True
    authentication_schemes: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "name": "OAuth Bearer Token",
            "description": "Authentication scheme using the OAuth Bearer Token Standard",
            "specUri": "http://www.rfc-editor.org/info/rfc6750",
            "type": "oauthbearertoken",
            "primary": True,
        }
    ])

    def to_dict(self, base_url: str = "https://meet.elevateiq.com/api/v1/scim/v2") -> Dict[str, Any]:
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
            "documentationUri": "https://docs.elevateiq.com/api/scim",
            "patch": {"supported": self.patch_supported},
            "bulk": {
                "supported": self.bulk.supported,
                "maxOperations": self.bulk.max_operations,
                "maxPayloadSize": self.bulk.max_payload_size_bytes,
            },
            "filter": {
                "supported": self.filter_config.supported,
                "maxResults": self.filter_config.max_results,
            },
            "changePassword": {"supported": self.change_password_supported},
            "sort": {"supported": self.sort_supported},
            "etag": {"supported": self.etag_supported},
            "authenticationSchemes": self.authentication_schemes,
            "meta": {
                "location": f"{base_url}/ServiceProviderConfig",
                "resourceType": "ServiceProviderConfig",
                "created": "2026-01-01T00:00:00Z",
                "lastModified": "2026-01-01T00:00:00Z",
            },
        }


class SCIMSchemaCatalog:
    """RFC 7643 Section 6 Schemas & ResourceTypes Registry."""

    USER_SCHEMA_URN = "urn:ietf:params:scim:schemas:core:2.0:User"
    GROUP_SCHEMA_URN = "urn:ietf:params:scim:schemas:core:2.0:Group"
    ENTERPRISE_USER_URN = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"

    @classmethod
    def get_user_schema(cls) -> Dict[str, Any]:
        """RFC 7643 §4.1 Core User Schema Definition."""
        return {
            "id": cls.USER_SCHEMA_URN,
            "name": "User",
            "description": "ElevateIQ Enterprise Core User Account",
            "attributes": [
                {"name": "userName", "type": "string", "multiValued": False, "required": True, "caseExact": False, "mutability": "readWrite", "returned": "default", "uniqueness": "server"},
                {"name": "name", "type": "complex", "multiValued": False, "required": False, "subAttributes": [
                    {"name": "formatted", "type": "string", "multiValued": False, "mutability": "readWrite"},
                    {"name": "familyName", "type": "string", "multiValued": False, "mutability": "readWrite"},
                    {"name": "givenName", "type": "string", "multiValued": False, "mutability": "readWrite"},
                ]},
                {"name": "displayName", "type": "string", "multiValued": False, "required": False, "mutability": "readWrite"},
                {"name": "active", "type": "boolean", "multiValued": False, "required": False, "mutability": "readWrite"},
                {"name": "emails", "type": "complex", "multiValued": True, "required": True, "subAttributes": [
                    {"name": "value", "type": "string", "multiValued": False, "required": True},
                    {"name": "type", "type": "string", "multiValued": False},
                    {"name": "primary", "type": "boolean", "multiValued": False},
                ]},
                {"name": "roles", "type": "complex", "multiValued": True, "required": False, "subAttributes": [
                    {"name": "value", "type": "string", "multiValued": False},
                    {"name": "display", "type": "string", "multiValued": False},
                ]},
            ],
            "meta": {"resourceType": "Schema", "location": f"/Schemas/{cls.USER_SCHEMA_URN}"},
        }

    @classmethod
    def get_group_schema(cls) -> Dict[str, Any]:
        """RFC 7643 §4.2 Group Schema Definition."""
        return {
            "id": cls.GROUP_SCHEMA_URN,
            "name": "Group",
            "description": "ElevateIQ User Role and Team Group Resource",
            "attributes": [
                {"name": "displayName", "type": "string", "multiValued": False, "required": True, "mutability": "readWrite"},
                {"name": "members", "type": "complex", "multiValued": True, "required": False, "mutability": "readWrite", "subAttributes": [
                    {"name": "value", "type": "string", "multiValued": False, "required": True, "mutability": "immutable"},
                    {"name": "$ref", "type": "reference", "multiValued": False, "referenceTypes": ["User", "Group"]},
                    {"name": "display", "type": "string", "multiValued": False},
                ]},
            ],
            "meta": {"resourceType": "Schema", "location": f"/Schemas/{cls.GROUP_SCHEMA_URN}"},
        }

    @classmethod
    def get_enterprise_user_schema(cls) -> Dict[str, Any]:
        """RFC 7643 §4.3 Enterprise User Extension Schema."""
        return {
            "id": cls.ENTERPRISE_USER_URN,
            "name": "EnterpriseUser",
            "description": "ElevateIQ Enterprise Organization Extension",
            "attributes": [
                {"name": "employeeNumber", "type": "string", "multiValued": False, "mutability": "readWrite"},
                {"name": "costCenter", "type": "string", "multiValued": False, "mutability": "readWrite"},
                {"name": "organization", "type": "string", "multiValued": False, "mutability": "readWrite"},
                {"name": "division", "type": "string", "multiValued": False, "mutability": "readWrite"},
                {"name": "department", "type": "string", "multiValued": False, "mutability": "readWrite"},
                {"name": "manager", "type": "complex", "multiValued": False, "subAttributes": [
                    {"name": "value", "type": "string", "multiValued": False},
                    {"name": "$ref", "type": "reference", "referenceTypes": ["User"]},
                    {"name": "displayName", "type": "string", "multiValued": False},
                ]},
            ],
            "meta": {"resourceType": "Schema", "location": f"/Schemas/{cls.ENTERPRISE_USER_URN}"},
        }

    @classmethod
    def list_all_schemas(cls) -> Dict[str, Any]:
        schemas = [cls.get_user_schema(), cls.get_group_schema(), cls.get_enterprise_user_schema()]
        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(schemas),
            "startIndex": 1,
            "itemsPerPage": len(schemas),
            "Resources": schemas,
        }

    @classmethod
    def list_resource_types(cls, base_url: str = "https://meet.elevateiq.com/api/v1/scim/v2") -> Dict[str, Any]:
        """RFC 7643 §6 ResourceTypes endpoint response."""
        types = [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "User",
                "name": "User",
                "endpoint": "/Users",
                "description": "User Account Resource",
                "schema": cls.USER_SCHEMA_URN,
                "schemaExtensions": [{"schema": cls.ENTERPRISE_USER_URN, "required": False}],
                "meta": {"location": f"{base_url}/ResourceTypes/User", "resourceType": "ResourceType"},
            },
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "id": "Group",
                "name": "Group",
                "endpoint": "/Groups",
                "description": "Group Resource",
                "schema": cls.GROUP_SCHEMA_URN,
                "meta": {"location": f"{base_url}/ResourceTypes/Group", "resourceType": "ResourceType"},
            },
        ]
        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(types),
            "startIndex": 1,
            "itemsPerPage": len(types),
            "Resources": types,
        }
