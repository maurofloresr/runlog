from functools import wraps
from flask import redirect, session


from db import fetch_weekly_workouts, fetch_monthly_workouts


# ────────── # Parse form strings to int/float (returns None if invalid). ──────────────────────────────────────────────────────────
def parse_form_int(value):
    try:
        return int(value) if value else None
    except ValueError:
        return None

def parse_form_float(value):
    try:
        return float(value) if value else None
    except ValueError:
        return None
    
    
    
# TODO MEJOR EN DB???
# ── Login required ──────────────────────────────────────────────────────────
def login_required(f):
    """Igual que Finance. Redirige a /login si no hay sesión activa."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# ── Custom Zone 2 (Karvonen) ───────────────────────────────────────────────
def calculate_zone2_ceiling(hr_max, hr_rest):
    """
    Returns the Zone 2 ceiling using the Karvonen formula at 70%.
    Returns 145 as a default fallback if data is missing.
    """
    try:
        hrr = hr_max - hr_rest  # hrr = Heart Rate Reserve
        ceiling = round((hrr * 0.70) + hr_rest)
        return ceiling
    except (TypeError, ValueError):
        return 145


# ── ACWR (Acute:Chronic Workload Ratio) ──────────────────────────────────────
def calculate_acwr(user_id):
    # Calculates the Acute:Chronic Workload Ratio (ACWR)
    # Acute load  = last 7 days
    # Chronic load = last 28 days average (divided by 4)
    # If all sessions have RPE + duration: uses (duration_min * rpe) as load
    # If any session is missing RPE or duration: falls back to distance_km
    # Returns None if insufficient data (< 21 days of history or < 8 sessions in 28 days)
    # Returns None if chronic load is 0 (avoid division by zero)
    # Sweet spot: 0.8 - 1.3 | Risk zone: > 1.5

    mon_sessions  = fetch_monthly_workouts(user_id)
    week_sessions = fetch_weekly_workouts(user_id)

    if len(week_sessions) < 1 or len(mon_sessions) < 8:
        return None

    acute         = 0
    chronic_total = 0

    if all(s["rpe"] and s["duration_sec"] for s in mon_sessions):
        for s in week_sessions:
            acute += (s["duration_sec"] / 60) * s["rpe"]
        for s in mon_sessions:
            chronic_total += (s["duration_sec"] / 60) * s["rpe"]
    else:
        for s in week_sessions:
            acute += s["distance_km"]
        for s in mon_sessions:
            chronic_total += s["distance_km"]

    chronic = chronic_total / 4

    if chronic == 0:
        return None

    return round(acute / chronic, 2)
        

# ── Zone 2 % of a session ────────────────────────────────────────────────────
def get_zone2_percentage(sessions):
    """Returns the percentage of the workout spent in Zone 2."""
    if not sessions:
        return None

    min_zone2 = 0
    min_total = 0

    if all(s["zone2_minutes"] is not None and s["duration_sec"] for s in sessions):
        for session in sessions:
            min_zone2 += session["zone2_minutes"]
            min_total += session["duration_sec"] / 60

        if min_total == 0:
            return None

        return round(min_zone2 / min_total * 100, 1)

    return None
    
def get_total_km(sessions):
    
    if not sessions:
        return None
    
    km = 0
    
    for session in sessions:
        km += session["distance_km"]
    return km

# ── % candece sessions ────────────────────────────────────────────────────
def get_cadence(sessions):
    
    if not sessions:
        return None
    
    cadence = 0
    sessions_with_cadence = [s for s in sessions if s["cadence"]]
    
    if not sessions_with_cadence:
        return None

    for session in sessions_with_cadence:
        cadence += session["cadence"]
        
    return round(cadence / len(sessions_with_cadence), 0)



# ── Format seconds → "42:30" ─────────────────────────────────────────────
def format_seconds(seconds):
    """Converts integer seconds to 'HH:MM' or 'MM:SS' string format."""
    if not seconds:
        return "—"
    
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_minutes(minutes):
    """Converts integer minutes to 'HH:MM' string format."""
    if not minutes:
        return "—"
    
    minutes = int(minutes)
    h = minutes // 60
    m = minutes % 60
    
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m} min"


# ── Pace: sec/km → "5:30 /km" ───────────────────────────────────────────────
def format_pace(sec_per_km):
    """Converts seconds per kilometer into a standard pace string."""
    if not sec_per_km:
        return "—"
    
    sec_per_km = int(sec_per_km)
    m = sec_per_km // 60
    s = sec_per_km % 60
    return f"{m}:{s:02d} /km"


# ── Pain alerts ──────────────────────────────────────────────────────────────
def check_pain_alerts(pain_records):
    """
    Takes a list of dicts {'zone': str, 'date': str, 'intensity': int}.
    Returns an alert if the same zone appears 3+ times in the last 2 weeks.
    """
    from datetime import date, timedelta
    from collections import Counter

    fourteen_days_ago = str(date.today() - timedelta(days=14))
    recent_records = [p for p in pain_records if p["date"] >= fourteen_days_ago]

    zones = Counter(p["zone"] for p in recent_records)
    for zone, count in zones.items():
        if count >= 3:
            formatted_zone = zone.replace("_", " ").capitalize()
            return f"You've had {count} sessions with discomfort in {formatted_zone}. Consider taking a rest or a recovery session."
    
    return None


