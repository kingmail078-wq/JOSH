from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .models import Artwork, utc_now


class NotFoundError(LookupError):
    pass


class LedgerAccessError(PermissionError):
    pass


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS artworks (
  project_id TEXT NOT NULL,
  artwork_id TEXT NOT NULL,
  title TEXT NOT NULL,
  primary_lab TEXT NOT NULL,
  supporting_labs TEXT NOT NULL,
  status TEXT NOT NULL,
  current_goal TEXT NOT NULL,
  constraints TEXT NOT NULL,
  next_action TEXT NOT NULL,
  version INTEGER NOT NULL CHECK(version > 0),
  updated_at TEXT NOT NULL,
  PRIMARY KEY(project_id, artwork_id)
);
CREATE TABLE IF NOT EXISTS artwork_versions (
  project_id TEXT NOT NULL,
  artwork_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  payload TEXT NOT NULL,
  approval_id TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY(project_id, artwork_id, version)
);
CREATE TABLE IF NOT EXISTS approvals (
  approval_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  artwork_id TEXT NOT NULL,
  base_version INTEGER NOT NULL,
  proposal_hash TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','cancelled')),
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  evidence_label TEXT NOT NULL,
  content TEXT NOT NULL,
  provenance TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conflicts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  record_a TEXT NOT NULL,
  record_b TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unresolved',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
  event_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  run_id TEXT,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


class Ledger:
    def __init__(self, database: str | Path = ":memory:") -> None:
        self.database = str(database)
        self.connection = sqlite3.connect(self.database)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self.connection.execute("BEGIN")
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def close(self) -> None:
        self.connection.close()

    def _row_to_artwork(self, row: sqlite3.Row) -> Artwork:
        return Artwork(
            artwork_id=row["artwork_id"], project_id=row["project_id"], title=row["title"],
            primary_lab=row["primary_lab"], supporting_labs=json.loads(row["supporting_labs"]),
            status=row["status"], current_goal=row["current_goal"],
            constraints=json.loads(row["constraints"]), next_action=row["next_action"],
            version=row["version"], updated_at=row["updated_at"],
        )

    def lookup_artwork(self, project_id: str, artwork_id: str) -> Artwork | None:
        row = self.connection.execute(
            "SELECT * FROM artworks WHERE project_id=? AND artwork_id=?", (project_id, artwork_id)
        ).fetchone()
        return self._row_to_artwork(row) if row else None

    def get_artwork(self, project_id: str, artwork_id: str) -> Artwork:
        artwork = self.lookup_artwork(project_id, artwork_id)
        if artwork is None:
            raise NotFoundError("not_found")
        return artwork

    def get_artwork_for_project(self, authorized_project_id: str, requested_project_id: str, artwork_id: str) -> Artwork:
        if authorized_project_id != requested_project_id:
            raise LedgerAccessError("insufficient_access")
        return self.get_artwork(requested_project_id, artwork_id)

    def create_artwork(self, artwork: Artwork, run_id: str = "RUN-SEED") -> None:
        payload = artwork.payload()
        with self.transaction() as db:
            db.execute(
                "INSERT INTO artworks VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (artwork.project_id, artwork.artwork_id, artwork.title, artwork.primary_lab,
                 json.dumps(artwork.supporting_labs), artwork.status, artwork.current_goal,
                 json.dumps(artwork.constraints), artwork.next_action, artwork.version, artwork.updated_at),
            )
            db.execute(
                "INSERT INTO artwork_versions VALUES (?,?,?,?,?,?)",
                (artwork.project_id, artwork.artwork_id, artwork.version, json.dumps(payload, sort_keys=True), None, utc_now()),
            )
            self._audit(db, artwork.project_id, run_id, "artwork_created", payload)

    @staticmethod
    def proposal_hash(changes: dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(changes, sort_keys=True).encode()).hexdigest()

    def request_approval(self, approval_id: str, project_id: str, artwork_id: str, base_version: int, changes: dict[str, Any]) -> str:
        digest = self.proposal_hash(changes)
        with self.transaction() as db:
            db.execute("INSERT INTO approvals VALUES (?,?,?,?,?,?,?)",
                       (approval_id, project_id, artwork_id, base_version, digest, "pending", utc_now()))
            self._audit(db, project_id, None, "approval_requested", {"approval_id": approval_id, "proposal_hash": digest})
        return digest

    def decide_approval(self, approval_id: str, approved: bool) -> None:
        status = "approved" if approved else "rejected"
        with self.transaction() as db:
            if db.execute("UPDATE approvals SET status=? WHERE approval_id=? AND status='pending'", (status, approval_id)).rowcount != 1:
                raise NotFoundError("approval_not_found_or_not_pending")

    def commit_change(self, project_id: str, artwork_id: str, base_version: int, changes: dict[str, Any], approval_id: str, run_id: str) -> Artwork:
        approval = self.connection.execute("SELECT * FROM approvals WHERE approval_id=?", (approval_id,)).fetchone()
        if not approval or approval["status"] != "approved":
            raise LedgerAccessError("approved_proposal_required")
        if approval["project_id"] != project_id or approval["artwork_id"] != artwork_id:
            raise LedgerAccessError("approval_scope_mismatch")
        if approval["base_version"] != base_version or approval["proposal_hash"] != self.proposal_hash(changes):
            raise LedgerAccessError("approval_invalidated")
        current = self.get_artwork(project_id, artwork_id)
        if current.version != base_version:
            raise LedgerAccessError("stale_version")
        data = current.payload()
        data.update(changes)
        data["version"] = base_version + 1
        data["updated_at"] = utc_now()
        updated = Artwork(**data)
        with self.transaction() as db:
            db.execute(
                "UPDATE artworks SET title=?, primary_lab=?, supporting_labs=?, status=?, current_goal=?, constraints=?, next_action=?, version=?, updated_at=? WHERE project_id=? AND artwork_id=? AND version=?",
                (updated.title, updated.primary_lab, json.dumps(updated.supporting_labs), updated.status,
                 updated.current_goal, json.dumps(updated.constraints), updated.next_action, updated.version,
                 updated.updated_at, project_id, artwork_id, base_version),
            )
            db.execute("INSERT INTO artwork_versions VALUES (?,?,?,?,?,?)",
                       (project_id, artwork_id, updated.version, json.dumps(updated.payload(), sort_keys=True), approval_id, utc_now()))
            self._audit(db, project_id, run_id, "canonical_version_committed", {"artwork_id": artwork_id, "version": updated.version})
        return updated

    def remember(self, project_id: str, run_id: str, content: str, provenance: str, evidence_label: str = "retrieved_fact") -> None:
        with self.transaction() as db:
            db.execute("INSERT INTO memory(project_id,run_id,evidence_label,content,provenance,created_at) VALUES (?,?,?,?,?,?)",
                       (project_id, run_id, evidence_label, content, provenance, utc_now()))

    def search_memory(self, project_id: str, phrase: str) -> list[dict[str, Any]]:
        rows = self.connection.execute("SELECT * FROM memory WHERE project_id=? AND content LIKE ? ORDER BY id", (project_id, f"%{phrase}%")).fetchall()
        return [dict(r) for r in rows]

    def record_conflict(self, project_id: str, run_id: str, record_a: str, record_b: str) -> None:
        with self.transaction() as db:
            db.execute("INSERT INTO conflicts(project_id,run_id,record_a,record_b,created_at) VALUES (?,?,?,?,?)",
                       (project_id, run_id, record_a, record_b, utc_now()))

    def conflicts(self, project_id: str) -> list[tuple[str, str]]:
        return [tuple(r) for r in self.connection.execute("SELECT record_a,record_b FROM conflicts WHERE project_id=? ORDER BY id", (project_id,))]

    def audit_trace(self, project_id: str) -> list[dict[str, Any]]:
        return [dict(r) for r in self.connection.execute("SELECT * FROM audit_events WHERE project_id=? ORDER BY created_at,event_id", (project_id,))]

    def _audit(self, db: sqlite3.Connection, project_id: str, run_id: str | None, event_type: str, payload: dict[str, Any]) -> None:
        raw = f"{project_id}|{run_id}|{event_type}|{json.dumps(payload, sort_keys=True)}|{utc_now()}"
        event_id = "EVT-" + hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        db.execute("INSERT INTO audit_events VALUES (?,?,?,?,?,?)", (event_id, project_id, run_id, event_type, json.dumps(payload, sort_keys=True), utc_now()))

