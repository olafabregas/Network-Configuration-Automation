"""Checks for the local demo lab and the unchanged SSH default."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from netauto_lib.connection import build_connection_params  # noqa: E402
from netauto_lib.demo import (  # noqa: E402
    SAMPLE_ADDRESS,
    SAMPLE_PING_TARGET,
    DemoConnection,
    demo_inventory,
    run_walkthrough,
)
from netauto_lib.utils import Device  # noqa: E402
import netauto  # noqa: E402


def _r1() -> Device:
    return next(device for device in demo_inventory() if device["name"] == "R1")


class DemoConnectionTests(unittest.TestCase):
    def test_interface_config_updates_brief_and_running_config(self) -> None:
        conn = DemoConnection(_r1())
        transcript = conn.send_config_set(
            [
                "interface GigabitEthernet0/1",
                "ip address 192.168.10.1 255.255.255.0",
                "no shutdown",
            ]
        )
        self.assertIn("R1(config-if)#ip address 192.168.10.1 255.255.255.0", transcript)
        self.assertIn("R1(config-if)#end", transcript)

        brief = conn.send_command("show ip interface brief")
        header, *rows = brief.splitlines()
        address_at = header.index("IP-Address")
        gi1 = next(row for row in rows if row.startswith("GigabitEthernet0/1"))
        self.assertEqual(gi1.index("192.168.10.1"), address_at)
        self.assertIn("manual", gi1)
        self.assertTrue(gi1.rstrip().endswith("up"))

        running = conn.send_command("show running-config")
        self.assertIn("No router was contacted", running)
        self.assertIn("ip address 192.168.10.1 255.255.255.0", running)
        self.assertNotIn("password", running.lower())
        self.assertNotIn("secret", running.lower())

    def test_ping_reaches_neighbor_and_fails_off_the_link(self) -> None:
        conn = DemoConnection(_r1())
        success = conn.send_command(f"ping {SAMPLE_PING_TARGET} repeat 5")
        failure = conn.send_command("ping 203.0.113.5 repeat 3")
        self.assertIn("Success rate is 100 percent (5/5)", success)
        self.assertIn("!!!!!", success)
        self.assertIn("Success rate is 0 percent (0/3)", failure)
        self.assertIn("...", failure)

    def test_ospf_commands_use_router_prompts(self) -> None:
        conn = DemoConnection(_r1())
        transcript = conn.send_config_set(
            [
                "router ospf 1",
                "router-id 1.1.1.1",
                "network 10.1.12.0 0.0.0.3 area 0",
            ]
        )
        self.assertIn("R1(config)#router ospf 1", transcript)
        self.assertIn("R1(config-router)#router-id 1.1.1.1", transcript)
        running = conn.send_command("show running-config")
        self.assertIn("router ospf 1", running)
        self.assertIn("router-id 1.1.1.1", running)
        self.assertIn("network 10.1.12.0 0.0.0.3 area 0", running)


class WalkthroughTests(unittest.TestCase):
    def test_walkthrough_runs_every_operation_without_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with patch("builtins.input", side_effect=AssertionError("demo prompted for input")):
                    with redirect_stdout(io.StringIO()):
                        run_walkthrough(DemoConnection(_r1()), backups_dir="demo_backups")
            finally:
                os.chdir(previous)

            backups = list(Path(tmp, "demo_backups").glob("R1_running_*.txt"))
            self.assertEqual(len(backups), 1)
            text = backups[0].read_text(encoding="utf-8")
            self.assertIn("No router was contacted", text)
            self.assertIn(SAMPLE_ADDRESS, text)
            self.assertIn("router ospf 1", text)
            self.assertIn("network 10.1.12.0 0.0.0.3 area 0", text)
            self.assertNotIn("password", text.lower())
            self.assertNotIn("secret", text.lower())


class CliTests(unittest.TestCase):
    def test_default_invocation_stays_on_the_live_path(self) -> None:
        args = netauto._parse_args([])
        self.assertFalse(args.demo)
        self.assertFalse(args.interactive)
        with self.assertRaises(SystemExit):
            netauto._parse_args(["--interactive"])

    def test_live_connection_params_are_not_written_to_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                params = build_connection_params(
                    {
                        "name": "R1",
                        "ip": "192.0.2.10",
                        "username": "admin",
                        "device_type": "cisco_ios",
                    },
                    "not-stored",
                )
                self.assertEqual(params["password"], "not-stored")
                self.assertEqual(params["host"], "192.0.2.10")
                self.assertEqual(list(Path(tmp).iterdir()), [])
            finally:
                os.chdir(previous)

    def test_demo_command_does_not_import_ssh_libraries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = (
                "import netauto\n"
                "netauto.main(['--demo'])\n"
                "import sys\n"
                "banned = [name for name in ('netmiko', 'paramiko', 'dotenv', 'yaml') if name in sys.modules]\n"
                "print('BANNED=' + ','.join(banned))\n"
            )
            env = os.environ.copy()
            env["PYTHONPATH"] = str(PROJECT_ROOT)
            env["NETAUTO_PASSWORD"] = "should-not-be-used"
            result = subprocess.run(
                [sys.executable, "-c", script],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("BANNED=", result.stdout)
            self.assertIn("BANNED=\n", result.stdout)
            self.assertIn("No SSH", result.stdout)
            self.assertIn("Success rate is 100 percent (5/5)", result.stdout)
            self.assertIn(SAMPLE_ADDRESS, result.stdout)
            self.assertNotIn("should-not-be-used", result.stdout)
            self.assertNotIn("Password", result.stdout)
            self.assertNotIn("Traceback", result.stderr)
            backups = list(Path(tmp, "demo_backups").glob("R1_running_*.txt"))
            self.assertEqual(len(backups), 1)

    def test_interactive_demo_menu_configures_without_ssh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scripted = "\n".join(
                [
                    "1",  # R1
                    "1",  # configure interface
                    "GigabitEthernet0/1",
                    "192.168.10.1",
                    "/24",
                    "2",  # show interfaces
                    "0",
                ]
            )
            env = os.environ.copy()
            env["NETAUTO_PASSWORD"] = "should-not-be-used"
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "netauto.py"), "--demo", "--interactive"],
                cwd=tmp,
                env=env,
                input=scripted,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No SSH", result.stdout)
            self.assertIn("R1(config-if)#ip address 192.168.10.1 255.255.255.0", result.stdout)
            self.assertIn("192.168.10.1", result.stdout)
            self.assertIn("Goodbye!", result.stdout)
            self.assertNotIn("should-not-be-used", result.stdout)
            self.assertNotIn("Traceback", result.stderr)

    def test_inventory_files_do_not_store_passwords(self) -> None:
        inventory = (PROJECT_ROOT / "devices.yaml").read_text(encoding="utf-8")
        example = (PROJECT_ROOT / "config.example.env").read_text(encoding="utf-8")
        self.assertNotRegex(inventory, r"(?i)password\s*:")
        self.assertNotRegex(inventory, r"(?i)secret\s*:")
        self.assertNotRegex(example, r"(?i)password\s*=")
        self.assertNotRegex(example, r"(?i)secret\s*=")


if __name__ == "__main__":
    unittest.main()
