"""
LUNARIS — Store-and-Forward Offline Resilience Queue
Requirement 6: Bus Offline & Network Failure Handling
Saves AI events locally in SQLite when backend/network is unreachable,
and safely uploads them with exponential backoff when connectivity resumes.
"""

import sqlite3
import json
import time
import urllib.request
import urllib.error
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("lunaris.ai.queue")

DB_PATH = Path(__file__).parent / "edge_queue.db"

class StoreAndForwardQueue:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT,
                    payload TEXT,
                    retry_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'PENDING',
                    created_at REAL,
                    last_attempt REAL
                )
            """)
            conn.commit()

    def enqueue(self, event_id: str, event_type: str, payload: Dict[str, Any]) -> bool:
        """Enqueue an event locally on disk."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO pending_events (id, event_type, payload, retry_count, status, created_at, last_attempt)
                    VALUES (?, ?, ?, 0, 'PENDING', ?, 0)
                """, (event_id, event_type, json.dumps(payload), time.time()))
                conn.commit()
            logger.info(f"[OFFLINE QUEUE] Stored event {event_id} locally in SQLite")
            return True
        except Exception as e:
            logger.error(f"[OFFLINE QUEUE] Failed to enqueue event: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Returns count of pending, failed, and total events."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM pending_events WHERE status = 'PENDING'")
                pending = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM pending_events WHERE status = 'FAILED'")
                failed = cursor.fetchone()[0]
                return {
                    "status": "ONLINE" if pending == 0 else "SYNCING",
                    "pending_events": pending,
                    "failed_events": failed,
                    "db_path": self.db_path
                }
        except Exception as e:
            return {"status": "ERROR", "pending_events": 0, "failed_events": 0, "error": str(e)}

    def sync_pending(self, backend_url: str, max_events: int = 10) -> int:
        """Attempt to flush pending events to the central backend API with exponential backoff."""
        flushed = 0
        now = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, payload, retry_count, last_attempt 
                FROM pending_events 
                WHERE status = 'PENDING'
                ORDER BY created_at ASC 
                LIMIT ?
            """, (max_events,))
            rows = cursor.fetchall()

            for event_id, payload_str, retries, last_attempt in rows:
                # Exponential backoff delay: 2, 4, 8, 16, 32, max 60 seconds
                backoff_wait = min(60.0, 2.0 ** retries)
                if (now - last_attempt) < backoff_wait:
                    continue

                try:
                    payload = json.loads(payload_str)
                    req = urllib.request.Request(
                        f"{backend_url.rstrip('/')}/detections/event",
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        if resp.status in (200, 201):
                            cursor.execute("DELETE FROM pending_events WHERE id = ?", (event_id,))
                            flushed += 1
                            logger.info(f"[OFFLINE QUEUE] Flushed event {event_id} to backend successfully")
                except Exception as ex:
                    new_retries = retries + 1
                    new_status = 'FAILED' if new_retries > 10 else 'PENDING'
                    cursor.execute("""
                        UPDATE pending_events 
                        SET retry_count = ?, last_attempt = ?, status = ? 
                        WHERE id = ?
                    """, (new_retries, now, new_status, event_id))
                    logger.warning(f"[OFFLINE QUEUE] Retry {new_retries} failed for {event_id}: {ex}")

            conn.commit()
        return flushed

edge_queue = StoreAndForwardQueue()
