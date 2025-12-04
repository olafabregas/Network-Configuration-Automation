"""Main entry point for the NetAuto CLI tool."""
from __future__ import annotations

import logging
from typing import Any

from netmiko.base_connection import BaseConnection  # type: ignore[import-untyped]

from netauto_lib.config_loader import get_global_settings, load_devices, load_env
from netauto_lib.connection import connect_to_device
from netauto_lib.logging_setup import setup_logging
from netauto_lib.operations import (
    backup_config,
    configure_interface,
    configure_ospf,
    ping_test,
    show_interfaces,
)
from netauto_lib.utils import Device, choose_device, is_valid_choice

VALID_MENU_CHOICES = {"0", "1", "2", "3", "4", "5"}


def main() -> None:
    """Initialize environment, select device, and handle menu interaction."""
    load_env()
    settings = get_global_settings()
    setup_logging(str(settings["logs_dir"]))
    logger = logging.getLogger(__name__)
    print("\n--- NetAuto CLI - Network Automation Tool ---")

    devices: list[Device] = load_devices()
    if not devices:
        msg = "No devices found in devices.yaml; exiting."
        print(msg)
        logger.error(msg)
        return

    device = choose_device(devices)
    if not device:
        logger.info("Device selection aborted by user; exiting.")
        return

    connection = connect_to_device(device)
    if connection is None:
        logger.error("Connection attempt failed; exiting.")
        return

    try:
        _interactive_menu(connection, device, settings, logger)
    finally:
        try:
            connection.disconnect()
        except AttributeError:
            pass
        logger.info("Program exited normally.")


def _interactive_menu(
    conn: BaseConnection,
    device: Device,
    settings: dict[str, Any],
    logger: logging.Logger,
) -> None:
    """Main interactive menu loop.

    Responsibilities:
    - Present user options.
    - Invoke the corresponding operation.
    - Remain agnostic of connection/setup concerns.
    - Exit cleanly when the user selects 0.
    """
    while True:
        print(
            "\n=== Network Automation Menu ===\n"
            "1) Configure interface\n"
            "2) Show interface status\n"
            "3) Test ping\n"
            "4) Backup running config\n"
            "5) Configure OSPF\n"
            "0) Exit"
        )
        choice = input("Select an option: ").strip()

        if not is_valid_choice(choice, VALID_MENU_CHOICES):
            print("Invalid choice. Please try again.")
            logger.warning("Invalid menu choice: %s", choice)
            continue

        logger.info("Menu selection: %s", choice)

        if choice == "1":
            configure_interface(conn)
        elif choice == "2":
            show_interfaces(conn)
        elif choice == "3":
            ping_test(conn, settings.get("default_ping_count", 5))
        elif choice == "4":
            backup_config(conn, device.get("name", "router"), str(settings["backups_dir"]))
        elif choice == "5":
            configure_ospf(conn)
        elif choice == "0":
            print("Goodbye!")
            logger.info("User exited via menu.")
            return


if __name__ == "__main__":
    main()
