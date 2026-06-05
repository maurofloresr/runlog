import os
import psycopg2
import psycopg2.extras
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    """Returns a new database connection."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def execute(query, *args):
    """
    Executes a query and returns results as a list of dicts.
    For INSERT/UPDATE/DELETE returns empty list.
    """
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, args if args else None)
            try:
                return [dict(row) for row in cur.fetchall()]
            except psycopg2.ProgrammingError:
                return []
    finally:
        conn.close()


# -------------------------- SQL FUNCTIONS -------------------------------

def get_user_by_id(user_id):
    result = execute("SELECT * FROM users WHERE id = %s", user_id)
    return result[0] if result else None

def get_user_by_username(username: str):
    result = execute("SELECT id, hash FROM users WHERE username = %s", username)
    return result[0] if result else None

def create_user(username, password, age, weight, height, sex, hr_max, hr_rest, location):
    hashed = generate_password_hash(password)
    execute(
        """INSERT INTO users 
           (username, hash, age, weight_kg, height_cm, sex, hr_max, hr_rest, location)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        username, hashed, age, weight, height, sex, hr_max, hr_rest, location
    )

def get_shoe(user_id):
    return execute("SELECT * FROM shoes WHERE user_id = %s AND active = 1 LIMIT 1", user_id)

def get_pain_history(user_id):
    return execute(
        """SELECT pain_zones, pain_intensity, session_date 
           FROM sessions 
           WHERE user_id = %s AND pain_zones != '' AND pain_zones IS NOT NULL 
           ORDER BY session_date DESC 
           LIMIT 14""",
        user_id
    )

def get_user_stats(user_id):
    result = execute("SELECT * FROM user_stats WHERE user_id = %s", user_id)
    return result[0] if result else None

def get_total_sessions(user_id):
    result = execute("SELECT COUNT(*) as count FROM sessions WHERE user_id = %s", user_id)
    return result[0]["count"] if result else 0

def get_last_vo2max(user_id):
    result = execute(
        "SELECT vo2max FROM sessions WHERE user_id = %s AND vo2max IS NOT NULL ORDER BY session_date DESC LIMIT 1",
        user_id
    )
    return result[0]["vo2max"] if result else None

def get_total_km_stats(user_id):
    stats = get_user_stats(user_id)
    return stats["km_total"] if stats else 0


# -------------------------- USER FUNCTIONS -------------------------------

def verify_user(username, password) -> bool:
    # check password — returns user id on success, False on failure
    user = get_user_by_username(username)
    if user is None:
        return False
    if check_password_hash(user["hash"], password):
        return user["id"]
    return False


# -------------------------- SESSION SQL -------------------------------

def create_training_session(data: dict):
    execute(
        """INSERT INTO sessions 
           (user_id, session_date, distance_km, duration_sec, avg_hr, max_hr, 
            cadence, calories, zone2_minutes, vo2max, rpe, pain_zones, 
            pain_intensity, surface, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        data["user_id"], data["session_date"], data["distance_km"], data["duration_sec"],
        data["avg_hr"], data["max_hr"], data["cadence"], data["calories"],
        data["zone2_minutes"], data["vo2max"], data["rpe"], data["pain_zones"],
        data["pain_intensity"], data["surface"], data["notes"]
    )

def fetch_weekly_workouts(user_id):
    return execute(
        "SELECT * FROM sessions WHERE user_id = %s AND session_date >= %s ORDER BY session_date DESC",
        user_id, (date.today() - timedelta(days=7))
    )

def fetch_monthly_workouts(user_id):
    return execute(
        "SELECT * FROM sessions WHERE user_id = %s AND session_date >= %s ORDER BY session_date DESC",
        user_id, (date.today() - timedelta(days=30))
    )

def fetch_last_sessions(user_id, limit):
    return execute(
        "SELECT * FROM sessions WHERE user_id = %s ORDER BY session_date DESC LIMIT %s",
        user_id, limit
    )

def get_goal_km(user_id):
    result = execute("SELECT goal_km FROM users WHERE id = %s", user_id)
    return result[0]["goal_km"] if result else 21

def get_max_distance(user_id):
    result = execute("SELECT km_max_session FROM user_stats WHERE user_id = %s", user_id)
    return result[0]["km_max_session"] if result else 0

def get_achievements(user_id):
    return execute("SELECT type, unlocked_at FROM achievements WHERE user_id = %s", user_id)

def fetch_yearly_workouts(user_id):
    return execute(
        "SELECT * FROM sessions WHERE user_id = %s AND session_date >= %s ORDER BY session_date DESC",
        user_id, (date.today() - timedelta(days=365))
    )

def db_update_user(user_id, data):
    execute(
        """UPDATE users SET
           age = %s, weight_kg = %s, height_cm = %s, sex = %s,
           hr_max = %s, hr_rest = %s, location = %s, goal_km = %s
           WHERE id = %s""",
        data["age"], data["weight_kg"], data["height_cm"], data["sex"],
        data["hr_max"], data["hr_rest"], data["location"], data["goal_km"],
        user_id
    )

def db_save_shoe(user_id, name, km, km_limit):
    execute("UPDATE shoes SET active = 0 WHERE user_id = %s", user_id)
    execute(
        "INSERT INTO shoes (user_id, name, km, km_limit, active) VALUES (%s, %s, %s, %s, 1)",
        user_id, name, km, km_limit
    )

def update_shoe_km(user_id, km):
    execute(
        "UPDATE shoes SET km = km + %s WHERE user_id = %s AND active = 1",
        km, user_id
    )


# -------------------------- FUNCTIONS Updates challenges and records -------------------------------

def update_user_stats(user_id, session_data):
    existing = execute("SELECT * FROM user_stats WHERE user_id = %s", user_id)

    new_km  = session_data["distance_km"] or 0
    new_min = (session_data["duration_sec"] or 0) // 60

    if not existing:
        execute(
            """INSERT INTO user_stats (user_id, km_total, km_max_session, min_total, min_max_session)
               VALUES (%s, %s, %s, %s, %s)""",
            user_id, new_km, new_km, new_min, new_min
        )
    else:
        execute(
            """UPDATE user_stats SET
               km_total        = km_total + %s,
               km_max_session  = GREATEST(km_max_session, %s),
               min_total       = min_total + %s,
               min_max_session = GREATEST(min_max_session, %s)
               WHERE user_id = %s""",
            new_km, new_km, new_min, new_min, user_id
        )


def check_and_unlock_achievements(user_id):
    stats = execute("SELECT * FROM user_stats WHERE user_id = %s", user_id)
    if not stats:
        return
    stats = stats[0]

    unlocked = {
        r["type"] for r in
        execute("SELECT type FROM achievements WHERE user_id = %s", user_id)
    }

    def unlock(achievement_type):
        if achievement_type not in unlocked:
            execute(
                "INSERT INTO achievements (user_id, type) VALUES (%s, %s)",
                user_id, achievement_type
            )

    # distance milestones
    if stats["km_max_session"] >= 7:  unlock("distance_7k")
    if stats["km_max_session"] >= 10: unlock("distance_10k")
    if stats["km_max_session"] >= 15: unlock("distance_15k")
    if stats["km_max_session"] >= 21: unlock("distance_21k")

    # accumulated km
    if stats["km_total"] >= 50:   unlock("total_50km")
    if stats["km_total"] >= 100:  unlock("total_100km")
    if stats["km_total"] >= 500:  unlock("total_500km")
    if stats["km_total"] >= 1000: unlock("total_1000km")

    # sessions this month
    first_of_month = date.today().replace(day=1).isoformat()
    result = execute(
        "SELECT COUNT(*) as count FROM sessions WHERE user_id = %s AND session_date >= %s",
        user_id, first_of_month
    )
    sessions_this_month = result[0]["count"] if result else 0
    if sessions_this_month >= 5:  unlock("sessions_5_month")
    if sessions_this_month >= 10: unlock("sessions_10_month")

    # zone 2
    z2 = execute(
        """SELECT COUNT(*) as count FROM sessions
           WHERE user_id = %s AND zone2_minutes IS NOT NULL AND duration_sec IS NOT NULL
           AND (zone2_minutes * 1.0 / (duration_sec / 60.0)) >= 0.9""",
        user_id
    )
    if z2 and z2[0]["count"] >= 1: unlock("zone2_perfect")

    # cadence
    cad = execute("SELECT MAX(cadence) as max FROM sessions WHERE user_id = %s", user_id)
    max_cadence = cad[0]["max"] if cad and cad[0]["max"] else 0
    if max_cadence >= 165: unlock("cadence_165")