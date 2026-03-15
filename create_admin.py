import time
from postgres_config import get_postgres_connection, get_dict_cursor
from security import generate_password_hash

conn = get_postgres_connection()
cur = get_dict_cursor(conn)

cur.execute("""
INSERT INTO admin_user
(email, password_hash, role, is_enabled, created_at)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (email) DO NOTHING
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