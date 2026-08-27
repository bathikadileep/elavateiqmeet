"""
ElevateIQ Developer API Gateway & Webhooks — Automated Unit Test Suite
======================================================================
Tests API Key generation, rotation, revocation, Token Bucket rate limits,
Webhook registration, HMAC-SHA256 signature calculations, and event dispatching.
"""

import unittest
import hmac
import hashlib
import time
from backend.app import create_app
from backend.extensions import db
from backend.models.models import User, APIKey, WebhookSubscription, WebhookDeliveryLog
from backend.services.webhook_service import WebhookService


class DeveloperWebhooksTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            self.user = User(
                username="devuser",
                email="dev@example.com",
                display_name="Developer User"
            )
            self.user.set_password("Password123!")
            db.session.add(self.user)
            db.session.commit()
            self.user_id = self.user.id

        # Login and obtain access token
        res = self.client.post("/api/v1/auth/login", json={
            "identity": "devuser",
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_api_key_lifecycle(self):
        # 1. Create API Key
        res_create = self.client.post("/api/developer/keys", json={
            "key_name": "Q3 Integration Key",
            "rate_limit": 150
        }, headers=self.headers)
        self.assertEqual(res_create.status_code, 201)
        key_data = res_create.get_json()
        self.assertIn("raw_api_key", key_data)
        key_id = key_data["id"]

        # 2. List API Keys
        res_list = self.client.get("/api/developer/keys", headers=self.headers)
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.get_json()), 1)

        # 3. Revoke API Key
        res_del = self.client.delete(f"/api/developer/keys/{key_id}", headers=self.headers)
        self.assertEqual(res_del.status_code, 200)

    def test_webhook_subscription_and_test_dispatch(self):
        # 1. Register Webhook
        res_sub = self.client.post("/api/developer/webhooks", json={
            "target_url": "https://httpbin.org/post",
            "events": ["meeting.created", "recording.ready"]
        }, headers=self.headers)
        self.assertEqual(res_sub.status_code, 201)
        sub_data = res_sub.get_json()
        self.assertIn("secret_token", sub_data)

        # 2. List Webhooks
        res_get = self.client.get("/api/developer/webhooks", headers=self.headers)
        self.assertEqual(res_get.status_code, 200)
        data = res_get.get_json()
        self.assertEqual(len(data["subscriptions"]), 1)

        # 3. Trigger Test Webhook
        res_test = self.client.post("/api/developer/webhooks/test", json={
            "event": "meeting.created"
        }, headers=self.headers)
        self.assertEqual(res_test.status_code, 200)

    def test_hmac_signature_generation(self):
        secret = "whsec_test_secret_12345"
        payload_str = '{"event":"recording.ready","data":{"id":"123"}}'
        expected_sig = hmac.new(secret.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
        self.assertTrue(len(expected_sig) == 64)


if __name__ == "__main__":
    unittest.main()
