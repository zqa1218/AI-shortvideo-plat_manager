import sqlite3
from pathlib import Path

from app.paths import ROOT

DB_DIR = ROOT / "data"
DB_PATH = DB_DIR / "social.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    nickname TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    media_path TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'video',
    images TEXT NOT NULL DEFAULT '',
    platforms TEXT NOT NULL DEFAULT '',
    material_ids TEXT NOT NULL DEFAULT '',
    scheduled_at TEXT NOT NULL DEFAULT '',
    tid TEXT NOT NULL DEFAULT '249',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS task_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    work_title TEXT NOT NULL,
    plays INTEGER NOT NULL DEFAULT 0,
    likes INTEGER NOT NULL DEFAULT 0,
    comments INTEGER NOT NULL DEFAULT 0,
    favorites INTEGER NOT NULL DEFAULT 0,
    shares INTEGER NOT NULL DEFAULT 0,
    work_id TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'image',
    tags TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    md5 TEXT NOT NULL DEFAULT '',
    thumb_path TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""


def connect():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(tasks)")]
        if "kind" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN kind TEXT NOT NULL DEFAULT 'video'")
        if "images" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN images TEXT NOT NULL DEFAULT ''")
        if "platforms" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN platforms TEXT NOT NULL DEFAULT ''")
        if "material_ids" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN material_ids TEXT NOT NULL DEFAULT ''")
        if "tid" not in columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN tid TEXT NOT NULL DEFAULT '249'")
        metric_columns = [row[1] for row in conn.execute("PRAGMA table_info(metrics)")]
        if "work_id" not in metric_columns:
            conn.execute("ALTER TABLE metrics ADD COLUMN work_id TEXT NOT NULL DEFAULT ''")
        if "url" not in metric_columns:
            conn.execute("ALTER TABLE metrics ADD COLUMN url TEXT NOT NULL DEFAULT ''")


def execute(sql, params=()):
    with connect() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def query(sql, params=()):
    with connect() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
