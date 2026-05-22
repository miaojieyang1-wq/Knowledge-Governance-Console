# -*- coding: utf-8 -*-
"""Export knowledge units to Agent-readable YAML sync files."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from utils import get_all_knowledge, get_knowledge_by_kid, load_config


class LiteralString(str):
    """Marker for YAML literal block scalar output."""


def _get_sync_dir() -> Path:
    config = load_config()
    return Path(config.get("sync_dir", "sync"))


def _remove_legacy_markdown(sync_dir: Path, kid: str) -> None:
    legacy_path = sync_dir / f"{kid}.md"
    if legacy_path.exists():
        legacy_path.unlink()


def _dump_yaml(payload: dict[str, Any]) -> str:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for YAML export. Run: python -m pip install -r requirements.txt") from exc

    def literal_string_representer(dumper: yaml.SafeDumper, data: LiteralString) -> yaml.nodes.ScalarNode:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")

    yaml.SafeDumper.add_representer(LiteralString, literal_string_representer)
    return yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_active(item: dict[str, Any]) -> bool:
    if item.get("status") != "生效中":
        return False
    expiry_date = _parse_date(item.get("expiry_date"))
    return expiry_date is None or expiry_date >= date.today()


def _to_yaml_payload(item: dict[str, Any]) -> dict[str, Any]:
    content = str(item.get("content") or "")
    return {
        "kid": item.get("kid") or item.get("knowledge_id"),
        "title": item.get("title"),
        "content": LiteralString(content) if "\n" in content or len(content) > 60 else content,
        "type": item.get("type") or item.get("knowledge_type"),
        "creator": item.get("creator"),
        "owner": item.get("owner"),
        "approver": item.get("approver"),
        "effective_date": item.get("effective_date"),
        "expiry_date": item.get("expiry_date") or None,
        "source": item.get("source"),
        "confidence": item.get("confidence") or item.get("trust_rating"),
        "version": item.get("version"),
        "scope": item.get("scope"),
        "status": item.get("status"),
    }


def export_to_sync(kid: str) -> Path:
    """Export one knowledge unit to sync/<kid>.yaml."""
    item = get_knowledge_by_kid(kid)
    if item is None:
        raise ValueError(f"Knowledge unit not found: {kid}")
    sync_dir = _get_sync_dir()
    sync_dir.mkdir(parents=True, exist_ok=True)
    output_path = sync_dir / f"{kid}.yaml"
    yaml_text = _dump_yaml(_to_yaml_payload(item))
    with output_path.open("w", encoding="utf-8", newline="\n") as file_obj:
        file_obj.write(yaml_text)
    _remove_legacy_markdown(sync_dir, kid)
    return output_path


def export_all_active() -> int:
    """Export all active, non-expired knowledge units. Return exported count."""
    exported_count = 0
    for item in get_all_knowledge({"status": "生效中", "sort_by": "kid", "sort_order": "ASC"}):
        kid = item.get("kid") or item.get("knowledge_id")
        if kid and _is_active(item):
            export_to_sync(str(kid))
            exported_count += 1
    return exported_count


def remove_sync_file(kid: str) -> bool:
    """Remove sync/<kid>.yaml and any legacy Markdown export if they exist."""
    sync_dir = _get_sync_dir()
    output_path = sync_dir / f"{kid}.yaml"
    removed = False
    if output_path.exists():
        output_path.unlink()
        removed = True
    legacy_path = sync_dir / f"{kid}.md"
    if legacy_path.exists():
        legacy_path.unlink()
        removed = True
    return removed


def get_sync_stats() -> dict[str, Any]:
    """Return YAML file count and latest modified time in sync/."""
    sync_dir = _get_sync_dir()
    if not sync_dir.exists():
        return {"file_count": 0, "last_modified": ""}
    yaml_files = sorted(sync_dir.glob("*.yaml"))
    if not yaml_files:
        return {"file_count": 0, "last_modified": ""}
    latest_mtime = max(path.stat().st_mtime for path in yaml_files)
    return {
        "file_count": len(yaml_files),
        "last_modified": datetime.fromtimestamp(latest_mtime).isoformat(timespec="seconds"),
    }
