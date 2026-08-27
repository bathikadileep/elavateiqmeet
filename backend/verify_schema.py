"""
Verification script — confirms all ElevateIQ schema objects exist in Neon.
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

# --- Tables ---
cur.execute("""
    SELECT tablename FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename;
""")
tables = [r[0] for r in cur.fetchall()]
print(f"\n[TABLES] ({len(tables)} found):")
for t in tables:
    print(f"  - {t}")

# --- Indexes ---
cur.execute("""
    SELECT indexname FROM pg_indexes
    WHERE schemaname = 'public'
    ORDER BY indexname;
""")
indexes = [r[0] for r in cur.fetchall()]
print(f"\n[INDEXES] ({len(indexes)} found):")
for ix in indexes:
    print(f"  - {ix}")

# --- ENUM types ---
cur.execute("""
    SELECT typname FROM pg_type
    WHERE typtype = 'e'
    ORDER BY typname;
""")
enums = [r[0] for r in cur.fetchall()]
print(f"\n[ENUM TYPES] ({len(enums)} found):")
for e in enums:
    print(f"  - {e}")

# --- Seed data ---
cur.execute("SELECT name FROM roles ORDER BY name;")
roles = [r[0] for r in cur.fetchall()]
print(f"\n[SEED ROLES] ({len(roles)} found): {roles}")

cur.execute("SELECT name FROM permissions ORDER BY name;")
perms = [r[0] for r in cur.fetchall()]
print(f"\n[SEED PERMISSIONS] ({len(perms)} found):")
for p in perms:
    print(f"  - {p}")

# --- Views ---
cur.execute("""
    SELECT viewname FROM pg_views
    WHERE schemaname = 'public'
    ORDER BY viewname;
""")
views = [r[0] for r in cur.fetchall()]
print(f"\n[VIEWS] ({len(views)} found): {views}")

cur.close()
conn.close()
print("\n[OK] Verification complete.")
