import os
from datetime import date, datetime, timedelta
from flask import Flask, session, redirect, render_template, request, flash
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from db import (
    verify_user,
    get_user_by_username,
    create_user,
    create_training_session,
    fetch_monthly_workouts,
    fetch_weekly_workouts,
    fetch_yearly_workouts,
    fetch_last_sessions,
    update_user_stats,
    check_and_unlock_achievements,
    get_goal_km,
    get_max_distance,
    get_achievements,
    get_user_by_id,
    get_shoe,
    get_pain_history,
    get_user_stats,
    get_total_sessions,
    get_last_vo2max,
    db_update_user,
    db_save_shoe,
    update_shoe_km,
    get_total_km_stats
)
from helpers import (
    parse_form_int,
    parse_form_float,
    login_required,
    calculate_acwr,
    calculate_zone2_ceiling,
    get_zone2_percentage,
    get_cadence,
    get_total_km,
    format_minutes,
    check_pain_alerts,
)


from weather import get_weather
from ai import extract_training_data

app = Flask(__name__)
csrf = CSRFProtect(app)

DEFAULT_GOAL_KM = 21


@app.context_processor
def inject_globals():
    return {
        "today": datetime.now().strftime("%d de %B, %Y"),
        "today_date": date.today().isoformat()
    }


# config session
load_dotenv()

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# call session
Session(app)

@app.route("/")
@login_required
def index():
    
    period = request.args.get("period", "month")
    user_id = session.get("user_id")

    # load user — redirect to login if session is stale
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return redirect("/login")
    
    # bring city for weather
    location = user["location"]
    weather = get_weather(location) if location else None
    
    # MAIN INFORMATION
    acwr = calculate_acwr(user_id)

    if period == "month":
        sessions = fetch_monthly_workouts(user_id)
    else:
        sessions = fetch_weekly_workouts(user_id)

    total_km   = get_total_km(sessions)
    zone_2_avg = get_zone2_percentage(sessions)
    cadence    = get_cadence(sessions)
        
    # LAST 5 SESSIONS BAR CHART
    last5_sessions = fetch_last_sessions(user_id,5)
    # char_labels takes only month and day
    char_labels = [s["session_date"].strftime("%m-%d") for s in last5_sessions]
    char_distances = [s["distance_km"] for s in last5_sessions]
    
    # PROGRESS TO GAOL 
    # TODO CHANGE GOAL TO USER SET
    goal_km = get_goal_km(user_id)
    max_distance = get_max_distance(user_id)    
    goal_progress_pct = min(round((max_distance / goal_km) * 100), 100) if goal_km else 0
    milestones = [
        {"km": 7,  "done": max_distance >= 7},
        {"km": 10, "done": max_distance >= 10},
        {"km": 15, "done": max_distance >= 15},
        {"km": 21, "done": max_distance >= 21},
    ]
    
    # LAST SESSION INFO
    last_sessions = fetch_last_sessions(user_id, 1)
    if last_sessions:
        last_session = last_sessions[0]
        last_session["duration_fmt"] = format_minutes((last_session["duration_sec"] or 0) // 60)
    else:
        last_session = None
    
    return render_template("index.html",
        acwr        = acwr,
        total_km    = total_km,
        zone_2_avg  = zone_2_avg,
        cadence     = cadence,
        chart_labels    = char_labels,
        chart_distances = char_distances,
        period      = period,
        goal_km = goal_km,
        max_distance = max_distance,
        goal_progress_pct = goal_progress_pct,
        milestones = milestones,
        last_session = last_session,
        weather = weather
    )    
    
# ENDPOINT: Extract training data from uploaded photos using AI
@csrf.exempt
@app.route("/extract", methods=["POST"])
@login_required
def extract():
    photos = request.files.getlist("photos")
    data = extract_training_data(photos)
    return data if data else {}    
    

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    
    if request.method == "POST":
        
        
         # validate date first
        session_date = request.form.get("session_date")
        
        # reject if date field is missing entirely
        if not session_date:
            flash("Invalid date", "error")
            return render_template("upload.html", today_date=date.today().isoformat())
             
        # reject if date format is invalid   
        try:
            datetime.strptime(session_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date", "error")
            return render_template("upload.html", today_date=date.today().isoformat())

        if session_date > date.today().isoformat():
            flash("Training date cannot be in the future", "error")
            return render_template("upload.html", today_date=date.today().isoformat())

        # IA PHOTOS FIELD
        photos  = request.files.getlist("photos")
        ai_data = extract_training_data(photos) if photos else None

        # helpers to combine AI + form
        def ai_or_form_float(field):
            if ai_data and ai_data.get(field):
                return ai_data.get(field)
            return parse_form_float(request.form.get(field))

        def ai_or_form_int(field):
            if ai_data and ai_data.get(field):
                return ai_data.get(field)
            return parse_form_int(request.form.get(field))
        
        # check km and time > 0
        distance = ai_or_form_float("distance_km")
        duration = (ai_or_form_int("duration_min") or 0) * 60

        if not distance or distance <= 0 or duration <= 0:
            flash("Distance and duration must be greater than 0", "error")
            return render_template("upload.html", today_date=date.today().isoformat())

        # save training info
        session_data = {
            "user_id":        session["user_id"],
            "session_date":   session_date,
            "distance_km":    distance,
            "duration_sec":   duration,
            "avg_hr":         ai_or_form_int("avg_hr"),
            "max_hr":         ai_or_form_int("max_hr"),
            "cadence":        ai_or_form_int("cadence"),
            "calories":       ai_or_form_int("calories"),
            "zone2_minutes":  ai_or_form_int("zone2_minutes"),
            "vo2max":         ai_or_form_float("vo2max"),
            "rpe":            parse_form_int(request.form.get("rpe")),
            "pain_zones":     request.form.get("pain_zones"),
            "pain_intensity": parse_form_int(request.form.get("pain_intensity")),
            "surface":        request.form.get("surface"),
            "notes":          request.form.get("notes"),
        }
        
        # save,check updates/challenges and redirect
        user_id = session["user_id"] 
        create_training_session(session_data)
        update_shoe_km(user_id, session_data["distance_km"] or 0)
        
        update_user_stats(user_id, session_data)
        check_and_unlock_achievements(user_id)
        
        
        return redirect("/history")
    
    return render_template("upload.html", today_date=date.today().isoformat())

@app.route("/history")
@login_required
def history():
    period = request.args.get("period", "month")
    user_id = session.get("user_id")

    if period == "week":
        raw = fetch_weekly_workouts(user_id)
    elif period == "year":
        raw = fetch_yearly_workouts(user_id)
    else:
        raw = fetch_monthly_workouts(user_id)

    sessions = []
    for s in raw:
        sessions.append({
            **s,
            "duration_fmt": format_minutes((s["duration_sec"] or 0) // 60),
            "zone2_pct":    get_zone2_percentage([s]) if s["zone2_minutes"] and s["duration_sec"] else None,
        })

    chart_labels = [s["session_date"].strftime("%m-%d") for s in sessions]
    hr_data      = [s["avg_hr"]    or 0 for s in sessions]
    zone2_data   = [s["zone2_pct"] or 0 for s in sessions]
    cadence_data = [s["cadence"]   or 0 for s in sessions]

    return render_template("history.html",
        sessions     = sessions,
        chart_labels = chart_labels,
        hr_data      = hr_data,
        zone2_data   = zone2_data,
        cadence_data = cadence_data,
        period       = period,
    )
    
    
@app.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")
    user          = get_user_by_id(user_id)
    
    if not user:
        session.clear()
        return redirect("/login")

    shoe_result   = get_shoe(user_id)
    shoe          = shoe_result[0] if shoe_result else None

    # zone 2 ceiling
    hr_max  = user["hr_max"]  or (220 - (user["age"] or 30))
    hr_rest = user["hr_rest"] or 60
    zone2_ceiling = calculate_zone2_ceiling(hr_max, hr_rest)

    # totals from user_stats
    total_sessions = get_total_sessions(user_id)
    vo2max         = get_last_vo2max(user_id)

    # pain history
    pain_raw = get_pain_history(user_id)
    pain_history = []
    for p in pain_raw:
        for zone in (p["pain_zones"] or "").split(","):
            if zone:
                pain_history.append({
                    "zone":       zone,
                    "intensity":  p["pain_intensity"] or 1,
                    "date":       p["session_date"],
                    "date_short": p["session_date"].strftime("%m-%d"),
                })
    pain_alert = check_pain_alerts(pain_history)

    # achievements
    unlocked = {r["type"] for r in get_achievements(user_id)}
    stats    = get_user_stats(user_id)
    max_dist = stats["km_max_session"] if stats else 0
    total_km_val = stats["km_total"] if stats else 0

    sessions_this_month = len(fetch_monthly_workouts(user_id))
    achievements = [
        {"icon": "🏃", "title": "First 7km run",        "subtitle": "Completed 7km in one session",       "unlocked": "distance_7k"  in unlocked},
        {"icon": "🔟", "title": "First 10km",            "subtitle": "Completed 10km in one session",      "unlocked": "distance_10k" in unlocked},
        {"icon": "💪", "title": "15km completed",        "subtitle": f"{round(max(15-max_dist,0),1)}km left" if max_dist < 15 else "You did it!", "unlocked": "distance_15k" in unlocked},
        {"icon": "🏅", "title": "Half marathon 21km",    "subtitle": "Final goal",                         "unlocked": "distance_21k" in unlocked},
        {"icon": "💚", "title": "100% Zone 2 session",   "subtitle": "Over 90% in aerobic zone",           "unlocked": "zone2_perfect" in unlocked},
        {"icon": "📈", "title": "Cadence ≥165 spm",      "subtitle": "Exceeded target cadence",            "unlocked": "cadence_165"  in unlocked},
        {"icon": "🔥", "title": "10 sessions in a month","subtitle": f"{sessions_this_month} this month" if sessions_this_month < 10 else "Incredible month!", "unlocked": "sessions_10_month" in unlocked},
        {"icon": "🌟", "title": "50km accumulated",      "subtitle": f"{round(max(50-total_km_val,0),1)}km left" if total_km_val < 50 else "You did it!", "unlocked": "total_50km" in unlocked},
    ]

    member_since = user["created_at"].strftime("%Y-%m") if user.get("created_at") else "—"
    
    return render_template("profile.html",
        user           = user,
        zone2_ceiling  = zone2_ceiling,
        total_km       = total_km_val,
        total_sessions = total_sessions,
        vo2max         = vo2max,
        shoe           = shoe,
        pain_history   = pain_history[:20],
        pain_alert     = pain_alert,
        achievements   = achievements,
        member_since   = member_since,
    )
    

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        
        username = request.form.get("username")
        password = request.form.get("password")
        
        # incorrect password
        user_id = verify_user(username, password)
        
        if not user_id:
            flash("Wrong username or password", "error")
            return render_template("login.html")
        
        session["user_id"] = user_id
        session["username"] = username 
        
        return redirect("/")
    
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        
        username = request.form.get("username")
        password = request.form.get("password")
        confirmed_password = request.form.get("confirmation")
        
        # check username avaiable and password => 8 char 
        # with numbers and match with confirmed password
        
        if get_user_by_username(username):
            flash("Username already taken", "error")
            return render_template("register.html")
        
        if not password or not (len(password) > 7 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
            flash("Password must be at least 8 characters long and contain both letters and numbers." , "error")
            return render_template("register.html")      
        
        if password != confirmed_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")
                
        # not essential information — convert to correct types for PostgreSQL
        age      = int(request.form.get("age"))         if request.form.get("age")       else None
        weight   = float(request.form.get("weight_kg")) if request.form.get("weight_kg") else None
        height   = float(request.form.get("height_cm")) if request.form.get("height_cm") else None
        sex      = request.form.get("sex")              or None
        hr_max   = int(request.form.get("hr_max"))      if request.form.get("hr_max")     else None
        hr_rest  = int(request.form.get("hr_rest"))     if request.form.get("hr_rest")    else None
        location = request.form.get("location", "").strip() or None
        
        create_user(username, password, age, weight, height, sex, hr_max, hr_rest, location)
        session["user_id"] = get_user_by_username(username)["id"]
        session["username"] = username 
        flash("Account created successfully", "success")
        
        
        return redirect("/")
    
    return render_template("register.html")


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)

    if request.method == "POST":
        db_update_user(user_id, {
            "age":       parse_form_int(request.form.get("age")),
            "weight_kg": parse_form_float(request.form.get("weight_kg")),
            "height_cm": parse_form_float(request.form.get("height_cm")),
            "sex":       request.form.get("sex") or None,
            "hr_max":    parse_form_int(request.form.get("hr_max")),
            "hr_rest":   parse_form_int(request.form.get("hr_rest")),
            "location":  request.form.get("location", "").strip() or None,
            "goal_km":   parse_form_int(request.form.get("goal_km")),
        })
        flash("Profile updated", "success")
        return redirect("/profile")

    return render_template("edit_profile.html", user=user)


@app.route("/profile/shoe", methods=["GET", "POST"])
@login_required
def profile_shoe():
    user_id = session.get("user_id")
    shoe_result = get_shoe(user_id)
    current = shoe_result[0] if shoe_result else None

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        km       = parse_form_float(request.form.get("km_inicial")) or 0
        km_limit = parse_form_int(request.form.get("km_limit")) or 650

        if not name:
            flash("Enter the shoe name", "error")
            return render_template("shoe.html", current=current)

        db_save_shoe(user_id, name, km, km_limit)
        flash("Shoe saved", "success")
        return redirect("/profile")

    return render_template("shoe.html", current=current)

# ENDPOINT: Real-time username availability check API
@app.route("/check-username")
def check_username():
    username = request.args.get("username", "").strip()
    exists = get_user_by_username(username)
    return {"available": exists is None}

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/login")


