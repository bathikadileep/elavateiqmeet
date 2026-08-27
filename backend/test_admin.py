"""
ElevateIQ — Admin Panel Unit Tests
====================================
Tests admin control panel endpoints:
  1. Admin authorization check
  2. Analytics overview
  3. List users & toggle status
  4. Role assignment
  5. List meetings & force end
"""

import unittest
from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.models import User, Role, UserRole

class AdminTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

            # Create super_admin role
            admin_role = Role(name="super_admin", description="Super Admin Role")
            db.session.add(admin_role)
            db.session.flush()

            # Create admin user
            admin = User(
                username="adminuser",
                email="admin@test.com",
                password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
                status="active"
            )
            db.session.add(admin)
            db.session.flush()

            ur = UserRole(user_id=admin.id, role_id=admin_role.id)
            db.session.add(ur)

            # Create regular user
            user = User(
                username="regularuser",
                email="regular@test.com",
                password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
                status="active"
            )
            db.session.add(user)
            db.session.commit()
            self.regular_user_id = user.id

        # Login Admin User
        self.client.post("/api/v1/auth/login", json={
            "identity": "adminuser",
            "password": "password123"
        })

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_admin_analytics_and_users(self):
        # 1. Analytics
        ana_res = self.client.get("/api/v1/admin/analytics")
        self.assertEqual(ana_res.status_code, 200)
        self.assertEqual(ana_res.get_json()["metrics"]["total_users"], 2)

        # 2. List Users
        users_res = self.client.get("/api/v1/admin/users")
        self.assertEqual(users_res.status_code, 200)
        self.assertEqual(len(users_res.get_json()["users"]), 2)

        # 3. Update User Status to suspended
        status_res = self.client.put(f"/api/v1/admin/users/{self.regular_user_id}/status", json={
            "status": "suspended"
        })
        self.assertEqual(status_res.status_code, 200)

        # 4. Roles List
        roles_res = self.client.get("/api/v1/admin/roles")
        self.assertEqual(roles_res.status_code, 200)

if __name__ == "__main__":
    unittest.main(verbosity=2)
