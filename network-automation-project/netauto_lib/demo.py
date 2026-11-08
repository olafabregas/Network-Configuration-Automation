"""In-memory Cisco IOS lab used by ``python netauto.py --demo``.

The mock speaks the same two methods the live operations already call
(``send_command`` and ``send_config_set``). Nothing here opens a socket.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from netauto_lib.operations import (
    backup_config,
    configure_interface,
    configure_ospf,
    ping_test,
    show_interfaces,
)
from netauto_lib.utils import Device

DEMO_BACKUPS_DIR = "demo_backups"
DEMO_LOGS_DIR = "demo_logs"
DEMO_LOG_NAME = "netauto-demo.log"

# Walkthrough inputs. Kept in one place so the CLI, tests, and README stay aligned.
SAMPLE_INTERFACE = "GigabitEthernet0/1"
SAMPLE_ADDRESS = "192.168.10.1"
SAMPLE_MASK = "255.255.255.0"
SAMPLE_PING_TARGET = "10.1.12.2"
SAMPLE_PING_COUNT = 5
SAMPLE_OSPF_PROCESS = 1
SAMPLE_ROUTER_ID = "1.1.1.1"
SAMPLE_NETWORK = "10.1.12.0"
SAMPLE_WILDCARD = "0.0.0.3"
SAMPLE_AREA = "0"

_LINK = {
    "R1": "10.1.12.1",
    "R2": "10.1.12.2",
}
_NEIGHBOR = {
    "R1": "10.1.12.2",
    "R2": "10.1.12.1",
}
_LOOPBACK = {
    "R1": "1.1.1.1",
    "R2": "2.2.2.2",
}
_PING_RE = re.compile(r"^ping\s+(\S+?)(?:\s+repeat\s+(\d+))?\s*$", re.IGNORECASE)
_DEMO_COMMENT_LINES = (
    "! Demo configuration generated locally by NetAuto --demo.",
    "! No router was contacted. This text is not a backup from a live device.",
)


@dataclass
class DemoInterface:
    """One interface on a simulated router."""

    name: str
    ip: str | None = None
    mask: str | None = None
    admin_down: bool = False
    method: str = "NVRAM"
    is_ethernet: bool = True

    @property
    def status(self) -> str:
        """Return the IOS Status column."""
        if self.admin_down:
            return "administratively down"
        return "up"

    @property
    def protocol(self) -> str:
        """Return the IOS Protocol column."""
        if self.admin_down or not self.ip:
            return "down"
        return "up"


@dataclass
class DemoConnection:
    """Fake Netmiko session for one sample router.

    Only the methods ``operations.py`` uses are implemented. Configuration
    changes stay in memory and show up in later ``show`` and backup output.
    """

    device: Device
    interfaces: dict[str, DemoInterface] = field(default_factory=dict)
    ospf_process: int | None = None
    router_id: str | None = None
    ospf_networks: list[tuple[str, str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.hostname = self.device["name"]
        if not self.interfaces:
            self.interfaces = _seed_interfaces(self.hostname)

    def send_command(self, command: str, *args: object, **kwargs: object) -> str:
        """Return canned exec-mode output for a command string."""
        del args, kwargs
        text = command.strip()
        lowered = text.lower()
        if lowered == "show ip interface brief":
            return self._show_ip_interface_brief()
        if lowered == "show running-config":
            return self._running_config()
        ping = _PING_RE.match(text)
        if ping:
            repeat = int(ping.group(2) or "5")
            return self._ping(ping.group(1), repeat)
        return f"% Invalid input detected at '^' marker.\n\n{self.hostname}#"

    def send_config_set(self, config_commands: list[str] | str, *args: object, **kwargs: object) -> str:
        """Apply a configuration set and return an IOS-style transcript."""
        del args, kwargs
        if isinstance(config_commands, str):
            commands = [config_commands]
        else:
            commands = [str(command) for command in config_commands]

        mode = "config"
        current: DemoInterface | None = None
        lines = [
            "configure terminal",
            "Enter configuration commands, one per line.  End with CNTL/Z.",
        ]
        for command in commands:
            lines.append(f"{_config_prompt(self.hostname, mode)}{command}")
            mode, current, applied = self._apply(command, mode, current)
            if not applied:
                lines.append("% Invalid input detected at '^' marker.")
        lines.append(f"{_config_prompt(self.hostname, mode)}end")
        lines.append(f"{self.hostname}#")
        return "\n".join(lines)

    def disconnect(self) -> None:
        """Close the simulated session. There is no socket to tear down."""
        return None

    def _apply(
        self,
        command: str,
        mode: str,
        current: DemoInterface | None,
    ) -> tuple[str, DemoInterface | None, bool]:
        text = command.strip()
        parts = text.split()
        if not parts:
            return mode, current, False

        keyword = parts[0].lower()
        if keyword == "interface" and len(parts) >= 2:
            iface = self._ensure_interface(" ".join(parts[1:]))
            return "config-if", iface, True
        if keyword == "router" and len(parts) >= 3 and parts[1].lower() == "ospf" and parts[2].isdigit():
            self.ospf_process = int(parts[2])
            return "config-router", current, True
        if text.lower() == "no shutdown" and mode == "config-if" and current is not None:
            current.admin_down = False
            return mode, current, True
        if keyword == "shutdown" and mode == "config-if" and current is not None:
            current.admin_down = True
            return mode, current, True
        if (
            keyword == "ip"
            and len(parts) >= 4
            and parts[1].lower() == "address"
            and mode == "config-if"
            and current is not None
        ):
            current.ip = parts[2]
            current.mask = parts[3]
            current.method = "manual"
            return mode, current, True
        if keyword == "router-id" and len(parts) >= 2 and mode == "config-router":
            self.router_id = parts[1]
            return mode, current, True
        if (
            keyword == "network"
            and mode == "config-router"
            and len(parts) >= 5
            and parts[3].lower() == "area"
        ):
            entry = (parts[1], parts[2], parts[4])
            self.ospf_networks = [
                item for item in self.ospf_networks if item[0] != entry[0] or item[1] != entry[1]
            ]
            self.ospf_networks.append(entry)
            return mode, current, True
        return mode, current, False

    def _ensure_interface(self, name: str) -> DemoInterface:
        existing = self._find(name)
        if existing is not None:
            return existing
        is_ethernet = not name.lower().startswith("loopback")
        iface = DemoInterface(
            name=name,
            admin_down=is_ethernet,
            method="unset",
            is_ethernet=is_ethernet,
        )
        self.interfaces[name] = iface
        return iface

    def _find(self, name: str) -> DemoInterface | None:
        for iface in self.interfaces.values():
            if iface.name.lower() == name.lower():
                return iface
        return None

    def _show_ip_interface_brief(self) -> str:
        header = (
            f"{'Interface':<23}{'IP-Address':<16}{'OK?':<4}{'Method':<7}{'Status':<22}Protocol"
        )
        rows = [header]
        for iface in self.interfaces.values():
            address = iface.ip if iface.ip else "unassigned"
            rows.append(
                f"{iface.name:<23}{address:<16}{'YES':<4}{iface.method:<7}"
                f"{iface.status:<22}{iface.protocol}"
            )
        return "\n".join(rows)

    def _ping(self, destination: str, repeat: int) -> str:
        count = repeat if repeat > 0 else 5
        reachable = self._can_ping(destination)
        mark = "!" if reachable else "."
        graphic = _wrap_marks(mark * count)
        if reachable:
            result = (
                f"Success rate is 100 percent ({count}/{count}), "
                "round-trip min/avg/max = 1/2/4 ms"
            )
        else:
            result = f"Success rate is 0 percent (0/{count})"
        return (
            "Type escape sequence to abort.\n"
            f"Sending {count}, 100-byte ICMP Echos to {destination}, timeout is 2 seconds:\n"
            f"{graphic}\n"
            f"{result}"
        )

    def _can_ping(self, destination: str) -> bool:
        for iface in self.interfaces.values():
            if iface.ip == destination and iface.protocol == "up":
                return True
        neighbor = _NEIGHBOR.get(self.hostname)
        link = self._find("GigabitEthernet0/0")
        return bool(neighbor and destination == neighbor and link and link.protocol == "up")

    def _running_config(self) -> str:
        lines = [
            "!",
            *_DEMO_COMMENT_LINES,
            "!",
            "version 15.7",
            "service timestamps debug datetime msec",
            "service timestamps log datetime msec",
            "!",
            f"hostname {self.hostname}",
            "!",
            "boot-start-marker",
            "boot-end-marker",
            "!",
            "no aaa new-model",
            "!",
            "ip cef",
            "!",
        ]
        for iface in self.interfaces.values():
            lines.append(f"interface {iface.name}")
            if iface.ip and iface.mask:
                lines.append(f" ip address {iface.ip} {iface.mask}")
            else:
                lines.append(" no ip address")
            if iface.is_ethernet:
                if iface.admin_down:
                    lines.append(" shutdown")
                lines.append(" duplex auto")
                lines.append(" speed auto")
            lines.append("!")
        if self.ospf_process is not None:
            lines.append(f"router ospf {self.ospf_process}")
            if self.router_id:
                lines.append(f" router-id {self.router_id}")
            for network, wildcard, area in self.ospf_networks:
                lines.append(f" network {network} {wildcard} area {area}")
            lines.append("!")
        lines.extend(
            [
                "ip forward-protocol nd",
                "!",
                "line con 0",
                "line aux 0",
                "line vty 0 4",
                " login",
                " transport input none",
                "!",
                "end",
            ]
        )
        body = "\n".join(lines)
        return (
            "Building configuration...\n\n"
            f"Current configuration : {len(body)} bytes\n"
            f"{body}"
        )


def demo_inventory() -> list[Device]:
    """Return the built-in R1/R2 lab. No passwords are included."""
    return [
        {
            "name": "R1",
            "ip": _LINK["R1"],
            "username": "demo",
            "device_type": "cisco_ios",
        },
        {
            "name": "R2",
            "ip": _LINK["R2"],
            "username": "demo",
            "device_type": "cisco_ios",
        },
    ]


def open_demo_session(device: Device) -> DemoConnection:
    """Attach to a simulated router and say so on stdout."""
    print(
        f"\nDemo mode: simulated session for {device['name']} ({device['ip']}). No SSH."
    )
    return DemoConnection(device)


def run_walkthrough(conn: DemoConnection, backups_dir: str = DEMO_BACKUPS_DIR) -> None:
    """Run every menu operation once against ``conn`` using sample values."""
    print(f"\nRunning each menu action once on {conn.hostname} with sample values.")
    print(
        "R2 (10.1.12.2) is the neighbor on GigabitEthernet0/0. "
        "Use --demo --interactive to open the menu.\n"
    )

    _print_step(
        1,
        "Configure interface",
        f"{SAMPLE_INTERFACE}, {SAMPLE_ADDRESS}, {SAMPLE_MASK}",
    )
    configure_interface(
        conn,
        interface=SAMPLE_INTERFACE,
        ip_addr=SAMPLE_ADDRESS,
        mask=SAMPLE_MASK,
    )

    _print_step(2, "Show interface status", "show ip interface brief")
    show_interfaces(conn)

    _print_step(3, "Test ping", f"ping {SAMPLE_PING_TARGET} repeat {SAMPLE_PING_COUNT}")
    ping_test(conn, destination=SAMPLE_PING_TARGET, count=SAMPLE_PING_COUNT)

    _print_step(
        4,
        "Configure OSPF",
        (
            f"process {SAMPLE_OSPF_PROCESS}, router-id {SAMPLE_ROUTER_ID}, "
            f"network {SAMPLE_NETWORK} {SAMPLE_WILDCARD} area {SAMPLE_AREA}"
        ),
    )
    configure_ospf(
        conn,
        process_id=SAMPLE_OSPF_PROCESS,
        router_id=SAMPLE_ROUTER_ID,
        network=SAMPLE_NETWORK,
        wildcard=SAMPLE_WILDCARD,
        area=SAMPLE_AREA,
    )

    _print_step(5, "Backup running config", f"written under {backups_dir}/")
    backup_config(conn, conn.hostname, backups_dir)
    print("Simulated backup only. The file was written on this computer, not copied from a router.")

    print("\nWalkthrough complete. No network connection was opened.")
    print("Interactive menu: python netauto.py --demo --interactive")


def _print_step(number: int, title: str, sample: str) -> None:
    print(f"\n--- {number}/5  {title} ---")
    print(f"Sample: {sample}")


def _config_prompt(hostname: str, mode: str) -> str:
    if mode == "config-if":
        return f"{hostname}(config-if)#"
    if mode == "config-router":
        return f"{hostname}(config-router)#"
    return f"{hostname}(config)#"


def _wrap_marks(marks: str) -> str:
    if not marks:
        return ""
    return "\n".join(marks[index : index + 80] for index in range(0, len(marks), 80))


def _seed_interfaces(hostname: str) -> dict[str, DemoInterface]:
    link_ip = _LINK.get(hostname, "10.1.12.1")
    loopback_ip = _LOOPBACK.get(hostname, "1.1.1.1")
    interfaces = [
        DemoInterface(
            name="GigabitEthernet0/0",
            ip=link_ip,
            mask="255.255.255.252",
            admin_down=False,
            method="NVRAM",
        ),
        DemoInterface(name="GigabitEthernet0/1", admin_down=True, method="NVRAM"),
        DemoInterface(name="GigabitEthernet0/2", admin_down=True, method="NVRAM"),
        DemoInterface(
            name="Loopback0",
            ip=loopback_ip,
            mask="255.255.255.255",
            admin_down=False,
            method="NVRAM",
            is_ethernet=False,
        ),
    ]
    return {iface.name: iface for iface in interfaces}
