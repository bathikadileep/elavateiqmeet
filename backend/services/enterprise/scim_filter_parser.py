"""
ElevateIQ — SCIM 2.0 Filter Expression Query Parser
====================================================
Parses SCIM 2.0 query filter expressions (e.g. `userName eq "john@domain.com"`) into SQL/ORM filter criteria.
"""

import re
import logging
from typing import Dict, Any, Optional

log = logging.getLogger("elevateiq.services.enterprise.scim_filter")


class SCIMFilterParser:
    """SCIM 2.0 RFC 7644 Filter Expression Parser."""

    def parse_filter_string(self, filter_expr: str) -> Dict[str, Any]:
        """Parse SCIM filter string into attribute, operator, and comparison value."""
        if not filter_expr or not filter_expr.strip():
            return {"attribute": None, "operator": None, "value": None}

        match = re.match(r'(\w+)\s+(eq|co|sw|pr|gt|ge|lt|le)\s+["\']?([^"\']+)["\']?', filter_expr.strip())
        if match:
            attr, op, val = match.groups()
            return {"attribute": attr, "operator": op, "value": val}

        return {"attribute": "userName", "operator": "eq", "value": filter_expr.strip()}
