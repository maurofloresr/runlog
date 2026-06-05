-- RunLog schema — PostgreSQL (Neon)

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    TEXT    NOT NULL UNIQUE,
    hash        TEXT    NOT NULL,
    age         INTEGER,
    weight_kg   REAL,
    height_cm   REAL,
    sex         TEXT,
    hr_max      INTEGER,
    hr_rest     INTEGER,
    location    TEXT,
    goal_km     INTEGER DEFAULT 21,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id             SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL,
    session_date   DATE    NOT NULL,
    distance_km    REAL,
    duration_sec   INTEGER,
    avg_hr         INTEGER,
    max_hr         INTEGER,
    cadence        INTEGER,
    calories       INTEGER,
    zone2_minutes  INTEGER,
    vo2max         REAL,
    rpe            INTEGER,
    pain_zones     TEXT,
    pain_intensity INTEGER,
    surface        TEXT,
    notes          TEXT,
    ai_feedback    TEXT,
    raw_extraction TEXT,
    uploaded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS uploads (
    id          SERIAL PRIMARY KEY,
    session_id  INTEGER NOT NULL,
    filename    TEXT    NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS shoes (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    km         REAL    DEFAULT 0,
    km_limit   INTEGER DEFAULT 650,
    active     INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_stats (
    user_id          INTEGER PRIMARY KEY,
    km_total         REAL    DEFAULT 0,
    km_max_session   REAL    DEFAULT 0,
    min_total        INTEGER DEFAULT 0,
    min_max_session  INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS achievements (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    type        TEXT    NOT NULL,
    unlocked_at DATE    DEFAULT CURRENT_DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);