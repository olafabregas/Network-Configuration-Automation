"""Device operations for the NetAuto tool."""
from __future__ import annotations

import ipaddress
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def configure_interface(conn: Any) -> None:
    """Prompt for interface details and push configuration."""
    interface = _prompt_interface_name()
    ip_addr = _prompt_ipv4("IPv4 address: ")
    mask = _prompt_subnet_mask("Subnet mask (dotted decimal or /prefix): ")

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


def ping_test(conn: Any, default_count: int = 5) -> None:
    """Execute a ping test from the router."""
    destination = _prompt_ipv4("Destination IP: ")
    repeat = _prompt_ping_count(default_count)
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


def configure_ospf(conn: Any) -> None:
    """Configure basic OSPF parameters on the device."""
    process_id = _prompt_positive_int("OSPF process ID: ")
    router_id = _prompt_ipv4("Router ID (IPv4): ")
    network = _prompt_ipv4("Network address (A.B.C.D): ")
    wildcard = _prompt_wildcard_mask("Wildcard mask: ")
    area = _prompt_area()

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
        value = input("Interface (e.g. GigabitEthernet0/0): ").strip()
        if value:
            normalized = value[0].upper() + value[1:] if len(value) > 1 else value.upper()
            logger.debug("Interface accepted: %s", normalized)
            return normalized
        print("Interface name cannot be empty.")


def _prompt_ipv4(prompt_text: str) -> str:
    """Prompt for an IPv4 address and validate input."""
    while True:
        candidate = input(prompt_text).strip()
        try:
            ip_value = str(ipaddress.IPv4Address(candidate))
            logger.debug("IPv4 accepted: %s", ip_value)
            return ip_value
        except ipaddress.AddressValueError:
            print("Invalid IPv4 address. Try again.")


def _prompt_subnet_mask(prompt_text: str) -> str:
    """Prompt for a subnet mask or prefix length and return dotted decimal."""
    while True:
        value = input(prompt_text).strip()
        if not value:
            print("Value cannot be empty.")
            continue
        try:
            network = ipaddress.IPv4Network(f"0.0.0.0/{value}", strict=False)
            mask_value = str(network.netmask)
            logger.debug("Subnet mask accepted: %s", mask_value)
            return mask_value
        except (ipaddress.AddressValueError, ValueError):
            print("Invalid subnet or mask. Use dotted decimal or prefix length.")


def _prompt_positive_int(prompt_text: str) -> int:
    """Prompt until a positive integer is entered."""
    while True:
        value = input(prompt_text).strip()
        if value.isdigit() and int(value) > 0:
            number = int(value)
            logger.debug("Positive integer accepted: %s", number)
            return number
        print("Enter a positive integer.")


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
