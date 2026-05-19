# -*- coding: utf-8 -*-
"""SQLite data access for the standalone knowledge governance console."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "config.yaml"
DEFAULT_DATA_DIR = "data"
DEFAULT_DB_FILE = "knowledge_base.db"
LOCAL_TZ = timezone(timedelta(hours=8))

KNOWLEDGE_COLUMNS = {
    "kid",
    "title",
    "content",
    "type",
    "creator",
    "owner",
    "approver",
    "effective_date",
    "expiry_date",
    "source",
    "confidence",
    "version",
    "scope",
    "status",
    "created_at",
    "updated_at",
    "changelog",
}
BADCASE_COLUMNS = {
    "kid",
    "description",
    "severity",
    "source",
    "reporter",
    "status",
    "reviewer_note",
    "created_at",
    "resolved_at",
}


def now_iso() -> str:
    return datetime.now(LOCAL_TZ).isoformat(timespec="seconds")


def _read_simple_yaml(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    if not path.exists():
        return config
    try:
        with path.open("r", encoding="utf-8") as file_obj:
            for raw_line in file_obj:
                line = raw_line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, value = line.split(":", 1)
                config[key.strip()] = value.strip().strip("\"'")
    except OSError as exc:
        LOGGER.warning("Unable to read config file %s: %s", path, exc)
    return config


def load_config() -> dict[str, str]:
    config = {
        "data_dir": DEFAULT_DATA_DIR,
        "database_file": DEFAULT_DB_FILE,
        "pending_verify_threshold": "0",
    }
    config.update({key: value for key, value in _read_simple_yaml(Path(DEFAULT_CONFIG_FILE)).items() if value})
    return config


def get_database_path() -> Path:
    config = load_config()
    data_dir = Path(config.get("data_dir", DEFAULT_DATA_DIR))
    database_file = config.get("database_file", DEFAULT_DB_FILE)
    return data_dir / database_file


def _connect() -> sqlite3.Connection:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [_normalize_knowledge_row(dict(row)) for row in rows]


def _normalize_knowledge_row(row: dict[str, Any]) -> dict[str, Any]:
    changelog = _parse_json_list(row.get("changelog"))
    normalized = dict(row)
    normalized["knowledge_id"] = normalized.get("kid", "")
    normalized["knowledge_type"] = normalized.get("type", "")
    normalized["trust_rating"] = normalized.get("confidence", "")
    normalized["modification_logs"] = changelog
    return normalized


def _normalize_badcase_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["badcase_id"] = f"BC-{normalized.get('id')}"
    normalized["related_knowledge_id"] = normalized.get("kid", "")
    normalized["error_level"] = normalized.get("severity", "")
    normalized["discovery_source"] = normalized.get("source", "")
    normalized["reject_reason"] = normalized.get("reviewer_note", "")
    normalized["submitted_at"] = normalized.get("created_at", "")
    normalized["reviewed_at"] = normalized.get("resolved_at", "")
    normalized["reviewer"] = normalized.get("reviewer_note", "")
    return normalized


def _parse_json_list(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    try:
        data = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _increment_version(version: str) -> str:
    try:
        return f"{float(version) + 0.1:.1f}"
    except (TypeError, ValueError):
        return "1.1"


def _build_changelog_entry(summary: str, modifier: str = "系统", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "modified_at": now_iso(),
        "modifier": modifier.strip() or "系统",
        "summary": summary,
    }
    if extra:
        entry.update(extra)
    return entry


def init_db() -> None:
    """Create SQLite tables and seed the example knowledge unit and reference."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_units (
                kid TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                creator TEXT,
                owner TEXT,
                approver TEXT,
                effective_date TEXT,
                expiry_date TEXT,
                source TEXT,
                confidence TEXT,
                version TEXT,
                scope TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                changelog TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS badcase_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kid TEXT,
                description TEXT NOT NULL,
                severity TEXT,
                source TEXT,
                reporter TEXT,
                status TEXT,
                reviewer_note TEXT,
                created_at TEXT,
                resolved_at TEXT,
                FOREIGN KEY (kid) REFERENCES knowledge_units(kid)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reference_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kid TEXT NOT NULL,
                referenced_at TEXT NOT NULL,
                report_id TEXT,
                source TEXT,
                FOREIGN KEY (kid) REFERENCES knowledge_units(kid)
            )
            """
        )
        _seed_example(connection)


def _seed_example(connection: sqlite3.Connection) -> None:
    existing = connection.execute(
        "SELECT 1 FROM knowledge_units WHERE kid = ?",
        ("KID-20260518-001",),
    ).fetchone()
    if existing:
        return
    connection.execute(
        """
        INSERT INTO knowledge_units (
            kid, title, content, type, creator, owner, approver, effective_date,
            expiry_date, source, confidence, version, scope, status, created_at,
            updated_at, changelog
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "KID-20260518-001",
            "示例：日本市场付费意愿更多与CV相关",
            "根据历史版本数据和社区反馈分析，日本市场玩家付费意愿与角色CV（声优）的关联度显著高于其他市场。当新角色由高人气CV配音时，日服流水通常出现明显上涨。",
            "经验总结",
            "示例运营人员",
            "示例运营人员",
            "示例管理者",
            "2026-05-18",
            "",
            "内部运营专家经验",
            "高置信度经多方验证",
            "1.0",
            "市场运营Agent、竞品雷达模块、日服分析",
            "生效中",
            "2026-05-18T00:00:00+08:00",
            "2026-05-18T00:00:00+08:00",
            "[]",
        ),
    )
    connection.execute(
        """
        INSERT INTO reference_log (kid, referenced_at, report_id, source)
        VALUES (?, ?, ?, ?)
        """,
        ("KID-20260518-001", "2026-05-18T00:00:00+08:00", "DEMO-REPORT-001", "手动测试"),
    )


def generate_kid() -> str:
    today = datetime.now(LOCAL_TZ).strftime("%Y%m%d")
    prefix = f"KID-{today}-"
    with _connect() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM knowledge_units WHERE kid LIKE ?",
            (f"{prefix}%",),
        ).fetchone()["count"]
    return f"{prefix}{count + 1:03d}"


def insert_knowledge(data: dict[str, Any]) -> None:
    item = {
        "kid": data.get("kid") or data.get("knowledge_id") or generate_kid(),
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "type": data.get("type") or data.get("knowledge_type", ""),
        "creator": data.get("creator", ""),
        "owner": data.get("owner", ""),
        "approver": data.get("approver", ""),
        "effective_date": data.get("effective_date", ""),
        "expiry_date": data.get("expiry_date", ""),
        "source": data.get("source", ""),
        "confidence": data.get("confidence") or data.get("trust_rating", ""),
        "version": data.get("version", "1.0"),
        "scope": data.get("scope", ""),
        "status": data.get("status", "生效中"),
        "created_at": data.get("created_at", now_iso()),
        "updated_at": data.get("updated_at", now_iso()),
        "changelog": json.dumps(data.get("changelog") or data.get("modification_logs") or [], ensure_ascii=False),
    }
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO knowledge_units (
                kid, title, content, type, creator, owner, approver, effective_date,
                expiry_date, source, confidence, version, scope, status, created_at,
                updated_at, changelog
            ) VALUES (
                :kid, :title, :content, :type, :creator, :owner, :approver, :effective_date,
                :expiry_date, :source, :confidence, :version, :scope, :status, :created_at,
                :updated_at, :changelog
            )
            """,
            item,
        )


def get_all_knowledge(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    clauses: list[str] = []
    params: list[Any] = []
    for key in ("status", "type", "confidence", "owner"):
        value = filters.get(key)
        if value:
            clauses.append(f"{key} = ?")
            params.append(value)
    expiry_date = filters.get("expiry_date")
    if expiry_date:
        operator = filters.get("expiry_operator", "<=")
        if operator not in {"<", "<=", "=", ">=", ">"}:
            operator = "<="
        clauses.append(f"expiry_date != '' AND expiry_date {operator} ?")
        params.append(expiry_date)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sort_by = filters.get("sort_by", "updated_at")
    if sort_by not in KNOWLEDGE_COLUMNS:
        sort_by = "updated_at"
    sort_order = str(filters.get("sort_order", "DESC")).upper()
    if sort_order not in {"ASC", "DESC"}:
        sort_order = "DESC"
    with _connect() as connection:
        rows = connection.execute(
            f"SELECT * FROM knowledge_units {where_sql} ORDER BY {sort_by} {sort_order}",
            params,
        ).fetchall()
    return _rows_to_dicts(rows)


def get_knowledge_by_kid(kid: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute("SELECT * FROM knowledge_units WHERE kid = ?", (kid,)).fetchone()
        if not row:
            return None
        item = _normalize_knowledge_row(dict(row))
        item["recent_references"] = get_recent_references(kid)
        return item


def update_knowledge(kid: str, updates: dict[str, Any]) -> None:
    allowed_updates = {key: value for key, value in updates.items() if key in KNOWLEDGE_COLUMNS - {"kid", "created_at", "changelog"}}
    modifier = str(updates.get("modifier", "系统"))
    summary = str(updates.get("changelog_summary") or "更新知识字段")
    with _connect() as connection:
        row = connection.execute("SELECT * FROM knowledge_units WHERE kid = ?", (kid,)).fetchone()
        if not row:
            raise ValueError(f"Knowledge unit not found: {kid}")
        current = dict(row)
        changelog = _parse_json_list(current.get("changelog"))
        changelog.append(
            _build_changelog_entry(
                summary,
                modifier,
                {"changed_fields": sorted(allowed_updates.keys())},
            )
        )
        allowed_updates["version"] = _increment_version(str(current.get("version", "1.0")))
        allowed_updates["updated_at"] = now_iso()
        allowed_updates["changelog"] = json.dumps(changelog, ensure_ascii=False)
        set_sql = ", ".join(f"{key} = ?" for key in allowed_updates)
        connection.execute(
            f"UPDATE knowledge_units SET {set_sql} WHERE kid = ?",
            [*allowed_updates.values(), kid],
        )


def mark_deprecated(kid: str) -> None:
    with _connect() as connection:
        row = connection.execute("SELECT changelog FROM knowledge_units WHERE kid = ?", (kid,)).fetchone()
        if not row:
            raise ValueError(f"Knowledge unit not found: {kid}")
        changelog = _parse_json_list(row["changelog"])
        changelog.append(_build_changelog_entry("知识状态标记为已作废", "系统"))
        connection.execute(
            """
            UPDATE knowledge_units
            SET status = ?, updated_at = ?, changelog = ?
            WHERE kid = ?
            """,
            ("已作废", now_iso(), json.dumps(changelog, ensure_ascii=False), kid),
        )


def get_dashboard_stats() -> dict[str, int]:
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=30)).isoformat()
    stale_day = (date.today() - timedelta(days=30)).isoformat()
    week_ago = (datetime.now(LOCAL_TZ) - timedelta(days=7)).isoformat(timespec="seconds")
    with _connect() as connection:
        total = connection.execute("SELECT COUNT(*) AS count FROM knowledge_units").fetchone()["count"]
        expired = connection.execute(
            "SELECT COUNT(*) AS count FROM knowledge_units WHERE expiry_date != '' AND expiry_date < ? AND status != ?",
            (today, "已作废"),
        ).fetchone()["count"]
        expiring_soon = connection.execute(
            """
            SELECT COUNT(*) AS count FROM knowledge_units
            WHERE expiry_date != '' AND expiry_date >= ? AND expiry_date <= ? AND status != ?
            """,
            (today, soon, "已作废"),
        ).fetchone()["count"]
        owner_missing = connection.execute(
            "SELECT COUNT(*) AS count FROM knowledge_units WHERE TRIM(COALESCE(owner, '')) = '' OR owner = ?",
            ("未指定",),
        ).fetchone()["count"]
        pending_verify = connection.execute(
            """
            SELECT COUNT(*) AS count FROM knowledge_units
            WHERE confidence = ? AND effective_date <= ?
            """,
            ("低置信度待验证", stale_day),
        ).fetchone()["count"]
        recent_new = connection.execute(
            "SELECT COUNT(*) AS count FROM knowledge_units WHERE created_at >= ?",
            (week_ago,),
        ).fetchone()["count"]
    return {
        "total": int(total),
        "expired": int(expired),
        "expiring_soon": int(expiring_soon),
        "owner_missing": int(owner_missing),
        "pending_verify": int(pending_verify),
        "recent_new": int(recent_new),
    }


def get_alert_list() -> dict[str, list[dict[str, Any]]]:
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=30)).isoformat()
    stale_day = (date.today() - timedelta(days=30)).isoformat()
    with _connect() as connection:
        expired = connection.execute(
            "SELECT * FROM knowledge_units WHERE expiry_date != '' AND expiry_date < ? AND status != ? ORDER BY expiry_date ASC",
            (today, "已作废"),
        ).fetchall()
        owner_missing = connection.execute(
            "SELECT * FROM knowledge_units WHERE TRIM(COALESCE(owner, '')) = '' OR owner = ? ORDER BY updated_at DESC",
            ("未指定",),
        ).fetchall()
        expiring_soon = connection.execute(
            """
            SELECT * FROM knowledge_units
            WHERE expiry_date != '' AND expiry_date >= ? AND expiry_date <= ? AND status != ?
            ORDER BY expiry_date ASC
            """,
            (today, soon, "已作废"),
        ).fetchall()
        pending_verify = connection.execute(
            """
            SELECT * FROM knowledge_units
            WHERE confidence = ? AND effective_date <= ?
            ORDER BY effective_date ASC
            """,
            ("低置信度待验证", stale_day),
        ).fetchall()
    return {
        "expired": _rows_to_dicts(expired),
        "owner_missing": _rows_to_dicts(owner_missing),
        "expiring_soon": _rows_to_dicts(expiring_soon),
        "pending_verify": _rows_to_dicts(pending_verify),
    }


def insert_badcase(data: dict[str, Any]) -> None:
    item = {
        "kid": data.get("kid") or data.get("related_knowledge_id", ""),
        "description": data.get("description", ""),
        "severity": data.get("severity") or data.get("error_level", ""),
        "source": data.get("source") or data.get("discovery_source", ""),
        "reporter": data.get("reporter", ""),
        "status": data.get("status", "待审核"),
        "reviewer_note": data.get("reviewer_note", ""),
        "created_at": data.get("created_at", now_iso()),
        "resolved_at": data.get("resolved_at", ""),
    }
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO badcase_log (
                kid, description, severity, source, reporter, status,
                reviewer_note, created_at, resolved_at
            ) VALUES (
                :kid, :description, :severity, :source, :reporter, :status,
                :reviewer_note, :created_at, :resolved_at
            )
            """,
            item,
        )


def get_badcase_list(status_filter: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM badcase_log"
    params: list[Any] = []
    if status_filter:
        sql += " WHERE status = ?"
        params.append(status_filter)
    sql += " ORDER BY created_at DESC, id DESC"
    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_normalize_badcase_row(dict(row)) for row in rows]


def update_badcase(id: int, updates: dict[str, Any]) -> None:
    allowed_updates = {key: value for key, value in updates.items() if key in BADCASE_COLUMNS - {"created_at"}}
    if not allowed_updates:
        return
    set_sql = ", ".join(f"{key} = ?" for key in allowed_updates)
    with _connect() as connection:
        connection.execute(
            f"UPDATE badcase_log SET {set_sql} WHERE id = ?",
            [*allowed_updates.values(), id],
        )


def get_badcase_stats() -> dict[str, Any]:
    with _connect() as connection:
        pending_count = connection.execute(
            "SELECT COUNT(*) AS count FROM badcase_log WHERE status = ?",
            ("待审核",),
        ).fetchone()["count"]
        severity_rows = connection.execute(
            "SELECT severity, COUNT(*) AS count FROM badcase_log GROUP BY severity ORDER BY count DESC"
        ).fetchall()
        knowledge_rows = connection.execute(
            "SELECT kid, COUNT(*) AS count FROM badcase_log GROUP BY kid ORDER BY count DESC"
        ).fetchall()
    return {
        "pending_count": int(pending_count),
        "by_severity": {row["severity"] or "未指定": row["count"] for row in severity_rows},
        "by_knowledge": {row["kid"] or "未关联": row["count"] for row in knowledge_rows},
    }


def log_reference(kid: str, report_id: str, source: str) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO reference_log (kid, referenced_at, report_id, source)
            VALUES (?, ?, ?, ?)
            """,
            (kid, now_iso(), report_id, source),
        )


def get_recent_references(kid: str) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, kid, referenced_at, report_id, source
            FROM reference_log
            WHERE kid = ?
            ORDER BY referenced_at DESC, id DESC
            LIMIT 5
            """,
            (kid,),
        ).fetchall()
    return [dict(row) for row in rows]
