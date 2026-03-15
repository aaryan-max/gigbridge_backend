import time
from postgres_config import get_postgres_connection, get_dict_cursor

def _parse_bool(value):
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")

def fetch_filtered_freelancers(top_rated=None, category=None, subscribed=None, verified_only=None):
    conn = get_postgres_connection()
    cur = get_dict_cursor(conn)
    sql = """
        SELECT
            f.id,
            f.name,
            COALESCE(fp.title, '') AS title,
            COALESCE(fp.skills, '') AS skills,
            COALESCE(fp.experience, 0) AS experience,
            COALESCE(fp.min_budget, 0) AS min_budget,
            COALESCE(fp.max_budget, 0) AS max_budget,
            COALESCE(fp.rating, 0) AS rating,
            COALESCE(fp.category, '') AS category,
            COALESCE(fp.bio, '') AS bio,
            COALESCE(fp.is_verified, 0) AS is_verified,
            COALESCE(fs.plan_name, 'BASIC') AS plan_name,
            COALESCE(fs.status, 'ACTIVE') AS sub_status,
            COALESCE(fs.end_date, NULL) AS sub_end
        FROM freelancer f
        LEFT JOIN freelancer_profile fp ON fp.freelancer_id = f.id
        LEFT JOIN freelancer_subscription fs ON fs.freelancer_id = fp.freelancer_id
        WHERE 1=1
    """
    params = []
    if category:
        sql += " AND LOWER(fp.category) = LOWER(%s)"
        params.append(str(category).strip())
    if _parse_bool(verified_only):
        sql += " AND COALESCE(fp.is_verified,0) = 1"
    if _parse_bool(subscribed):
        now = int(time.time())
        sql += " AND COALESCE(fs.plan_name,'BASIC') IN ('PREMIUM','PRO') AND COALESCE(fs.status,'ACTIVE')='ACTIVE' AND (fs.end_date IS NULL OR fs.end_date > %s)"
        params.append(now)
    if _parse_bool(top_rated):
        sql += " ORDER BY rating DESC, f.id DESC"
    else:
        sql += " ORDER BY f.id DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({
            "freelancer_id": r.get("id"),
            "name": r["name"],
            "title": r["title"],
            "skills": r["skills"],
            "experience": r["experience"],
            "budget_range": f"{r['min_budget']} - {r['max_budget']}",
            "rating": r["rating"],
            "category": r["category"],
            "bio": r["bio"],
            "is_verified": r["is_verified"] == 1,
            "subscription_plan": "PREMIUM" if (r["plan_name"] in ("PREMIUM","PRO")) else "BASIC"
        })
    return out
