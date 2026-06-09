-- =========================================================================
-- The Slouch Punisher - Database schema
-- Loaded automatically by the Postgres container on first start
-- (mounted into /docker-entrypoint-initdb.d/).
-- =========================================================================

-- ------------------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id           SERIAL PRIMARY KEY,
    username     VARCHAR(50)  UNIQUE NOT NULL,
    email        VARCHAR(255) UNIQUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------
-- CALIBRATIONS  (one user has many; only one is_active at a time)
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calibrations (
    id                       SERIAL PRIMARY KEY,
    user_id                  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    baseline_spine_angle     REAL,
    baseline_head_angle      REAL,
    baseline_left_pressure   REAL,
    baseline_right_pressure  REAL,
    is_active                BOOLEAN NOT NULL DEFAULT FALSE
);

-- ------------------------------------------------------------------------
-- POSTURE CLASSES  (lookup table - the 6 classes from PD01)
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posture_classes (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(50) UNIQUE NOT NULL,
    description  TEXT,
    severity     VARCHAR(10) NOT NULL CHECK (severity IN ('good','warning','bad'))
);

-- ------------------------------------------------------------------------
-- SESSIONS  (a bracketed sitting period, start/stop via button or Gradio)
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at     TIMESTAMPTZ,
    notes        TEXT
);

-- ------------------------------------------------------------------------
-- POSTURE READINGS  (one row per MediaPipe -> classifier inference)
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posture_readings (
    id                SERIAL PRIMARY KEY,
    session_id        INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    posture_class_id  INTEGER NOT NULL REFERENCES posture_classes(id),
    recorded_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence        REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    spine_angle       REAL,
    head_angle        REAL
);

-- ------------------------------------------------------------------------
-- SENSOR READINGS  (armrest + seat pressure, different cadence than ML)
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sensor_readings (
    id                      SERIAL PRIMARY KEY,
    session_id              INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    recorded_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    left_armrest_pressure   REAL,
    right_armrest_pressure  REAL,
    seat_pressure           REAL
);

-- ------------------------------------------------------------------------
-- ALERTS  (log of every buzzer/LED/speaker/OLED event)
-- ------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id                   SERIAL PRIMARY KEY,
    session_id           INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    posture_reading_id   INTEGER REFERENCES posture_readings(id) ON DELETE SET NULL,
    triggered_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alert_type           VARCHAR(20) NOT NULL CHECK (alert_type IN ('buzzer','led','speaker','oled_message')),
    duration_ms          INTEGER
);

-- ------------------------------------------------------------------------
-- Indexes for time-series queries (the Gradio dashboard will hit these)
-- ------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_posture_readings_session_time
    ON posture_readings(session_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_session_time
    ON sensor_readings(session_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_alerts_session_time
    ON alerts(session_id, triggered_at);

-- ------------------------------------------------------------------------
-- Seed the six posture classes from PD01
-- ------------------------------------------------------------------------
INSERT INTO posture_classes (name, description, severity) VALUES
    ('Perfect',         'Back is straight, head aligned with shoulders.',  'good'),
    ('Forward Slouch',  'Head leaning significantly toward the monitor.',  'bad'),
    ('Slump',           'Shoulders rounded and lowered.',                  'bad'),
    ('Side-lean Left',  'Weight shifted heavily onto the left armrest.',   'warning'),
    ('Side-lean Right', 'Weight shifted heavily onto the right armrest.',  'warning'),
    ('Not There',       'No person detected in the chair.',                'good')
ON CONFLICT (name) DO NOTHING;
