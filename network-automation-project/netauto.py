"""Main entry point for the NetAuto CLI tool."""
from __future__ import annotations

import argparse
import logging
from typing import Any, Optional, Sequence

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


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Run the live device CLI, or the local demo when ``--demo`` is set."""
    args = _parse_args(argv)
    if args.demo:
        _run_demo(interactive=args.interactive)
        return
    _run_live()


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="netauto.py",
        description="Configure and check Cisco IOS devices from a small menu.",
        epilog=(
            "examples:\n"
            "  python netauto.py --demo\n"
            "  python netauto.py --demo --interactive\n"
            "  python netauto.py"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use the built-in R1/R2 lab. No SSH, .env file, or password prompt.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="With --demo, open the device menu instead of the scripted walkthrough.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.interactive and not args.demo:
        parser.error("--interactive is only available together with --demo")
    return args


def _run_live() -> None:
    """Prompt for a real device and drive the menu over Netmiko. Unchanged default path."""
    from netauto_lib.config_loader import get_global_settings, load_devices, load_env
    from netauto_lib.connection import connect_to_device

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


def _run_demo(interactive: bool) -> None:
    """Run the sample lab locally. Does not load ``.env`` or open SSH."""
    from netauto_lib.demo import (
        DEMO_BACKUPS_DIR,
        DEMO_LOG_NAME,
        DEMO_LOGS_DIR,
        demo_inventory,
        open_demo_session,
        run_walkthrough,
    )

    setup_logging(DEMO_LOGS_DIR, log_name=DEMO_LOG_NAME, console_level=logging.WARNING)
    logger = logging.getLogger(__name__)
    print("\n--- NetAuto CLI - Network Automation Tool (demo) ---")
    print("Simulated Cisco IOS lab. No SSH, no .env file, and no password prompt.")
    print("Inventory: R1 (10.1.12.1) and R2 (10.1.12.2).")
    print(f"Backups directory: {DEMO_BACKUPS_DIR}/")
    print(f"Log file: {DEMO_LOGS_DIR}/{DEMO_LOG_NAME}")
    logger.info("Demo mode started. SSH was not used.")

    if interactive:
        device = choose_device(demo_inventory())
        if not device:
            logger.info("Demo device selection aborted by user; exiting.")
            return
        connection = open_demo_session(device)
        settings = {
            "backups_dir": DEMO_BACKUPS_DIR,
            "logs_dir": DEMO_LOGS_DIR,
            "default_ping_count": 5,
        }
        try:
            _interactive_menu(connection, device, settings, logger)
        finally:
            connection.disconnect()
            logger.info("Demo session closed without contacting a router.")
        return

    device = next(item for item in demo_inventory() if item["name"] == "R1")
    connection = open_demo_session(device)
    try:
        run_walkthrough(connection, DEMO_BACKUPS_DIR)
    finally:
        connection.disconnect()
        logger.info("Demo walkthrough finished without contacting a router.")


def _interactive_menu(
    conn: Any,
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
        try:
            choice = input("Select an option: ").strip()
        except EOFError:
            print("\nGoodbye!")
            logger.info("User exited via EOF.")
            return

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
