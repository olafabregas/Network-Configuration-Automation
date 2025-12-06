"""Netmiko connection helpers."""
from __future__ import annotations

import logging
from getpass import getpass
from typing import Any, Optional, TYPE_CHECKING, cast

from netmiko import ConnectHandler  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from netauto_lib.utils import Device

    class NetmikoAuthenticationException(BaseException):
        ...

    class NetmikoTimeoutException(BaseException):
        ...
else:
    try:
        from netmiko.ssh_exception import (  # type: ignore[import-untyped]
            NetmikoAuthenticationException,
            NetmikoTimeoutException,
        )
    except ModuleNotFoundError:  # Netmiko >= 4.3 relocated exceptions
        from netmiko.exceptions import (  # type: ignore[import-untyped]
            NetmikoAuthenticationException,
            NetmikoTimeoutException,
        )

logger = logging.getLogger(__name__)


def build_connection_params(device: "Device", password: str) -> dict[str, Any]:
    """Return keyword arguments for Netmiko ConnectHandler."""
    host_value = device.get("ip") or device.get("host")
    if not host_value:
        raise ValueError("Device entry must include an 'ip' value.")
    return {
        "device_type": device.get("device_type", "cisco_ios"),
        "host": host_value,
        "username": device.get("username"),
        "password": password,
    }


def connect_to_device(device: "Device") -> Optional[Any]:
    """Prompt for missing credentials and establish a Netmiko session.

    Returns an active Netmiko connection on success, otherwise ``None`` after
    logging the failure. Netmiko timeout/authentication exceptions are caught
    so callers can handle connection issues gracefully.
    """
    username = device.get("username")
    if not username:
        username = input("Device username: ").strip()
        logger.warning("Prompted user for missing username on device %s", device.get("name"))
    username = str(username)
    password = getpass(f"Password for {username}: ")

    enriched = cast("Device", {**device, "username": username})
    params = build_connection_params(enriched, password)
    host_display = str(params.get("host", "unknown"))
    device_name = device.get("name", host_display)
    print(f"Connecting to {device_name} ({host_display}) ...")
    try:
        connection = ConnectHandler(**params)
        print(f"Connected to {host_display}.")
        logger.info("Connected to %s", host_display)
        return connection
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as exc:  # type: ignore[misc]
        print(f"Unable to connect to {host_display}: {exc}")
        logger.error("Failed connecting to %s: %s", host_display, exc)  # type: ignore[arg-type]
        return None
