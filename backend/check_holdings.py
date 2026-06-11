#!/usr/bin/env python3
"""One-off: print all holdings rows from the production database."""
import re
import subprocess
import sys
import time

import psycopg2

PROJECT = "stk-portfolio-assistant-498901"
PROXY_PORT = 5433

# Pull DATABASE_URL from Secret Manager
secret = subprocess.run(
    ["gcloud", "secrets", "versions", "access", "latest",
     f"--secret=DATABASE_URL", f"--project={PROJECT}"],
    capture_output=True, text=True, check=True,
).stdout.strip()

# Parse postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/<instance>
m = re.match(
    r"postgresql\+asyncpg://([^:]+):([^@]+)@/([^?]+)\?host=/cloudsql/(.+)",
    secret,
)
if not m:
    sys.exit(f"Unexpected DATABASE_URL format: {secret!r}")

db_user, db_pass, db_name, instance = m.groups()

# Start cloud-sql-proxy on a local TCP port
proxy = subprocess.Popen(
    ["cloud-sql-proxy", f"--port={PROXY_PORT}", instance],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)

try:
    # Wait for proxy to be ready (retry up to 10 s)
    conn = None
    for _ in range(10):
        try:
            conn = psycopg2.connect(
                host="127.0.0.1", port=PROXY_PORT,
                user=db_user, password=db_pass, dbname=db_name,
            )
            break
        except psycopg2.OperationalError:
            time.sleep(1)
    if conn is None:
        sys.exit("Could not connect via cloud-sql-proxy after 10 s")

    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, ticker, shares, avg_cost FROM holdings ORDER BY user_id, ticker"
    )
    rows = cur.fetchall()
    conn.close()
finally:
    proxy.terminate()
    proxy.wait()

if not rows:
    print("holdings table is empty.")
else:
    print(f"{'user_id':<40} {'ticker':<8} {'shares':<12} {'avg_cost'}")
    print("-" * 72)
    for user_id, ticker, shares, avg_cost in rows:
        print(f"{str(user_id):<40} {ticker:<8} {float(shares):<12.6g} {float(avg_cost):.2f}")
