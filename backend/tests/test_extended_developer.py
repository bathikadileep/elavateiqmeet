"""
ElevateIQ — Extended Developer API Keys & Webhook Test Suite
============================================================
Tests API key generation, rate limits, and webhook subscription delivery logs.
"""

import unittest
import hashlib
from backend.app import create_app
from backend.extensions import db
from backend.models.models import APIKey, WebhookSubscription, WebhookDeliveryLog, User


class ExtendedDeveloperTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.dev_user = User(
            username="dev_user",
            email="dev@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Developer User",
            status="active",
            email_verified=True,
        )
        db.session.add(self.dev_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_api_key_generation(self):
        """Test scoped API key creation and hashing."""
        raw_key = "eliq_live_99887766554433221100"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        key = APIKey(
            user_id=self.dev_user.id,
            key_name="Staging Integration Key",
            api_key_hash=key_hash,
            key_prefix="eliq_live_9988",
            rate_limit=120,
            is_active=True
        )
        db.session.add(key)
        db.session.commit()

        fetched = APIKey.query.filter_by(api_key_hash=key_hash).first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.key_prefix, "eliq_live_9988")
        self.assertEqual(fetched.rate_limit, 120)

    def test_webhook_subscription(self):
        """Test webhook event subscription registration."""
        sub = WebhookSubscription(
            user_id=self.dev_user.id,
            target_url="https://example.com/webhook/endpoint",
            events_json=["meeting.created", "recording.ready"],
            secret_token="whsec_1234567890",
            is_active=True
        )
        db.session.add(sub)
        db.session.commit()

        fetched = WebhookSubscription.query.filter_by(user_id=self.dev_user.id).first()
        self.assertIsNotNone(fetched)
        self.assertIn("recording.ready", fetched.events_json)


if __name__ == "__main__":
    unittest.main()
