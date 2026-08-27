"""
Cleanup script — drops all ElevateIQ schema objects before re-applying.
Run this ONLY if you need a fresh schema reapplication.
"""
import os, re, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
import pg8000.dbapi as pg

raw_url = os.getenv("DATABASE_URL", "")
url = raw_url
for prefix in ("postgresql+pg8000://", "postgresql://", "postgres://"):
    if url.startswith(prefix):
        url = url[len(prefix):]; break

url_no_qs = url.split("?")[0]
m = re.match(r"^(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^/:]+)(?::(?P<port>\d+))?/(?P<database>.+)$", url_no_qs)

conn = pg.connect(
    host=m.group("host"), database=m.group("database"),
    user=m.group("user"), password=m.group("password"),
    port=int(m.group("port") or 5432), ssl_context=True,
)
conn.autocommit = True
cur = conn.cursor()

DROP_SQL = """
-- Drop views
DROP VIEW IF EXISTS v_active_meetings CASCADE;
DROP VIEW IF EXISTS v_user_meeting_history CASCADE;

-- Drop tables (reverse dependency order)
DROP TABLE IF EXISTS meeting_recordings CASCADE;
DROP TABLE IF EXISTS files CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS attendance_logs CASCADE;
DROP TABLE IF EXISTS meeting_participants CASCADE;
DROP TABLE IF EXISTS meetings CASCADE;
DROP TABLE IF EXISTS user_roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS role_permissions CASCADE;
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Drop function
DROP FUNCTION IF EXISTS fn_update_timestamp CASCADE;

-- Drop ENUM types
DROP TYPE IF EXISTS recording_status CASCADE;
DROP TYPE IF EXISTS file_category CASCADE;
DROP TYPE IF EXISTS notif_type CASCADE;
DROP TYPE IF EXISTS message_type CASCADE;
DROP TYPE IF EXISTS participant_status CASCADE;
DROP TYPE IF EXISTS participant_role CASCADE;
DROP TYPE IF EXISTS meeting_type CASCADE;
DROP TYPE IF EXISTS meeting_status CASCADE;
DROP TYPE IF EXISTS user_status CASCADE;
"""

print("Dropping all ElevateIQ schema objects ...")
cur.execute(DROP_SQL)
print("[DONE] All objects dropped.")
cur.close()
conn.close()
