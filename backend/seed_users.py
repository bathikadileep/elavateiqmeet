"""
ElevateIQ — Database Seed Script
=================================
Seeds standard enterprise test users into Neon PostgreSQL:
  1. Username: admin      | Password: Password123! | Role: super_admin
  2. Username: hostuser   | Password: Password123! | Role: host
  3. Username: user1      | Password: Password123! | Role: participant
"""

import os
import sys

_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

import logging
from backend.app import create_app
from backend.extensions import db, bcrypt
from backend.models.models import User, Role, UserRole

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("elevateiq.seed")

app = create_app("development")

def seed():
    with app.app_context():
        log.info("Ensuring default roles exist...")

        roles_def = [
            ("super_admin", "Super Administrator with full platform permissions"),
            ("host", "Meeting host capable of scheduling and managing rooms"),
            ("participant", "Standard meeting participant"),
        ]

        roles_map = {}
        for role_name, desc in roles_def:
            r = db.session.execute(
                db.select(Role).filter_by(name=role_name)
            ).scalar_one_or_none()

            if not r:
                r = Role(name=role_name, description=desc, is_system=True)
                db.session.add(r)
                db.session.flush()
                log.info("Created role: %s", role_name)
            roles_map[role_name] = r

        db.session.commit()

        users_def = [
            ("admin", "admin@elevateiq.com", "Password123!", "ElevateIQ Admin", "super_admin"),
            ("hostuser", "host@elevateiq.com", "Password123!", "Sarah Host", "host"),
            ("user1", "user1@elevateiq.com", "Password123!", "Alex Participant", "participant"),
            ("user2", "user2@elevateiq.com", "Password123!", "David Miller", "participant"),
            ("user3", "user3@elevateiq.com", "Password123!", "Emma Watson", "participant"),
            ("user4", "user4@elevateiq.com", "Password123!", "James Wilson", "participant"),
            ("user5", "user5@elevateiq.com", "Password123!", "Sophia Chen", "participant"),
            ("user6", "user6@elevateiq.com", "Password123!", "Liam Johnson", "participant"),
            ("user7", "user7@elevateiq.com", "Password123!", "Olivia Garcia", "participant"),
            ("user8", "user8@elevateiq.com", "Password123!", "Noah Martinez", "participant"),
            ("user9", "user9@elevateiq.com", "Password123!", "Ava Robinson", "participant"),
            ("user10", "user10@elevateiq.com", "Password123!", "Lucas Taylor", "participant"),
        ]

        for username, email, raw_pwd, display_name, role_key in users_def:
            u = db.session.execute(
                db.select(User).filter_by(username=username)
            ).scalar_one_or_none()

            if not u:
                pwd_hash = bcrypt.generate_password_hash(raw_pwd).decode("utf-8")
                u = User(
                    username=username,
                    email=email,
                    password_hash=pwd_hash,
                    display_name=display_name,
                    status="active",
                    email_verified=True,
                )
                db.session.add(u)
                db.session.flush()

                # Assign role
                ur = UserRole(user_id=u.id, role_id=roles_map[role_key].id)
                db.session.add(ur)
                log.info("Seeded user '%s' (%s) with role '%s'", username, email, role_key)
            else:
                # Reset password to Password123!
                u.password_hash = bcrypt.generate_password_hash(raw_pwd).decode("utf-8")
                u.status = "active"
                log.info("Updated existing user '%s' password.", username)

        db.session.commit()
        log.info("[OK] Database seeding complete!")

if __name__ == "__main__":
    seed()
