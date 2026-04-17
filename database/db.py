import sqlite3
import datetime
import os

DB_PATH = "equiguard.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            fairness_ratio REAL,
            compliance_pass BOOLEAN,
            top_feature TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_audit_run(fairness_ratio: float, compliance_pass: bool, top_feature: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO audit_history (timestamp, fairness_ratio, compliance_pass, top_feature)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, fairness_ratio, compliance_pass, top_feature))
    conn.commit()
    conn.close()

def get_audit_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, fairness_ratio, compliance_pass, top_feature 
        FROM audit_history 
        ORDER BY timestamp ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    # Format as list of dicts
    history = []
    for row in rows:
        history.append({
            "timestamp": row[0],
            "fairness_ratio": row[1],
            "compliance_pass": bool(row[2]),
            "top_feature": row[3]
        })
    return history

# Initialize DB when module is imported
init_db()
