"""
Tests for SCIM 2.0 Bulk Resource Processor & Transactional Rollback Engine
===========================================================================
Validates RFC 7644 bulk operations, dependency DAG sorting, bulkId reference
resolution, and compensation rollback on failure.
"""

import unittest
from backend.services.enterprise.scim_bulk_processor import (
    ScimBulkProcessor,
    ScimStorageRepository,
    SCIM_BULK_REQUEST_SCHEMA,
    SCIM_BULK_RESPONSE_SCHEMA,
    SCIM_USER_SCHEMA,
    SCIM_GROUP_SCHEMA,
)


class TestScimBulkProcessor(unittest.TestCase):

    def setUp(self):
        self.repo = ScimStorageRepository()
        self.processor = ScimBulkProcessor(repository=self.repo)

    def test_single_user_creation_bulk(self):
        payload = {
            "schemas": [SCIM_BULK_REQUEST_SCHEMA],
            "failOnErrors": 1,
            "Operations": [
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "bulk_u1",
                    "data": {
                        "userName": "alice@corp.com",
                        "name": {"formatted": "Alice Smith"},
                        "emails": [{"value": "alice@corp.com", "primary": True}],
                    },
                }
            ],
        }

        resp = self.processor.process_bulk_request(payload)
        self.assertIn(SCIM_BULK_RESPONSE_SCHEMA, resp["schemas"])
        ops = resp["Operations"]
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]["method"], "POST")
        self.assertEqual(ops[0]["status"], "201")
        self.assertEqual(ops[0]["bulkId"], "bulk_u1")

        created_id = ops[0]["response"]["id"]
        saved = self.repo.get_user(created_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["userName"], "alice@corp.com")

    def test_dependent_group_and_user_creation_with_bulk_id(self):
        # Even if Group creation appears first in the operations list,
        # the topological sorter should detect that the group depends on bulkId:user_bob,
        # and re-order user_bob to be created first!
        payload = {
            "schemas": [SCIM_BULK_REQUEST_SCHEMA],
            "failOnErrors": 1,
            "Operations": [
                {
                    "method": "POST",
                    "path": "/Groups",
                    "bulkId": "group_eng",
                    "data": {
                        "displayName": "Engineering",
                        "members": [{"value": "bulkId:user_bob", "display": "Bob Jones"}],
                    },
                },
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "user_bob",
                    "data": {
                        "userName": "bob@corp.com",
                        "name": {"formatted": "Bob Jones"},
                    },
                },
            ],
        }

        resp = self.processor.process_bulk_request(payload)
        ops = resp["Operations"]
        self.assertEqual(len(ops), 2)

        # Confirm user was created first
        self.assertEqual(ops[0]["bulkId"], "user_bob")
        self.assertEqual(ops[0]["status"], "201")
        bob_id = ops[0]["response"]["id"]

        # Confirm group was created with bob's real UUID
        self.assertEqual(ops[1]["bulkId"], "group_eng")
        self.assertEqual(ops[1]["status"], "201")
        group_id = ops[1]["response"]["id"]

        saved_group = self.repo.get_group(group_id)
        self.assertEqual(saved_group["displayName"], "Engineering")
        self.assertEqual(len(saved_group["members"]), 1)
        self.assertEqual(saved_group["members"][0]["value"], bob_id)

    def test_patch_operation_and_membership_removal(self):
        # Pre-seed user and group
        user = self.repo.save_user("usr_charlie", {"userName": "charlie@corp.com"})
        group = self.repo.save_group("grp_devops", {
            "displayName": "DevOps",
            "members": [{"value": "usr_charlie", "display": "Charlie"}],
        })

        payload = {
            "schemas": [SCIM_BULK_REQUEST_SCHEMA],
            "Operations": [
                {
                    "method": "PATCH",
                    "path": "/Groups/grp_devops",
                    "data": {
                        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
                        "Operations": [
                            {"op": "remove", "path": 'members[value eq "usr_charlie"]'},
                            {"op": "replace", "path": "displayName", "value": "Platform Engineering"},
                        ],
                    },
                }
            ],
        }

        resp = self.processor.process_bulk_request(payload)
        ops = resp["Operations"]
        self.assertEqual(ops[0]["status"], "200")

        updated_group = self.repo.get_group("grp_devops")
        self.assertEqual(updated_group["displayName"], "Platform Engineering")
        self.assertEqual(len(updated_group["members"]), 0)

    def test_fail_on_errors_rollback(self):
        # Test error threshold triggering compensation rollback
        payload = {
            "schemas": [SCIM_BULK_REQUEST_SCHEMA],
            "failOnErrors": 1,
            "Operations": [
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "user_temp",
                    "data": {"userName": "temp_user@corp.com"},
                },
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "user_invalid",
                    "data": {},  # missing userName -> triggers 400 error
                },
            ],
        }

        resp = self.processor.process_bulk_request(payload)
        ops = resp["Operations"]
        self.assertEqual(len(ops), 2)
        self.assertEqual(ops[1]["status"], "400")

        # Confirm that user_temp was rolled back (deleted) from storage!
        created_user = self.repo.find_user_by_username("temp_user@corp.com")
        self.assertIsNone(created_user, "temp_user should have been rolled back upon batch abortion")

    def test_circular_dependency_error(self):
        payload = {
            "schemas": [SCIM_BULK_REQUEST_SCHEMA],
            "Operations": [
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "node_a",
                    "data": {"userName": "a@corp.com", "manager": "bulkId:node_b"},
                },
                {
                    "method": "POST",
                    "path": "/Users",
                    "bulkId": "node_b",
                    "data": {"userName": "b@corp.com", "manager": "bulkId:node_a"},
                },
            ],
        }

        resp = self.processor.process_bulk_request(payload)
        self.assertEqual(resp.get("status"), "400")
        self.assertEqual(resp.get("scimType"), "invalidValue")
        self.assertIn("Circular bulkId dependency", resp.get("detail", ""))

    def test_missing_schema_validation(self):
        payload = {"Operations": []}
        resp = self.processor.process_bulk_request(payload)
        self.assertEqual(resp.get("status"), "400")
        self.assertEqual(resp.get("scimType"), "invalidSyntax")


if __name__ == "__main__":
    unittest.main()
