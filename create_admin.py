import sqlite3
from werkzeug.security import generate_password_hash
import time

conn = sqlite3.connect("freelancer.db")
cur = conn.cursor()

cur.execute("""
INSERT OR IGNORE INTO admin_user
(email, password_hash, role, is_enabled, created_at)
VALUES (?, ?, ?, ?, ?)
""", (
    "admin@gigbridge.com",
    generate_password_hash("admin123"),
    "ADMIN",
    1,
    int(time.time())
))

conn.commit()
conn.close()

print("✅ Admin Ready")