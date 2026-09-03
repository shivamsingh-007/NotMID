"""Migration discovery tests for the repeatable Phase 7 schema runner."""

from pathlib import Path

import pytest

from app.migrations import MigrationChecksumMismatch, discover_migrations


def test_discovers_up_migrations_in_numeric_order(tmp_path: Path) -> None:
    (tmp_path / "0002_second.up.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "0001_first.up.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "0001_first.down.sql").write_text("SELECT 0;", encoding="utf-8")

    migrations = discover_migrations(tmp_path)

    assert [migration.version for migration in migrations] == [1, 2]
    assert [migration.name for migration in migrations] == ["first", "second"]
    assert all(migration.checksum_sha256 for migration in migrations)


def test_rejects_duplicate_migration_versions(tmp_path: Path) -> None:
    (tmp_path / "0001_first.up.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "0001_duplicate.up.sql").write_text("SELECT 2;", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate migration version"):
        discover_migrations(tmp_path)


def test_checksum_mismatch_error_does_not_include_migration_sql() -> None:
    error = MigrationChecksumMismatch(1, "expected-secret", "actual-secret")

    assert "expected-secret" not in str(error)
    assert "actual-secret" not in str(error)
