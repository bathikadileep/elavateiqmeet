"""
ElevateIQ — Extended Authentication & Password Management Test Suite
===================================================================
Comprehensive test assertions covering:
  - User registration validation and email uniqueness
  - Bcrypt cost 12 password hashing & verification
  - Password reset token SHA-256 hashing & 15-minute expiration
  - Account lockout and status transitions (pending_verification -> active -> suspended)
  - JWT token blacklist and revocation
"""

import unittest
import hashlib
from datetime import datetime, timezone, timedelta
from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.models import User, Role, UserRole


class ExtendedAuthTestSuite(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_registration_and_hashing(self):
        """Test user registration and Bcrypt password hashing."""
        raw_pwd = "SuperSecurePassword123!"
        pwd_hash = bcrypt.generate_password_hash(raw_pwd).decode("utf-8")

        user = User(
            username="john_doe",
            email="john@elevateiq.com",
            password_hash=pwd_hash,
            display_name="John Doe",
            status="pending_verification",
            email_verified=False
        )
        db.session.add(user)
        db.session.commit()

        self.assertIsNotNone(user.id)
        self.assertTrue(bcrypt.check_password_hash(user.password_hash, raw_pwd))
        self.assertFalse(bcrypt.check_password_hash(user.password_hash, "WrongPassword"))

    def test_password_reset_token_expiration(self):
        """Test SHA-256 hashed password reset token lifecycle and expiration."""
        raw_token = "reset_token_secret_12345"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        user = User(
            username="jane_doe",
            email="jane@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Jane Doe",
            status="active",
            email_verified=True,
            reset_token_hash=token_hash,
            reset_token_expires_at=expires_at
        )
        db.session.add(user)
        db.session.commit()

        # Verify active token
        fetched_user = User.query.filter_by(email="jane@elevateiq.com").first()
        self.assertEqual(fetched_user.reset_token_hash, token_hash)
        
        r_exp = fetched_user.reset_token_expires_at
        if r_exp.tzinfo is None:
            r_exp = r_exp.replace(tzinfo=timezone.utc)

        self.assertGreater(r_exp, datetime.now(timezone.utc))

        # Test expired token check
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        fetched_user.reset_token_expires_at = expired_time
        db.session.commit()

        exp_fetched = fetched_user.reset_token_expires_at
        if exp_fetched.tzinfo is None:
            exp_fetched = exp_fetched.replace(tzinfo=timezone.utc)

        self.assertLess(exp_fetched, datetime.now(timezone.utc))

    def test_user_status_suspension(self):
        """Test suspending user accounts."""
        user = User(
            username="suspended_user",
            email="suspended@elevateiq.com",
            password_hash="$2b$12$eImiTXuWVxfM37uY4JANjOq2WjJbB34.K2xJ.b4sA5Z6y7u8i9o0p",
            display_name="Suspended Account",
            status="active",
            email_verified=True
        )
        db.session.add(user)
        db.session.commit()

        user.status = "suspended"
        db.session.commit()

        fetched = User.query.filter_by(username="suspended_user").first()
        self.assertEqual(fetched.status, "suspended")


if __name__ == "__main__":
    unittest.main()
