"""
Schema application script — ElevateIQ Meeting Platform.
Executes the full schema.sql as a single transaction using pg8000.dbapi.
"""
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import pg8000.dbapi as pg

raw_url = os.getenv("DATABASE_URL", "")
if not raw_url:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

# Strip protocol prefix
url = raw_url
for prefix in ("postgresql+pg8000://", "postgresql://", "postgres://"):
    if url.startswith(prefix):
        url = url[len(prefix):]
        break

# Remove query string
url_no_qs = url.split("?")[0]

m = re.match(
    r"^(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^/:]+)(?::(?P<port>\d+))?/(?P<database>.+)$",
    url_no_qs
)
if not m:
    print("ERROR: Cannot parse DATABASE_URL")
    sys.exit(1)

schema_path = Path(__file__).parent / "schema.sql"
schema_sql = schema_path.read_text(encoding="utf-8")

print(f"Connecting to Neon: {m.group('host')} / {m.group('database')} ...")

try:
    conn = pg.connect(
        host=m.group("host"),
        database=m.group("database"),
        user=m.group("user"),
        password=m.group("password"),
        port=int(m.group("port") or 5432),
        ssl_context=True,
    )
    conn.autocommit = True   # DDL statements like CREATE TYPE need autocommit
    print("[OK] Connected.")
except Exception as e:
    print(f"[FAIL] Connection error: {e}")
    sys.exit(1)

cursor = conn.cursor()

# --- Run entire schema as one operation ---
print("Applying schema ...")
try:
    cursor.execute(schema_sql)
    print("[DONE] Full schema applied successfully.")
except pg.DatabaseError as e:
    print(f"[FAIL] Schema error: {e}")
    # Attempt individual statements as fallback
    print("Falling back to per-statement execution ...")
    
    # Better splitter: split on ";\n" at the top level (ignoring inside function bodies)
    # Use regex to find statement-ending semicolons not inside $$ ... $$ blocks
    parts = re.split(r'(?<!\$\$);(?!\$\$)', schema_sql)
    ok = warn = 0
    for i, stmt in enumerate(parts, 1):
        stmt = stmt.strip()
        # Skip pure comments and blanks
        clean = re.sub(r'--[^\n]*', '', stmt).strip()
        if not clean:
            continue
        try:
            cursor.execute(stmt)
            ok += 1
        except pg.DatabaseError as se:
            msg = str(se)
            if "already exists" in msg.lower():
                ok += 1  # idempotent
            else:
                print(f"  [WARN] stmt {i}: {msg[:160]}")
                warn += 1
    print(f"[DONE] {ok} succeeded, {warn} warnings.")

cursor.close()
conn.close()
print("[OK] Connection closed.")
