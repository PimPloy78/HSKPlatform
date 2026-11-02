"""
Database Management & SQLite Connection Layer
Handles SQLite relational schema, connection pooling, and table creation.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Generator, Any, Dict, List, Optional

DB_FILE = Path(__file__).resolve().parent.parent / "hsk_exam.db"

def get_connection() -> sqlite3.Connection:
    """Creates a thread-safe connection to SQLite with row dictionary factory."""
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Questions Dimension Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level INTEGER NOT NULL,
            part TEXT NOT NULL,
            question TEXT NOT NULL,
            pinyin TEXT,
            translation TEXT,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 2. Exam Attempts Fact Table (Tracks individual exam sessions & performance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'guest',
            level INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            time_spent_seconds INTEGER DEFAULT 0,
            parts TEXT NOT NULL,
            answers_detail TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create indexes for analytical query acceleration
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_level ON questions (level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_part ON questions (part);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_created ON exam_attempts (created_at DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_level ON exam_attempts (level);")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_FILE)
