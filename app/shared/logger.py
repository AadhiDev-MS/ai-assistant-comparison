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
        self._create_table()

    def _create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                model_name TEXT,
                prompt TEXT,
                response TEXT,
                latency_ms REAL,
                total_tokens INTEGER,
                cost_usd REAL
            )
        ''')
        self.conn.commit()

    def log_interaction(self, model_name, prompt, response, latency_ms, total_tokens, cost_usd):
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO logs (timestamp, model_name, prompt, response, latency_ms, total_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, model_name, prompt, response, latency_ms, total_tokens, cost_usd))
        self.conn.commit()

    def get_logs_as_list(self):
        """Returns all logs as a list of lists, perfect for a Gradio Dataframe."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT timestamp, model_name, latency_ms, total_tokens, cost_usd, prompt, response FROM logs ORDER BY id DESC')
        return cursor.fetchall()
