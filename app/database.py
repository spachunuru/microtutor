import sqlite3
from pathlib import Path

from app.config import settings

_connection: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT 'Learner',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    settings_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    difficulty_level INTEGER DEFAULT 1,
    curriculum_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    topic TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    content_json TEXT,
    summary TEXT,
    difficulty INTEGER DEFAULT 1,
    estimated_minutes INTEGER DEFAULT 5,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT DEFAULT 'available'
);

CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    questions_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lesson_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    time_spent_seconds INTEGER
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    quiz_id INTEGER NOT NULL REFERENCES quizzes(id),
    answers_json TEXT NOT NULL,
    score REAL NOT NULL,
    xp_earned INTEGER DEFAULT 0,
    completed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS review_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    next_review_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_progress (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    total_xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_activity_date TEXT,
    lessons_completed INTEGER DEFAULT 0,
    quizzes_completed INTEGER DEFAULT 0,
    reviews_completed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    achievement_key TEXT NOT NULL,
    unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, achievement_key)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    skill_id INTEGER REFERENCES skills(id),
    lesson_id INTEGER REFERENCES lessons(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS skill_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    description_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS skill_project_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    project_id INTEGER NOT NULL REFERENCES skill_projects(id),
    submission TEXT NOT NULL,
    feedback_json TEXT,
    xp_earned INTEGER DEFAULT 0,
    passed INTEGER DEFAULT 0,
    completed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _run_migrations(db: sqlite3.Connection):
    """Add columns to existing tables without failing if they already exist."""
    migrations = [
        "ALTER TABLE skills ADD COLUMN cheatsheet TEXT",
    ]
    for sql in migrations:
        try:
            db.execute(sql)
            db.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists — idempotent


def get_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(settings.db_path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL;")
        _connection.execute("PRAGMA foreign_keys=ON;")
        _connection.executescript(SCHEMA)
        _connection.commit()
        _run_migrations(_connection)
        _ensure_default_user(_connection)
    return _connection


def _ensure_default_user(db: sqlite3.Connection):
    row = db.execute("SELECT id FROM users WHERE id = 1").fetchone()
    if row is None:
        db.execute("INSERT INTO users (name) VALUES ('Learner')")
        db.execute("INSERT INTO user_progress (user_id) VALUES (1)")
        db.commit()


def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return get_db().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return get_db().execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> int:
    cur = get_db().execute(sql, params)
    get_db().commit()
    return cur.lastrowid


def executescript(sql: str):
    get_db().executescript(sql)
