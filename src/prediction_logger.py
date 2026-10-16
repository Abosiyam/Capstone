# ============================================================================
# src/prediction_logger.py – Structured JSON Logging to SQLite
# ============================================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Optional, Any
from contextlib import contextmanager

# ---------- Paths ----------
DB_PATH = Path(__file__).parent.parent / 'artifacts' / 'predictions.db'


def init_db():
    """Create the predictions table if it does not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                input_json TEXT,
                output_json TEXT,
                latency_ms REAL,
                status_code INTEGER,
                error TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON prediction_logs (timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_endpoint
            ON prediction_logs (endpoint)
        """)
        conn.commit()


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def log_request(
    endpoint: str,
    input_data: Any,
    output_data: Any = None,
    latency_ms: Optional[float] = None,
    status_code: int = 200,
    error: Optional[str] = None,
) -> int:
    """Log a request to the SQLite database."""
    init_db()

    timestamp = datetime.now(timezone.utc).isoformat()

    def safe_json(obj):
        if obj is None:
            return None
        try:
            return json.dumps(obj, default=str, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"_serialization_error": str(e)})

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO prediction_logs
                (timestamp, endpoint, input_json, output_json,
                 latency_ms, status_code, error)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            endpoint,
            safe_json(input_data),
            safe_json(output_data),
            latency_ms,
            status_code,
            error,
        ))
        conn.commit()
        return cursor.lastrowid


class Timer:
    """Context manager to measure latency in milliseconds."""

    def __init__(self):
        self.start_time = None
        self.latency_ms = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.latency_ms = (time.perf_counter() - self.start_time) * 1000
        return False


def get_stats() -> dict:
    """Return aggregate statistics from the logs."""
    init_db()
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM prediction_logs").fetchone()[0]

        avg_latency_row = conn.execute(
            "SELECT AVG(latency_ms) FROM prediction_logs WHERE latency_ms IS NOT NULL"
        ).fetchone()
        avg_latency = avg_latency_row[0] if avg_latency_row else 0

        errors = conn.execute(
            "SELECT COUNT(*) FROM prediction_logs WHERE status_code >= 400 OR error IS NOT NULL"
        ).fetchone()[0]

        by_endpoint = conn.execute("""
            SELECT endpoint, COUNT(*) as count
            FROM prediction_logs
            GROUP BY endpoint
        """).fetchall()

        recent = conn.execute("""
            SELECT timestamp, endpoint, latency_ms, status_code
            FROM prediction_logs
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

    return {
        "total_requests": total,
        "avg_latency_ms": round(avg_latency, 2) if avg_latency else 0,
        "error_count": errors,
        "by_endpoint": {row["endpoint"]: row["count"] for row in by_endpoint},
        "recent": [dict(row) for row in recent],
    }


def get_recent(limit: int = 20) -> list:
    """Return the most recent log entries."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, timestamp, endpoint, latency_ms, status_code
            FROM prediction_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    print("=" * 60)
    print("Prediction Logger – Self-Test")
    print("=" * 60)

    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM prediction_logs")
        conn.commit()

    with Timer() as t1:
        time.sleep(0.05)
    log_request("/predict", {"order_count": 5}, {"probability": 0.78}, t1.latency_ms, 200)

    with Timer() as t2:
        time.sleep(0.03)
    log_request("/recommend", {"basket": ["84997C"]}, {"n_returned": 2}, t2.latency_ms, 200)

    with Timer() as t3:
        time.sleep(0.02)
    log_request("/chat", {"question": "What is the return policy?"}, {"grounded": True}, t3.latency_ms, 200)

    log_request("/predict", {"invalid": True}, None, 12.5, 400, "Missing columns")

    stats = get_stats()
    print(f"\n📊 Stats:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Avg latency:    {stats['avg_latency_ms']} ms")
    print(f"   Errors:         {stats['error_count']}")
    print(f"   By endpoint:    {stats['by_endpoint']}")

    print(f"\n📋 Recent logs:")
    for r in get_recent(5):
        print(f"   {r['timestamp'][:19]} | {r['endpoint']} | {r['latency_ms']:.1f}ms | {r['status_code']}")

    print("\n✅ Logger self-test complete!")