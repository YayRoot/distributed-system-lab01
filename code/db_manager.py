"""
Standalone Database Manager for Calculator App
Handles all database operations and action logging
"""

import time
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager

class DatabaseManager:
    """Manages all database operations for the calculator application"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calculations.db")
        self.db_path = db_path
        self.timeout = 10.0  # 10 second timeout
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Reduce lock duration
        conn.execute("PRAGMA busy_timeout=10000")
        try:
            yield conn
            conn.commit()
        except sqlite3.OperationalError as e:
            conn.rollback()
            if "locked" in str(e):
                time.sleep(0.1)  # Brief pause before retry
            raise e
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            # Main calculation history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    expression TEXT NOT NULL,
                    result     TEXT NOT NULL,
                    timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Action log table - tracks ALL actions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS action_log (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_type TEXT NOT NULL,
                    details    TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def log_action(self, action_type: str, details: str = None,
                   ip_address: str = None, user_agent: str = None, conn=None):
        """Log any action performed in the app"""
        query = """INSERT INTO action_log (action_type, details, ip_address, user_agent)
                   VALUES (?, ?, ?, ?)"""
        params = (action_type, details, ip_address, user_agent)
        
        if conn is not None:
            conn.execute(query, params)
        else:
            with self.get_connection() as new_conn:
                new_conn.execute(query, params)

    def add_calculation(self, expression: str, result: str,
                       ip_address: str = None, user_agent: str = None) -> Dict:
        """Add a calculation to history and log the action"""
        with self.get_connection() as conn:
            # Insert calculation
            cur = conn.execute(
                "INSERT INTO history (expression, result) VALUES (?, ?)",
                (expression, result)
            )
            calc_id = cur.lastrowid

            # Log the action
            self.log_action(
                action_type="CALCULATION",
                details=f"Expression: {expression} = {result}",
                ip_address=ip_address,
                user_agent=user_agent,
                conn=conn
            )

            # Fetch the inserted record
            row = conn.execute(
                "SELECT id, expression, result, timestamp FROM history WHERE id = ?",
                (calc_id,)
            ).fetchone()

            return dict(row)

    def get_history(self, limit: int = None) -> List[Dict]:
        """Retrieve calculation history"""
        with self.get_connection() as conn:
            query = "SELECT id, expression, result, timestamp FROM history ORDER BY id DESC"
            if limit:
                query += f" LIMIT {limit}"

            rows = conn.execute(query).fetchall()

            # Log the action
            self.log_action(
                action_type="VIEW_HISTORY",
                details=f"Retrieved {len(rows)} records",
                conn=conn
            )

            return [dict(row) for row in rows]

    def clear_history(self, ip_address: str = None, user_agent: str = None):
        """Clear all calculation history"""
        with self.get_connection() as conn:
            # Count records before deletion
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]

            # Delete all records
            conn.execute("DELETE FROM history")

            # Log the action
            self.log_action(
                action_type="CLEAR_HISTORY",
                details=f"Cleared {count} records",
                ip_address=ip_address,
                user_agent=user_agent,
                conn=conn
            )

    def get_action_log(self, limit: int = 100) -> List[Dict]:
        """Retrieve action log"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT id, action_type, details, ip_address, user_agent, timestamp
                   FROM action_log ORDER BY id DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {
                "total_calculations": conn.execute("SELECT COUNT(*) FROM history").fetchone()[0],
                "total_actions": conn.execute("SELECT COUNT(*) FROM action_log").fetchone()[0],
                "last_calculation": None,
                "most_common_operation": None
            }

            # Get last calculation
            last = conn.execute(
                "SELECT expression, result, timestamp FROM history ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if last:
                stats["last_calculation"] = dict(last)

            return stats
