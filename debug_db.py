from database import freelancer_db
from psycopg2.extras import RealDictCursor

def check_tables():
    conn = freelancer_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [r['table_name'] for r in cur.fetchall()]
        print(f"Tables in freelancer_db: {tables}")
        
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()['count']
            print(f"Table {table}: {count} records")
            
    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()
