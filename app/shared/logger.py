import sqlite3
import os
from datetime import datetime

class InteractionLogger:
    def __init__(self):
        """
        Initializes the SQLite database to track all model interactions, costs, and latencies.
        """
        # Store DB in the root of the project
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "interactions.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._drop_table()
        self._create_table()

    def _drop_table(self):
        cursor = self.conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS logs')
        self.conn.commit()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_name TEXT,
                user_prompt TEXT,
                model_response TEXT,
                ttft_ms REAL,
                tps REAL,
                total_tokens INTEGER,
                cost_usd REAL,
                session_id TEXT
            )
        ''')
        
        # Add session_id column if it doesn't exist (migration for existing db)
        try:
            cursor.execute("ALTER TABLE logs ADD COLUMN session_id TEXT DEFAULT 'default'")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        self.conn.commit()

    def log_interaction(self, model_name, user_prompt, model_response, ttft_ms, tps, total_tokens, cost_usd, session_id="default"):
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO logs (model_name, user_prompt, model_response, ttft_ms, tps, total_tokens, cost_usd, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (model_name, user_prompt, model_response, ttft_ms, tps, total_tokens, cost_usd, session_id))
        self.conn.commit()

    def get_logs_as_list(self, session_id="default"):
        """Returns the most recent logs as a list of lists for UI rendering."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT timestamp, model_name, ttft_ms, tps, total_tokens, cost_usd, user_prompt
            FROM logs 
            WHERE session_id = ?
            ORDER BY timestamp DESC LIMIT 50
        ''', (session_id,))
        return cursor.fetchall()
