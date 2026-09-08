"""
ElevateIQ — Multi-Region Data Residency & Sovereignty Router
=============================================================
Enforces geographic data residency constraints, cross-border media transit rules,
and sovereign edge-node selection according to tenant compliance mandates (GDPR, HIPAA, APPI, Swiss FADP).
"""

import re
import ipaddress
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger("elevateiq.services.enterprise.residency")


class SovereignRegion(str, Enum):
    """Supported sovereign data regions."""
    EU_WEST = "eu-west"        # GDPR / EU Privacy Shield (Frankfurt / Dublin)
    US_EAST = "us-east"        # HIPAA / SOC2 / FedRAMP (N. Virginia / Ohio)
    US_WEST = "us-west"        # US West / California CCPA (Oregon / N. California)
    APAC_EAST = "apac-east"    # APPI / Australia Privacy Act (Tokyo / Sydney)
    CH_CENTRAL = "ch-central"  # Swiss FADP (Zurich)
    GLOBAL_DEFAULT = "global"  # Unrestricted global routing


@dataclass
class EdgeCluster:
    """Represents a regional WebRTC SFU media and database cluster."""
    cluster_id: str
    region: SovereignRegion
    location_name: str
    is_active: bool = True
    load_factor: float = 0.0   # 0.0 to 1.0 (capacity load)
    ip_subnets: List[str] = field(default_factory=list)


@dataclass
class TenantResidencyPolicy:
    """Defines strict residency and sovereign boundary rules for a tenant."""
    tenant_id: str
    tenant_name: str
    primary_region: SovereignRegion
    allowed_regions: Set[SovereignRegion]
    strictly_enforced: bool = True
    allow_cross_border_fallback: bool = False
    anonymize_transit_metadata: bool = True
    require_e2ee_for_foreign_transit: bool = True


class DataResidencyRouter:
    """
    Enterprise Data Residency & Sovereignty Decision Engine.
    Validates data transfer boundaries, selects sovereign edge nodes,
    and enforces geofencing rules across global meeting topologies.
    """

    def __init__(self):
        self.clusters: Dict[str, EdgeCluster] = {}
        self.tenant_policies: Dict[str, TenantResidencyPolicy] = {}
        self._initialize_default_edge_clusters()

    def _initialize_default_edge_clusters(self) -> None:
        """Register default high-availability sovereign edge clusters."""
        defaults = [
            EdgeCluster("sfu-eu-de-1", SovereignRegion.EU_WEST, "Frankfurt, Germany", ip_subnets=["3.120.0.0/14"]),
            EdgeCluster("sfu-eu-ie-1", SovereignRegion.EU_WEST, "Dublin, Ireland", ip_subnets=["34.240.0.0/13"]),
            EdgeCluster("sfu-us-va-1", SovereignRegion.US_EAST, "Northern Virginia, USA", ip_subnets=["52.0.0.0/11"]),
            EdgeCluster("sfu-us-or-1", SovereignRegion.US_WEST, "Oregon, USA", ip_subnets=["54.184.0.0/13"]),
            EdgeCluster("sfu-ap-jp-1", SovereignRegion.APAC_EAST, "Tokyo, Japan", ip_subnets=["13.112.0.0/14"]),
            EdgeCluster("sfu-ap-au-1", SovereignRegion.APAC_EAST, "Sydney, Australia", ip_subnets=["13.236.0.0/14"]),
            EdgeCluster("sfu-ch-zh-1", SovereignRegion.CH_CENTRAL, "Zurich, Switzerland", ip_subnets=["18.192.0.0/14"]),
        ]
        for c in defaults:
            self.clusters[c.cluster_id] = c

    def register_tenant_policy(
        self,
        tenant_id: str,
        tenant_name: str,
        primary_region: SovereignRegion,
        allowed_regions: Optional[Set[SovereignRegion]] = None,
        strictly_enforced: bool = True,
        allow_cross_border_fallback: bool = False
    ) -> TenantResidencyPolicy:
        """Register or update a tenant's compliance residency policy."""
        allowed = allowed_regions or {primary_region}
        allowed.add(primary_region)

        policy = TenantResidencyPolicy(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            primary_region=primary_region,
            allowed_regions=allowed,
            strictly_enforced=strictly_enforced,
            allow_cross_border_fallback=allow_cross_border_fallback
        )
        self.tenant_policies[tenant_id] = policy
        log.info("DataResidencyRouter: Configured policy for %s -> Primary: %s, Allowed: %s",
                 tenant_name, primary_region.value, [r.value for r in allowed])
        return policy

    def select_optimal_cluster(
        self,
        tenant_id: str,
        preferred_region: Optional[SovereignRegion] = None
    ) -> EdgeCluster:
        """
        Select the best active edge cluster compliant with the tenant's data residency policy.
        Chooses lowest load cluster within the permissible sovereign boundaries.
        """
        policy = self.tenant_policies.get(tenant_id)
        candidate_regions: Set[SovereignRegion]

        if policy:
            if preferred_region and preferred_region in policy.allowed_regions:
                candidate_regions = {preferred_region}
            else:
                candidate_regions = policy.allowed_regions
        else:
            candidate_regions = {preferred_region} if preferred_region else set(SovereignRegion)

        # Filter clusters located in compliant candidate regions
        eligible_clusters = [
            c for c in self.clusters.values()
            if c.is_active and c.region in candidate_regions
        ]

        if not eligible_clusters:
            if policy and not policy.allow_cross_border_fallback and policy.strictly_enforced:
                raise PermissionError(
                    f"Data Sovereignty Violation: No available active edge clusters in compliant regions "
                    f"for tenant '{policy.tenant_name}' ({[r.value for r in candidate_regions]})."
                )
            # Fallback to any active cluster
            eligible_clusters = [c for c in self.clusters.values() if c.is_active]

        # Pick cluster with lowest load factor
        selected = min(eligible_clusters, key=lambda c: c.load_factor)
        log.info("DataResidencyRouter: Assigned cluster %s (%s) for tenant %s",
                 selected.cluster_id, selected.region.value, tenant_id)
        return selected

    def validate_cross_border_transfer(
        self,
        tenant_id: str,
        source_region: SovereignRegion,
        destination_region: SovereignRegion,
        is_e2ee: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate whether data or media streaming can legally flow from source to destination region.
        Returns (is_allowed: bool, reason: str).
        """
        if source_region == destination_region:
            return True, "Intra-region transfer is compliant."

        policy = self.tenant_policies.get(tenant_id)
        if not policy:
            return True, "Default unmanaged tenant permits cross-border routing."

        # Check if destination is inside allowed regions
        if destination_region not in policy.allowed_regions:
            if policy.require_e2ee_for_foreign_transit and not is_e2ee:
                return False, (
                    f"Cross-border transfer blocked: Destination '{destination_region.value}' violates "
                    f"residency policy for tenant '{policy.tenant_name}'. E2EE encryption is required."
                )
            if policy.strictly_enforced:
                return False, (
                    f"Strict data residency violation: Data flow from {source_region.value} to "
                    f"{destination_region.value} is prohibited for tenant '{policy.tenant_name}'."
                )

        return True, "Cross-border transfer authorized under tenant policy."

    def sanitize_metadata_for_transit(self, metadata: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Redact IP addresses, device identifiers, and PII from telemetry logs
        prior to cross-regional transit or foreign replica archiving.
        """
        policy = self.tenant_policies.get(tenant_id)
        if not policy or not policy.anonymize_transit_metadata:
            return metadata

        sanitized = dict(metadata)

        # Anonymize IP
        if "ip_address" in sanitized:
            raw_ip = str(sanitized["ip_address"])
            try:
                ip_obj = ipaddress.ip_address(raw_ip)
                if ip_obj.version == 4:
                    # Zero out last octet
                    parts = raw_ip.split(".")
                    sanitized["ip_address"] = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
                elif ip_obj.version == 6:
                    sanitized["ip_address"] = "xxxx:xxxx:xxxx::/48"
            except ValueError:
                sanitized["ip_address"] = "0.0.0.0"

        # Mask User Email
        if "email" in sanitized:
            email = str(sanitized["email"])
            if "@" in email:
                user_part, domain_part = email.split("@", 1)
                masked_user = user_part[0] + "***" if len(user_part) > 1 else "*"
                sanitized["email"] = f"{masked_user}@{domain_part}"

        # Strip Hardware MAC / Device Serial
        for sensitive_key in ("device_serial", "mac_address", "imei"):
            if sensitive_key in sanitized:
                sanitized[sensitive_key] = "[REDACTED_BY_SOVEREIGNTY_POLICY]"

        return sanitized
