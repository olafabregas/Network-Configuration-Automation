"""Helpers for loading configuration artifacts.

Expected ``devices.yaml`` structure::

        devices:
            - name: R1
                ip: 192.168.50.10
                username: admin
                device_type: cisco_ios
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, cast

import yaml
from dotenv import load_dotenv  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from netauto_lib.utils import Device

logger = logging.getLogger(__name__)


def load_env(env_path: str = ".env") -> None:
    """Load environment variables from the provided file if it exists."""
    path = Path(env_path)
    if path.exists():
        load_dotenv(path)


def load_devices(path: str = "devices.yaml") -> list["Device"]:
    """Return the list of devices defined in the YAML inventory."""
    inventory_path = Path(path)
    if not inventory_path.exists():
        _report(f"Device inventory not found at {inventory_path}.")
        return []

    try:
        parsed = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        _report(f"Unable to parse {inventory_path}: {exc}")
        return []

    if parsed is None:
        _report("Inventory file is empty.", logging.WARNING)
        return []
    if not isinstance(parsed, dict):
        _report("Inventory file must contain a mapping with a 'devices' list.")
        return []

    parsed_dict = cast(Dict[str, Any], parsed)
    raw_devices = parsed_dict.get("devices")
    if not isinstance(raw_devices, list):
        _report("Inventory file must define a 'devices' list.")
        return []

    device_entries = cast(List[Any], raw_devices)
    normalized: list["Device"] = []
    for entry in device_entries:
        if not isinstance(entry, dict):
            _report("Skipping malformed device entry (not a mapping).", logging.WARNING)
            continue

        entry_dict = cast(Dict[str, Any], entry)
        name = entry_dict.get("name")
        ip_value = entry_dict.get("ip")
        username = entry_dict.get("username")
        if not name or not ip_value or not username:
            _report(
                "Skipping device entry; required keys 'name', 'ip', 'username' are mandatory.",
                logging.WARNING,
            )
            continue

        normalized.append(
            {
                "name": str(name),
                "ip": str(ip_value),
                "username": str(username),
                "device_type": str(entry_dict.get("device_type", "cisco_ios")),
            }
        )
    return normalized


def get_global_settings() -> dict[str, Any]:
    """Return directory and behavior defaults sourced from the environment."""
    backups_dir = Path(os.getenv("BACKUPS_DIR", "backups"))
    logs_dir = Path(os.getenv("LOGS_DIR", "logs"))
    default_ping_raw = os.getenv("DEFAULT_PING_COUNT", "5")
    try:
        default_ping_count = int(default_ping_raw)
    except ValueError:
        print("Invalid DEFAULT_PING_COUNT; falling back to 5.")
        default_ping_count = 5

    return {
        "backups_dir": backups_dir,
        "logs_dir": logs_dir,
        "default_ping_count": default_ping_count,
    }


def _report(message: str, level: int = logging.ERROR) -> None:
    """Print the message and emit it to the module logger."""
    print(message)
    logger.log(level, message)
