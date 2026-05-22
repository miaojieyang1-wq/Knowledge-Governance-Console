# -*- coding: utf-8 -*-
"""Repeatable smoke checks for the Knowledge Governance Console."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"[OK] {name}")


def write_temp_config() -> None:
    Path("config.yaml").write_text(
        "data_dir: data\n"
        "database_file: knowledge_base.db\n"
        "pending_verify_threshold: 0\n"
        "sync_dir: sync\n"
        "launch_host: 127.0.0.1\n"
        "launch_port: 8501\n"
        "launch_timeout_seconds: 30\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    sys.path.insert(0, str(PROJECT_ROOT))
    from synchronizer import export_all_active, export_to_sync, get_sync_stats, remove_sync_file
    from utils import (
        get_badcase_list,
        get_badcase_stats,
        get_dashboard_stats,
        get_knowledge_by_kid,
        get_recent_references,
        init_db,
        insert_badcase,
        insert_knowledge,
        log_reference,
        mark_deprecated,
        update_badcase,
        update_knowledge,
    )

    with tempfile.TemporaryDirectory(prefix="kg_console_selfcheck_", ignore_cleanup_errors=True) as temp_dir:
        original_cwd = Path.cwd()
        os.chdir(temp_dir)
        try:
            write_temp_config()
            init_db()
            check("seed knowledge exists", get_knowledge_by_kid("KID-20260518-001") is not None)
            check("seed reference exists", len(get_recent_references("KID-20260518-001")) == 1)

            kid = "KID-20990101-SELF"
            insert_knowledge(
                {
                    "kid": kid,
                    "title": "自检知识",
                    "content": "第一行\n第二行",
                    "type": "规则",
                    "creator": "自检",
                    "owner": "自检责任人",
                    "approver": "自检审批人",
                    "effective_date": "2099-01-01",
                    "expiry_date": "2099-12-31",
                    "source": "内部运营专家经验",
                    "confidence": "高置信度经多方验证",
                    "version": "1.0",
                    "scope": "自检",
                    "status": "生效中",
                }
            )

            legacy_path = Path("sync") / f"{kid}.md"
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text("# legacy markdown\n", encoding="utf-8", newline="\n")
            yaml_path = export_to_sync(kid)
            yaml_text = yaml_path.read_text(encoding="utf-8")
            payload = yaml.safe_load(yaml_text)
            check("yaml kid", payload["kid"] == kid)
            check("yaml expiry", payload["expiry_date"] == "2099-12-31")
            check("yaml literal block", "content: |" in yaml_text)
            check("legacy markdown cleaned on export", not legacy_path.exists())

            update_knowledge(kid, {"content": "更新后内容", "modifier": "自检", "changelog_summary": "自检更新"})
            updated = get_knowledge_by_kid(kid)
            check("version increments", updated is not None and updated["version"] == "1.1")
            check("changelog appended", updated["modification_logs"][-1]["summary"] == "自检更新")

            log_reference(kid, "REPORT-SELF-CHECK", "手动测试")
            check("reference logged", get_knowledge_by_kid(kid)["recent_references"][0]["report_id"] == "REPORT-SELF-CHECK")

            insert_badcase(
                {
                    "related_knowledge_id": kid,
                    "description": "自检Badcase",
                    "error_level": "轻微细节偏差",
                    "discovery_source": "定期审计主动发现",
                    "reporter": "自检",
                    "status": "待审核",
                }
            )
            pending_badcases = get_badcase_list("待审核")
            check("badcase inserted", len(pending_badcases) == 1)
            update_badcase(
                int(pending_badcases[0]["id"]),
                {"status": "已修正", "reviewer_note": "自检通过", "resolved_at": "2099-01-01T00:00:00+08:00"},
            )
            check("badcase resolved", get_badcase_stats()["pending_count"] == 0)

            check("export all active", export_all_active() >= 2)
            mark_deprecated(kid)
            legacy_path.write_text("# legacy markdown\n", encoding="utf-8", newline="\n")
            check("deprecated sync removed", remove_sync_file(kid) is True)
            check("legacy markdown removed", not legacy_path.exists())

            dashboard_stats = get_dashboard_stats()
            sync_stats = get_sync_stats()
            check("dashboard total", dashboard_stats["total"] == 2)
            check("sync stats", sync_stats["file_count"] >= 1)
            print("[OK] selfcheck complete")
            return 0
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    raise SystemExit(main())
