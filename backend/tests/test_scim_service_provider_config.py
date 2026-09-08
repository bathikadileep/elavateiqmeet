"""
ElevateIQ — Unit Test Suite for SCIM 2.0 Discovery & Schema Catalog (RFC 7643)
================================================================================
Tests ServiceProviderConfig metadata, Schemas (User, Group, EnterpriseUser),
and ResourceTypes endpoints for Okta/Azure AD compatibility.
"""

import unittest
from backend.services.enterprise.scim_service_provider_config import (
    ServiceProviderConfig,
    SCIMSchemaCatalog,
    BulkConfig,
    FilterConfig,
)


class SCIMServiceProviderConfigTestSuite(unittest.TestCase):

    def setUp(self):
        self.config = ServiceProviderConfig(
            patch_supported=True,
            bulk=BulkConfig(supported=True, max_operations=500),
            filter_config=FilterConfig(supported=True, max_results=100),
        )

    def test_service_provider_config_serialization(self):
        """Verify RFC 7643 Section 5 structure."""
        data = self.config.to_dict("https://api.elevateiq.com/scim/v2")

        self.assertIn("urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig", data["schemas"])
        self.assertTrue(data["patch"]["supported"])
        self.assertTrue(data["bulk"]["supported"])
        self.assertEqual(data["bulk"]["maxOperations"], 500)
        self.assertTrue(data["filter"]["supported"])
        self.assertEqual(data["filter"]["maxResults"], 100)
        self.assertTrue(data["sort"]["supported"])
        self.assertTrue(data["etag"]["supported"])
        self.assertFalse(data["changePassword"]["supported"])
        self.assertEqual(data["meta"]["resourceType"], "ServiceProviderConfig")

    def test_user_schema_attributes(self):
        """Verify RFC 7643 §4.1 User schema required attributes."""
        user_schema = SCIMSchemaCatalog.get_user_schema()

        self.assertEqual(user_schema["id"], SCIMSchemaCatalog.USER_SCHEMA_URN)
        attr_names = [a["name"] for a in user_schema["attributes"]]
        self.assertIn("userName", attr_names)
        self.assertIn("emails", attr_names)
        self.assertIn("name", attr_names)
        self.assertIn("roles", attr_names)

        # Check sub-attributes of name
        name_attr = next(a for a in user_schema["attributes"] if a["name"] == "name")
        sub_names = [s["name"] for s in name_attr["subAttributes"]]
        self.assertIn("givenName", sub_names)
        self.assertIn("familyName", sub_names)

    def test_group_schema_attributes(self):
        """Verify RFC 7643 §4.2 Group schema."""
        group_schema = SCIMSchemaCatalog.get_group_schema()

        self.assertEqual(group_schema["id"], SCIMSchemaCatalog.GROUP_SCHEMA_URN)
        attr_names = [a["name"] for a in group_schema["attributes"]]
        self.assertIn("displayName", attr_names)
        self.assertIn("members", attr_names)

    def test_enterprise_user_extension_schema(self):
        """Verify RFC 7643 §4.3 EnterpriseUser extension schema."""
        ext_schema = SCIMSchemaCatalog.get_enterprise_user_schema()

        self.assertEqual(ext_schema["id"], SCIMSchemaCatalog.ENTERPRISE_USER_URN)
        attr_names = [a["name"] for a in ext_schema["attributes"]]
        self.assertIn("employeeNumber", attr_names)
        self.assertIn("costCenter", attr_names)
        self.assertIn("organization", attr_names)
        self.assertIn("manager", attr_names)

    def test_list_all_schemas(self):
        """Verify listing all supported schemas response."""
        res = SCIMSchemaCatalog.list_all_schemas()

        self.assertIn("urn:ietf:params:scim:api:messages:2.0:ListResponse", res["schemas"])
        self.assertEqual(res["totalResults"], 3)
        self.assertEqual(len(res["Resources"]), 3)

    def test_list_resource_types(self):
        """Verify ResourceTypes endpoint catalog."""
        res = SCIMSchemaCatalog.list_resource_types()

        self.assertEqual(res["totalResults"], 2)
        type_ids = [t["id"] for t in res["Resources"]]
        self.assertIn("User", type_ids)
        self.assertIn("Group", type_ids)

        user_type = next(t for t in res["Resources"] if t["id"] == "User")
        self.assertEqual(user_type["endpoint"], "/Users")
        self.assertEqual(len(user_type["schemaExtensions"]), 1)


if __name__ == "__main__":
    unittest.main()
