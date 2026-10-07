"""Phase 46 — fresh-database migration reliability tests.

Regression tests for the pre-existing bug where migration d36b2909d14d
unconditionally dropped the nonexistent `_alembic_tmp_attachments`
batch-operation artifact, breaking `alembic upgrade head` on a fresh DB.

Alembic commands run in a subprocess with DATABASE_URL pointed at a
temporary empty SQLite file, because env.py reads DATABASE_URL from the
cached pydantic settings singleton at import time.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"

EXPECTED_ATTACHMENTS_COLUMNS = {
    "id",
    "organization_id",
    "uploaded_by",
    "entity_type",
    "entity_id",
    "file_name",
    "file_size",
    "mime_type",
    "storage_key",
    "created_at",
}

EXPECTED_DASHBOARD_LAYOUTS_COLUMNS = {
    "id",
    "user_id",
    "organization_id",
    "layout",
    "updated_at",
}


def _run_alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _tables(db_path: Path) -> set[str]:
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        con.close()


def _columns(db_path: Path, table: str) -> set[str]:
    con = sqlite3.connect(db_path)
    try:
        return {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
    finally:
        con.close()


def _alembic_version(db_path: Path) -> str | None:
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT version_num FROM alembic_version").fetchone()
        return row[0] if row else None
    finally:
        con.close()


@pytest.fixture()
def fresh_db(tmp_path: Path) -> Path:
    db = tmp_path / "fresh_phase46.db"
    result = _run_alembic(db, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    return db


def test_fresh_db_upgrade_reaches_head(fresh_db: Path) -> None:
    """A completely empty database migrates base -> head cleanly."""
    assert _alembic_version(fresh_db) == "b2c3d4e5f6a7"
    tables = _tables(fresh_db)
    for expected in (
        "attachments",
        "dashboard_layouts",
        "releases",
        "release_approvals",
        "users",
        "organizations",
        "alembic_version",
    ):
        assert expected in tables, f"missing table {expected}"
    # The batch-mode temp-table artifact must never be created.
    assert "_alembic_tmp_attachments" not in tables


def test_attachments_schema_exists(fresh_db: Path) -> None:
    columns = _columns(fresh_db, "attachments")
    assert EXPECTED_ATTACHMENTS_COLUMNS <= columns


def test_dashboard_layout_table_exists(fresh_db: Path) -> None:
    columns = _columns(fresh_db, "dashboard_layouts")
    assert EXPECTED_DASHBOARD_LAYOUTS_COLUMNS <= columns


def test_upgrade_downgrade_upgrade_cycle(fresh_db: Path) -> None:
    """Downgrade past the fixed revision and upgrade back to head."""
    result = _run_alembic(fresh_db, "downgrade", "d4e5f6a7b8c9")
    assert result.returncode == 0, result.stderr
    assert _alembic_version(fresh_db) == "d4e5f6a7b8c9"

    result = _run_alembic(fresh_db, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    assert _alembic_version(fresh_db) == "b2c3d4e5f6a7"

    # Schema intact after the round trip.
    tables = _tables(fresh_db)
    assert "attachments" in tables
    assert "dashboard_layouts" in tables
    assert "_alembic_tmp_attachments" not in tables


def test_single_head_and_unique_revisions() -> None:
    """Migration graph has exactly one head and no duplicate revisions."""
    cfg = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"multiple heads: {heads}"
    revisions = [rev.revision for rev in script.walk_revisions()]
    assert len(revisions) == len(set(revisions)), "duplicate revision ids"
    assert "b2c3d4e5f6a7" in revisions
