from database import freelancer_db
from psycopg2.extras import RealDictCursor

def check_freelancer_data(fid):
    conn = freelancer_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        tables = ['freelancer', 'freelancer_profile', 'hire_request', 'saved_client', 'freelancer_verification']
        for table in tables:
            if table == 'freelancer':
                cur.execute(f"SELECT * FROM {table} WHERE id=%s", (fid,))
            else:
                cur.execute(f"SELECT * FROM {table} WHERE freelancer_id=%s", (fid,))
            rows = cur.fetchall()
            print(f"Table {table} for freelancer {fid}: {len(rows)} records")
            for row in rows:
                print(f"  {row}")
            
    except Exception as e:
        print(f"Error checking freelancer data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_freelancer_data(1)
