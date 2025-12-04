"""User interaction helpers for device selection.

Expected device structure::

    {
        "name": "R1",
        "ip": "192.168.50.10",
        "username": "admin",
        "device_type": "cisco_ios"
    }
"""
from __future__ import annotations

import logging
from typing import Optional, TypedDict


class Device(TypedDict):
    """Inventory entry describing a managed device."""

    name: str
    ip: str
    username: str
    device_type: str


logger = logging.getLogger(__name__)


def choose_device(devices: list[Device]) -> Optional[Device]:
    """Return the selected device from the inventory or None."""
    if not devices:
        print("No devices found in the inventory. Please update devices.yaml.")
        return None

    if len(devices) == 1:
        only_device = devices[0]
        logger.info("Auto-selected sole device: %s (%s)", only_device.get("name"), only_device.get("ip"))
        print(
            f"Only one device available. Using {only_device.get('name')} ({only_device.get('ip')})."
        )
        return only_device

    while True:
        _print_device_menu(devices)
        selection = input("Select a device number: ").strip()
        index = _safe_int(selection)
        if index is None:
            print("Please enter a valid number.")
            continue
        if 1 <= index <= len(devices):
            chosen = devices[index - 1]
            logger.info("User selected device: %s (%s)", chosen.get("name"), chosen.get("ip"))
            return chosen
        print("Selection out of range. Try again.")


def _print_device_menu(devices: list[Device]) -> None:
    """Print numbered device choices for the user."""
    print("\nAvailable devices:")
    for idx, device in enumerate(devices, start=1):
        name = device.get("name", "Unnamed")
        ip_addr = device.get("ip", "unknown")
        print(f"  {idx}) {name} ({ip_addr})")


def _safe_int(value: str) -> Optional[int]:
    """Convert value to int, returning None on failure."""
    try:
        return int(value)
    except ValueError:
        return None


def is_valid_choice(choice: str, valid_choices: set[str]) -> bool:
    """Return True when the provided menu choice is allowed."""
    return choice in valid_choices
