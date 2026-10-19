"""SQLite storage for job applications. Uses only the Python standard library."""

import csv
import sqlite3
from datetime import date

STATUSES = ["Wishlist", "Applied", "Interview", "Offer", "Rejected"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company     TEXT NOT NULL,
    role        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'Applied',
    applied_on  TEXT NOT NULL,
    follow_up   TEXT,
    link        TEXT,
    notes       TEXT
)
"""

FIELDS = ["company", "role", "status", "applied_on", "follow_up", "link", "notes"]


class Tracker:
    def __init__(self, path="applications.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(_SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def _validate(self, data):
        if not data.get("company", "").strip() or not data.get("role", "").strip():
            raise ValueError("Company and role are required.")
        if data.get("status", "Applied") not in STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")
        for key in ("applied_on", "follow_up"):
            if data.get(key):
                date.fromisoformat(data[key])  # raises ValueError if not YYYY-MM-DD

    def add(self, **data):
        data.setdefault("status", "Applied")
        data.setdefault("applied_on", date.today().isoformat())
        self._validate(data)
        values = [data.get(f) or None for f in FIELDS]
        cur = self.conn.execute(
            f"INSERT INTO applications ({', '.join(FIELDS)}) VALUES ({', '.join('?' * len(FIELDS))})",
            values,
        )
        self.conn.commit()
        return cur.lastrowid

    def update(self, app_id, **data):
        current = self.get(app_id)
        if current is None:
            raise KeyError(f"No application with id {app_id}")
        merged = {**dict(current), **data}
        self._validate(merged)
        self.conn.execute(
            f"UPDATE applications SET {', '.join(f + ' = ?' for f in FIELDS)} WHERE id = ?",
            [merged.get(f) or None for f in FIELDS] + [app_id],
        )
        self.conn.commit()

    def delete(self, app_id):
        self.conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        self.conn.commit()

    def get(self, app_id):
        return self.conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()

    def list(self, status=None, search=""):
        sql = "SELECT * FROM applications WHERE 1=1"
        params = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if search:
            sql += " AND (company LIKE ? OR role LIKE ? OR notes LIKE ?)"
            params += [f"%{search}%"] * 3
        sql += " ORDER BY applied_on DESC, id DESC"
        return self.conn.execute(sql, params).fetchall()

    def due_follow_ups(self, today=None):
        """Open applications whose follow-up date is today or earlier."""
        today = today or date.today().isoformat()
        return self.conn.execute(
            "SELECT * FROM applications WHERE follow_up IS NOT NULL AND follow_up <= ? "
            "AND status NOT IN ('Offer', 'Rejected') ORDER BY follow_up",
            (today,),
        ).fetchall()

    def stats(self):
        counts = dict.fromkeys(STATUSES, 0)
        for row in self.conn.execute(
            "SELECT status, COUNT(*) AS n FROM applications GROUP BY status"
        ):
            counts[row["status"]] = row["n"]
        return counts

    def export_csv(self, path):
        rows = self.list()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id"] + FIELDS)
            for r in rows:
                writer.writerow([r["id"]] + [r[f] or "" for f in FIELDS])
        return len(rows)
