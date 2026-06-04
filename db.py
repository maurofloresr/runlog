from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date, datetime, timedelta

db = SQL("sqlite:///training.db")


# -------------------------- SQL FUNCTIONS -------------------------------
def get_user_by_id(user_id):
    result = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not result:
        return None
    return result[0]

def get_user_by_username(username : str):
    result = db.execute("SELECT id, hash FROM users WHERE username = ?", username)
    if not result:
        return None
    return result[0] # result = {"id": ..., "hash": ...} or None

def create_user(username, password, age, weight, height, sex, hr_max, hr_rest, location):
    hashed = generate_password_hash(password)
    db.execute(
        """INSERT INTO users 
           (username, hash, age, weight_kg, height_cm, sex, hr_max, hr_rest, location)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        username, hashed, age, weight, height, sex, hr_max, hr_rest, location
    )
    
def get_shoe(user_id):
    return db.execute("SELECT * FROM shoes WHERE user_id = ? AND active = 1 LIMIT 1", user_id)
    
def get_pain_history(user_id):
    return db.execute(
        """SELECT pain_zones, pain_intensity, session_date 
           FROM sessions 
           WHERE user_id = ? AND pain_zones != '' AND pain_zones IS NOT NULL 
           ORDER BY session_date DESC 
           LIMIT 14""",
        user_id
    )
    
def get_user_stats(user_id):
    result = db.execute("SELECT * FROM user_stats WHERE user_id = ?", user_id)
    return result[0] if result else None

def get_total_sessions(user_id):
    result = db.execute("SELECT COUNT(*) as count FROM sessions WHERE user_id = ?", user_id)
    return result[0]["count"] if result else 0

def get_last_vo2max(user_id):
    result = db.execute(
        "SELECT vo2max FROM sessions WHERE user_id = ? AND vo2max IS NOT NULL ORDER BY session_date DESC LIMIT 1",
        user_id
    )
    return result[0]["vo2max"] if result else None

def get_total_km_stats(user_id):
    stats = get_user_stats(user_id)
    return stats["km_total"] if stats else 0
    
# -------------------------- USER FUNCTIONS -------------------------------

# check password -> if succes return id / else return False
def verify_user(username, password) -> bool:
    user = get_user_by_username(username)
    
    if user is None:
        return False
    
    if check_password_hash(user["hash"], password):
        return user["id"]
    
    # if passwor dosn't match
    return False





# -------------------------- SESSION SQL -------------------------------

def create_training_session(data: dict):
   db.execute(
    """INSERT INTO sessions 
       (user_id, session_date, distance_km, duration_sec, avg_hr, max_hr, 
        cadence, calories, zone2_minutes, vo2max, rpe, pain_zones, 
        pain_intensity, surface, notes)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",  
    data["user_id"], data["session_date"], data["distance_km"], data["duration_sec"],
    data["avg_hr"], data["max_hr"], data["cadence"], data["calories"],
    data["zone2_minutes"], data["vo2max"], data["rpe"], data["pain_zones"],
    data["pain_intensity"], data["surface"], data["notes"]
    ) 

def fetch_weekly_workouts(user_id):
    return db.execute("SELECT * FROM sessions WHERE user_id = ? and session_date >= ? ORDER BY session_date DESC", user_id, (date.today() - timedelta(days=7)))  
    
def fetch_monthly_workouts(user_id):
    return db.execute("SELECT * FROM sessions WHERE user_id = ? and session_date >= ? ORDER BY session_date DESC", user_id, (date.today() - timedelta(days=30)))  

def fetch_last_sessions(user_id, limit):
    return db.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY session_date DESC LIMIT ?", user_id, limit)  

def get_goal_km(user_id):
    result = db.execute("SELECT goal_km FROM users WHERE id = ?", user_id)  
    return result[0]["goal_km"] if result else 21

def get_max_distance(user_id):
    result = db.execute("SELECT km_max_session FROM user_stats WHERE user_id = ?", user_id)  
    return result[0]["km_max_session"] if result else 0

def get_achievements(user_id):
    return db.execute("SELECT type, unlocked_at FROM achievements WHERE user_id = ?", user_id)
    
def fetch_yearly_workouts(user_id):
    return db.execute("SELECT * FROM sessions WHERE user_id = ? AND session_date >= ? ORDER BY session_date DESC", user_id, (date.today() - timedelta(days=365)))

def db_update_user(user_id, data):
    db.execute(
        """UPDATE users SET
           age = ?, weight_kg = ?, height_cm = ?, sex = ?,
           hr_max = ?, hr_rest = ?, location = ?, goal_km = ?
           WHERE id = ?""",
        data["age"], data["weight_kg"], data["height_cm"], data["sex"],
        data["hr_max"], data["hr_rest"], data["location"], data["goal_km"],
        user_id
    )

def db_save_shoe(user_id, name, km, km_limit):
    db.execute("UPDATE shoes SET active = 0 WHERE user_id = ?", user_id)
    db.execute(
        "INSERT INTO shoes (user_id, name, km, km_limit, active) VALUES (?, ?, ?, ?, 1)",
        user_id, name, km, km_limit
    )
    
  
def update_shoe_km(user_id, km):
    db.execute(
        "UPDATE shoes SET km = km + ? WHERE user_id = ? AND active = 1",
        km, user_id
    )
# -------------------------- FUNCTIONS Updates challenges and records -------------------------------

def update_user_stats(user_id, session_data):
    existing = db.execute("SELECT * FROM user_stats WHERE user_id = ?", user_id)
    
    new_km    = session_data["distance_km"] or 0
    new_min   = (session_data["duration_sec"] or 0) // 60

    if not existing:
        db.execute(
            """INSERT INTO user_stats (user_id, km_total, km_max_session, min_total, min_max_session)
               VALUES (?, ?, ?, ?, ?)""",
            user_id, new_km, new_km, new_min, new_min
        )
    else:
        db.execute(
            """UPDATE user_stats SET
               km_total        = km_total + ?,
               km_max_session  = MAX(km_max_session, ?),
               min_total       = min_total + ?,
               min_max_session = MAX(min_max_session, ?)
               WHERE user_id = ?""",
            new_km, new_km, new_min, new_min, user_id
        )


def check_and_unlock_achievements(user_id):
    stats    = db.execute("SELECT * FROM user_stats WHERE user_id = ?", user_id)
    if not stats:
        return
    stats = stats[0]

    unlocked = {
        r["type"] for r in
        db.execute("SELECT type FROM achievements WHERE user_id = ?", user_id)
    }

    def unlock(achievement_type):
        if achievement_type not in unlocked:
            db.execute(
                "INSERT INTO achievements (user_id, type) VALUES (?, ?)",
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
    sessions_this_month = db.execute(
        "SELECT COUNT(*) as count FROM sessions WHERE user_id = ? AND session_date >= ?",
        user_id, first_of_month
    )[0]["count"]
    if sessions_this_month >= 5:  unlock("sessions_5_month")
    if sessions_this_month >= 10: unlock("sessions_10_month")

    # zone 2
    z2_sessions = db.execute(
        """SELECT COUNT(*) as count FROM sessions
           WHERE user_id = ? AND zone2_minutes IS NOT NULL AND duration_sec IS NOT NULL
           AND (zone2_minutes * 1.0 / (duration_sec / 60.0)) >= 0.9""",
        user_id
    )[0]["count"]
    if z2_sessions >= 1: unlock("zone2_perfect")

    # cadence
    max_cadence = db.execute(
        "SELECT MAX(cadence) as max FROM sessions WHERE user_id = ?", user_id
    )[0]["max"] or 0
    if max_cadence >= 165: unlock("cadence_165")