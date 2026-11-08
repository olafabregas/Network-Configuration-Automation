"""Device operations for the NetAuto tool."""
from __future__ import annotations

import ipaddress
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def configure_interface(
    conn: Any,
    interface: str | None = None,
    ip_addr: str | None = None,
    mask: str | None = None,
) -> None:
    """Prompt for interface details and push configuration.

    Pass ``interface``, ``ip_addr``, and ``mask`` to skip the prompts. The demo
    walkthrough uses that path; the menu leaves them empty and asks the operator.
    """
    interface = _prompt_interface_name() if interface is None else _require_interface(interface)
    ip_addr = _prompt_ipv4("IPv4 address: ") if ip_addr is None else _require_ipv4(ip_addr)
    mask = _prompt_subnet_mask("Subnet mask (dotted decimal or /prefix): ") if mask is None else _require_mask(mask)

    commands = [
        f"interface {interface}",
        f"ip address {ip_addr} {mask}",
        "no shutdown",
    ]
    logger.info("Configuring interface %s with %s %s", interface, ip_addr, mask)
    output = _send_config(conn, commands, "interface configuration")
    if output is not None:
        print(output)


def show_interfaces(conn: Any) -> None:
    """Display 'show ip interface brief' output."""
    logger.info("Running 'show ip interface brief'")
    output = _send_command(conn, "show ip interface brief", "interface summary")
    if output is not None:
        print(output)


def ping_test(
    conn: Any,
    default_count: int = 5,
    destination: str | None = None,
    count: int | None = None,
) -> None:
    """Execute a ping test from the router.

    ``destination`` and ``count`` skip the prompts when the caller already has
    sample values, as the demo walkthrough does.
    """
    destination = _prompt_ipv4("Destination IP: ") if destination is None else _require_ipv4(destination)
    repeat = _prompt_ping_count(default_count) if count is None else _require_positive_int(count, "Ping count")
    logger.info("Pinging %s %s times", destination, repeat)
    output = _send_command(conn, f"ping {destination} repeat {repeat}", "ping test")
    if output is not None:
        print(output)


def backup_config(conn: Any, hostname: str, backups_dir: str) -> None:
    """Save running configuration to disk."""
    logger.info("Backing up running-config for %s", hostname)
    config_text = _send_command(conn, "show running-config", "running-config capture")
    if config_text is None:
        return
    backup_path = Path(backups_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = backup_path / f"{hostname}_running_{timestamp}.txt"
    filename.write_text(config_text, encoding="utf-8")
    print(f"Saved running-config to {filename}")
    logger.info("Backup stored at %s", filename)


def configure_ospf(
    conn: Any,
    process_id: int | None = None,
    router_id: str | None = None,
    network: str | None = None,
    wildcard: str | None = None,
    area: str | None = None,
) -> None:
    """Configure basic OSPF parameters on the device.

    Any argument left as ``None`` is prompted. The demo walkthrough supplies
    all of them.
    """
    process_id = (
        _prompt_positive_int("OSPF process ID: ")
        if process_id is None
        else _require_positive_int(process_id, "OSPF process ID")
    )
    router_id = _prompt_ipv4("Router ID (IPv4): ") if router_id is None else _require_ipv4(router_id)
    network = _prompt_ipv4("Network address (A.B.C.D): ") if network is None else _require_ipv4(network)
    wildcard = _prompt_wildcard_mask("Wildcard mask: ") if wildcard is None else _require_ipv4(wildcard)
    area = _prompt_area() if area is None else _require_area(area)

    commands = [
        f"router ospf {process_id}",
        f"router-id {router_id}",
        f"network {network} {wildcard} area {area}",
    ]
    logger.info(
        "Configuring OSPF process %s, router-id %s, network %s %s area %s",
        process_id,
        router_id,
        network,
        wildcard,
        area,
    )
    output = _send_config(conn, commands, "OSPF configuration")
    if output is not None:
        print(output)


def _prompt_interface_name() -> str:
    """Prompt for an interface name and normalize casing."""
    while True:
        try:
            normalized = _require_interface(input("Interface (e.g. GigabitEthernet0/0): "))
        except ValueError as exc:
            print(exc)
            continue
        logger.debug("Interface accepted: %s", normalized)
        return normalized


def _prompt_ipv4(prompt_text: str) -> str:
    """Prompt for an IPv4 address and validate input."""
    while True:
        try:
            ip_value = _require_ipv4(input(prompt_text))
        except ipaddress.AddressValueError:
            print("Invalid IPv4 address. Try again.")
            continue
        logger.debug("IPv4 accepted: %s", ip_value)
        return ip_value


def _prompt_subnet_mask(prompt_text: str) -> str:
    """Prompt for a subnet mask or prefix length and return dotted decimal."""
    while True:
        try:
            mask_value = _require_mask(input(prompt_text))
        except ValueError:
            print("Invalid subnet or mask. Use dotted decimal or prefix length.")
            continue
        logger.debug("Subnet mask accepted: %s", mask_value)
        return mask_value


def _prompt_positive_int(prompt_text: str) -> int:
    """Prompt until a positive integer is entered."""
    while True:
        raw = input(prompt_text).strip()
        if raw.isdigit():
            try:
                number = _require_positive_int(int(raw), prompt_text)
            except ValueError:
                print("Enter a positive integer.")
                continue
            logger.debug("Positive integer accepted: %s", number)
            return number
        print("Enter a positive integer.")


def _require_interface(value: str) -> str:
    """Normalize an interface name or raise ``ValueError`` when it is empty."""
    text = value.strip()
    if not text:
        raise ValueError("Interface name cannot be empty.")
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()


def _require_ipv4(value: str) -> str:
    """Return a canonical IPv4 address or raise ``AddressValueError``."""
    return str(ipaddress.IPv4Address(value.strip()))


def _require_mask(value: str) -> str:
    """Return a dotted-decimal mask from a mask or prefix length."""
    token = value.strip()
    if not token:
        raise ValueError("Value cannot be empty.")
    if token.startswith("/"):
        token = token[1:]
    network = ipaddress.IPv4Network(f"0.0.0.0/{token}", strict=False)
    return str(network.netmask)


def _require_positive_int(value: int, label: str) -> int:
    """Return ``value`` when it is a positive integer."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")
    return value


def _require_area(value: str) -> str:
    """Return a non-empty OSPF area id."""
    area = value.strip()
    if not area:
        raise ValueError("Area cannot be empty.")
    return area


def _prompt_ping_count(default_count: int) -> int:
    """Prompt for ping repeat count with a default fallback."""
    raw = input(f"Ping count [{default_count}]: ").strip()
    if not raw:
        logger.debug("Ping count default applied: %s", default_count)
        return default_count
    if raw.isdigit() and int(raw) > 0:
        count = int(raw)
        logger.debug("Ping count accepted: %s", count)
        return count
    print("Invalid count. Using default.")
    return default_count


def _prompt_area() -> str:
    """Prompt until a non-empty OSPF area ID is entered."""
    while True:
        area = input("Area ID: ").strip()
        if area:
            logger.debug("Area accepted: %s", area)
            return area
        print("Area cannot be empty.")


def _prompt_wildcard_mask(prompt_text: str) -> str:
    """Prompt for a wildcard mask and ensure it is a valid IPv4 address."""
    while True:
        value = input(prompt_text).strip()
        try:
            wildcard = str(ipaddress.IPv4Address(value))
            logger.debug("Wildcard mask accepted: %s", wildcard)
            return wildcard
        except ipaddress.AddressValueError:
            print("Invalid wildcard mask. Use dotted decimal (e.g. 0.0.0.255).")


def _send_config(conn: Any, commands: list[str], action: str) -> str | None:
    """Execute a configuration set with error handling."""
    try:
        return conn.send_config_set(commands)
    except Exception as exc:  # pragma: no cover - Netmiko raises many subclasses
        logger.error("Failed during %s: %s", action, exc)
        print(f"An error occurred while performing {action}.")
        return None


def _send_command(conn: Any, command: str, action: str) -> str | None:
    """Execute an exec-mode command with error handling."""
    try:
        return conn.send_command(command)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed during %s: %s", action, exc)
        print(f"An error occurred while performing {action}.")
        return None
