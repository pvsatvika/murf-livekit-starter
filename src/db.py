import sqlite3
import json
import logging

DB_FILE = "asha_memory.db"
logger = logging.getLogger("asha-db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def get_patient(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, language_preference, facts FROM patients WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "language_preference": row[1],
            "facts": json.loads(row[2]) if row[2] else {}
        }
    return None

def save_patient(user_id: str, name: str, language_preference: str, facts: dict):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO patients (user_id, name, language_preference, facts)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = CURRENT_TIMESTAMP
    """, (user_id, name, language_preference, json.dumps(facts)))
    conn.commit()
    conn.close()
    logger.info(f"Saved patient data for {user_id}")

def delete_patient(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()