"""
ElevateIQ — Unit Test Suite for SCIM 2.0 PATCH Evaluator (RFC 7644)
=====================================================================
Tests RFC 7644 Add, Replace, and Remove operations against SCIM User and Group
resources, including complex filtered value paths.
"""

import unittest
from backend.services.enterprise.scim_patch_builder import (
    SCIMPatchBuilder,
    SCIMPatchEvaluator,
    SCIMPatchOperation,
    PatchOp,
)


class SCIMPatchEvaluatorTestSuite(unittest.TestCase):

    def setUp(self):
        self.sample_user = {
            "id": "usr_alpha_101",
            "userName": "jane.doe@enterprise.com",
            "name": {
                "givenName": "Jane",
                "familyName": "Doe",
            },
            "active": True,
            "emails": [
                {"type": "work", "value": "jane.doe@enterprise.com", "primary": True},
                {"type": "home", "value": "jane.personal@gmail.com", "primary": False},
            ],
            "roles": ["member"],
        }

        self.sample_group = {
            "id": "grp_eng_01",
            "displayName": "Core Engineering",
            "members": [
                {"value": "usr_001", "display": "Alice Smith"},
                {"value": "usr_002", "display": "Bob Jones"},
            ],
        }

    def test_add_operation_simple_and_list(self):
        """Test adding new attributes and appending to list."""
        builder = SCIMPatchBuilder()
        builder.add("title", "VP of Engineering")
        builder.add("roles", "admin")

        updated, audit = SCIMPatchEvaluator.apply_patch(self.sample_user, builder.build_operations())

        self.assertEqual(updated["title"], "VP of Engineering")
        self.assertIn("admin", updated["roles"])
        self.assertIn("member", updated["roles"])
        self.assertTrue(len(audit) >= 2)

    def test_replace_nested_attribute(self):
        """Test replacing sub-attribute in complex dictionary."""
        builder = SCIMPatchBuilder()
        builder.replace("name.familyName", "Doe-Smith")
        builder.replace("active", False)

        updated, audit = SCIMPatchEvaluator.apply_patch(self.sample_user, builder.build_operations())

        self.assertEqual(updated["name"]["familyName"], "Doe-Smith")
        self.assertEqual(updated["name"]["givenName"], "Jane")
        self.assertFalse(updated["active"])

    def test_replace_filtered_multivalue_attribute(self):
        """Test replacing filtered value: emails[type eq 'work'].value."""
        builder = SCIMPatchBuilder()
        builder.replace('emails[type eq "work"].value', "jane.smith@enterprise.com")

        updated, audit = SCIMPatchEvaluator.apply_patch(self.sample_user, builder.build_operations())

        work_email = next(e for e in updated["emails"] if e["type"] == "work")
        self.assertEqual(work_email["value"], "jane.smith@enterprise.com")

        # Home email untouched
        home_email = next(e for e in updated["emails"] if e["type"] == "home")
        self.assertEqual(home_email["value"], "jane.personal@gmail.com")

    def test_remove_simple_attribute(self):
        """Test removing an attribute from the resource."""
        builder = SCIMPatchBuilder()
        builder.remove("name.familyName")

        updated, audit = SCIMPatchEvaluator.apply_patch(self.sample_user, builder.build_operations())

        self.assertNotIn("familyName", updated["name"])
        self.assertIn("givenName", updated["name"])

    def test_remove_filtered_group_member(self):
        """Test removing group member via filter: members[value eq 'usr_001']."""
        builder = SCIMPatchBuilder()
        builder.remove('members[value eq "usr_001"]')

        updated, audit = SCIMPatchEvaluator.apply_patch(self.sample_group, builder.build_operations())

        self.assertEqual(len(updated["members"]), 1)
        self.assertEqual(updated["members"][0]["value"], "usr_002")

    def test_patch_payload_serialization(self):
        """Test generating RFC 7644 JSON payload."""
        builder = (
            SCIMPatchBuilder()
            .replace("active", False)
            .add("members", [{"value": "usr_003", "display": "Carol"}])
        )
        payload = builder.build_payload()

        self.assertEqual(payload["schemas"], ["urn:ietf:params:scim:api:messages:2.0:PatchOp"])
        self.assertEqual(len(payload["Operations"]), 2)
        self.assertEqual(payload["Operations"][0]["op"], "replace")
        self.assertEqual(payload["Operations"][1]["op"], "add")

    def test_invalid_operation_rejection(self):
        """Test that invalid op names raise ValueError."""
        with self.assertRaises(ValueError):
            SCIMPatchOperation.from_dict({"op": "INVALID_OP", "path": "active", "value": True})


if __name__ == "__main__":
    unittest.main()
