#!/usr/bin/env python3
"""
Seed minimal test data for GigBridge CLI verification.
Ensures required tables have at least one record for all 19 feature tests.
"""
import os
import sys
import time

# Ensure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import client_db, freelancer_db
from postgres_config import get_dict_cursor

def seed():
    now = int(time.time())
    
    # Ensure client 1 and freelancer 1 exist
    cconn = client_db()
    fconn = freelancer_db()
    try:
        ccur = get_dict_cursor(cconn)
        fcur = get_dict_cursor(fconn)
        
        # Client 1 - ensure exists
        ccur.execute("SELECT id FROM client WHERE id=1")
        if not ccur.fetchone():
            try:
                ccur.execute("INSERT INTO client (name, email, password) VALUES ('Test Client', 'client1@test.com', 'xxx') RETURNING id")
                print("Created client")
            except Exception:
                pass
        
        # Freelancer 1 - ensure exists
        fcur.execute("SELECT id FROM freelancer WHERE id=1")
        if not fcur.fetchone():
            try:
                fcur.execute("INSERT INTO freelancer (name, email, password) VALUES ('Test Freelancer', 'fl1@test.com', 'xxx') RETURNING id")
                print("Created freelancer")
            except Exception:
                pass
        
        # Ensure freelancer has profile for search
        fcur.execute("SELECT freelancer_id FROM freelancer_profile WHERE freelancer_id=1")
        if not fcur.fetchone():
            fcur.execute("""
                INSERT INTO freelancer_profile (freelancer_id, title, skills, experience, min_budget, max_budget, category)
                VALUES (1, 'Photographer', 'Camera', 3, 3000, 10000, 'Photography')
                ON CONFLICT (freelancer_id) DO UPDATE SET category='Photography'
            """)
        
        # Saved freelancer (for test 6)
        try:
            fcur.execute("INSERT INTO saved_freelancer (client_id, freelancer_id) VALUES (1, 1) ON CONFLICT (client_id, freelancer_id) DO NOTHING")
            fconn.commit()
        except Exception:
            pass
        
        # Notification (for test 7) - client notifications in client db
        ccur.execute("SELECT 1 FROM notification WHERE client_id=1 LIMIT 1")
        if not ccur.fetchone():
            try:
                ccur.execute("INSERT INTO notification (client_id, message, created_at) VALUES (1, 'Test notification', %s)", (now,))
            except Exception:
                pass
        
        # Hire request (for test 9)
        fcur.execute("SELECT id FROM hire_request WHERE client_id=1 LIMIT 1")
        if not fcur.fetchone():
            fcur.execute("""
                INSERT INTO hire_request (client_id, freelancer_id, job_title, proposed_budget, note, status, created_at, contract_type)
                VALUES (1, 1, 'Test Job', 1000, 'Test', 'PENDING', %s, 'FIXED')
            """, (now,))
        
        # Project post (for tests 13, 14, 15)
        fcur.execute("SELECT id FROM project_post WHERE client_id=1 LIMIT 1")
        if not fcur.fetchone():
            fcur.execute("""
                INSERT INTO project_post (client_id, title, description, category, skills, budget_type, budget_min, budget_max, status, created_at)
                VALUES (1, 'Test Project', 'Test Desc', 'Photography', 'Camera', 'FIXED', 1000, 5000, 'OPEN', %s)
                RETURNING id
            """, (now,))
            proj = fcur.fetchone()
            if proj:
                pid = proj.get("id") or proj[0]
                # Project application
                try:
                    fcur.execute("""
                        INSERT INTO project_application (project_id, freelancer_id, proposal_text, bid_amount, status, created_at)
                        VALUES (%s, 1, 'Test proposal', 2000, 'APPLIED', %s)
                    """, (pid, now))
                except Exception:
                    pass
        
        cconn.commit()
        fconn.commit()
        print("Seed data inserted successfully")
    except Exception as e:
        print("Seed error:", e)
        cconn.rollback()
        fconn.rollback()
    finally:
        cconn.close()
        fconn.close()

if __name__ == "__main__":
    seed()
