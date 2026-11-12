# NetAuto

NetAuto is a command-line tool for everyday Cisco IOS tasks: set an interface IPv4 address, show interface status, ping from the router, save the running config, and configure OSPF.

![NetAuto demo on a dark terminal: typing python netauto.py --demo configures GigabitEthernet0/1, shows the interface table, pings R2, configures OSPF, and saves the running config on simulated router R1. Then python netauto.py --demo --interactive selects R1, shows interface status, and exits.](docs/media/netauto-demo.gif)

[Watch the full demo video](docs/media/netauto-demo.mp4)

You can try the whole menu on a laptop. Demo mode uses a built-in two-router lab and does not need GNS3, hardware, SSH, a `.env` file, or a password.

## Try it now

Requires Python 3.10 or newer. If the `python` command is missing, use `python3` in the commands below.

```bash
git clone https://github.com/olafabregas/Network-Configuration-Automation.git
cd Network-Configuration-Automation/network-automation-project
python -m pip install -r requirements.txt
python netauto.py --demo
```

That command runs every menu action once on simulated router R1 and exits. The same menu is available interactively:

```bash
python netauto.py --demo --interactive
```

Demo backups land in `demo_backups/` and the demo log in `demo_logs/netauto-demo.log`. Both are labeled as simulated output.

## Use a real lab

Run the same program with no flag. This is the default, and it is the path that talks to devices:

```bash
cd network-automation-project
python netauto.py
```

NetAuto loads `devices.yaml`, asks you to pick a router, prompts for the password with `getpass`, and opens a Netmiko session using that entry's `device_type`. The sample inventory is a telnet lab (`cisco_ios_telnet`). Use `cisco_ios` when the device listens for SSH. The password is prompted on each run. It is not written to disk, read from `.env`, or kept in `devices.yaml`.

Optional file locations and log level live in `.env`. Copy the example and edit the paths if you want; leave passwords out of it.

```bash
cp config.example.env .env
```

`config.example.env` documents `BACKUPS_DIR`, `LOGS_DIR`, `DEFAULT_PING_COUNT`, and `LOG_LEVEL`.

## Sample demo output

This is a real `python netauto.py --demo` run. The backup filename's timestamp changes each time.

```text
--- NetAuto CLI - Network Automation Tool (demo) ---
Simulated Cisco IOS lab. No SSH, no .env file, and no password prompt.
Inventory: R1 (10.1.12.1) and R2 (10.1.12.2).
Backups directory: demo_backups/
Log file: demo_logs/netauto-demo.log

Demo mode: simulated session for R1 (10.1.12.1). No SSH.

Running each menu action once on R1 with sample values.
R2 (10.1.12.2) is the neighbor on GigabitEthernet0/0. Use --demo --interactive to open the menu.


--- 1/5  Configure interface ---
Sample: GigabitEthernet0/1, 192.168.10.1, 255.255.255.0
configure terminal
Enter configuration commands, one per line.  End with CNTL/Z.
R1(config)#interface GigabitEthernet0/1
R1(config-if)#ip address 192.168.10.1 255.255.255.0
R1(config-if)#no shutdown
R1(config-if)#end
R1#

--- 2/5  Show interface status ---
Sample: show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0     10.1.12.1       YES NVRAM  up                    up
GigabitEthernet0/1     192.168.10.1    YES manual up                    up
GigabitEthernet0/2     unassigned      YES NVRAM  administratively down down
Loopback0              1.1.1.1         YES NVRAM  up                    up

--- 3/5  Test ping ---
Sample: ping 10.1.12.2 repeat 5
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 10.1.12.2, timeout is 2 seconds:
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms

--- 4/5  Configure OSPF ---
Sample: process 1, router-id 1.1.1.1, network 10.1.12.0 0.0.0.3 area 0
configure terminal
Enter configuration commands, one per line.  End with CNTL/Z.
R1(config)#router ospf 1
R1(config-router)#router-id 1.1.1.1
R1(config-router)#network 10.1.12.0 0.0.0.3 area 0
R1(config-router)#end
R1#

--- 5/5  Backup running config ---
Sample: written under demo_backups/
Saved running-config to demo_backups/R1_running_20261108-060229.txt
Simulated backup only. The file was written on this computer, not copied from a router.

Walkthrough complete. No network connection was opened.
Interactive menu: python netauto.py --demo --interactive
```

The saved file starts with a banner that says NetAuto generated it locally. The body is IOS-style text for the sample lab, including the interface and OSPF changes from the walkthrough.

## Menu

1. Configure interface (IPv4 address and mask, then `no shutdown`)
2. Show interface status (`show ip interface brief`)
3. Test ping
4. Backup running config
5. Configure OSPF (process, router ID, network, wildcard, area)
0. Exit

Input is checked before it is sent: IPv4 addresses, subnet masks (`255.255.255.0` or `/24`), ping counts, and OSPF values.

## Layout

```text
Network-Configuration-Automation/
├── README.md
└── network-automation-project/
    ├── netauto.py                 # CLI entry point
    ├── netauto_lib/
    │   ├── config_loader.py       # .env and devices.yaml
    │   ├── connection.py          # Netmiko session for the live path
    │   ├── demo.py                # in-memory R1/R2 lab
    │   ├── logging_setup.py
    │   ├── operations.py          # menu actions
    │   └── utils.py               # device picker
    ├── devices.yaml               # live inventory
    ├── config.example.env
    ├── requirements.txt
    └── tests/test_demo.py
```

`--demo` keeps the existing operations and swaps the session. `DemoConnection` implements `send_command` and `send_config_set` in memory, so the menu code is the same one the live path uses. The demo inventory is R1 (`10.1.12.1`) and R2 (`10.1.12.2`). It does not read `devices.yaml`.

## Live inventory

`devices.yaml` lists lab routers. A password field is not part of the file. Example:

```yaml
devices:
  - name: R1
    ip: 10.1.12.1
    username: cisco
    device_type: cisco_ios_telnet
```

Required keys are `name`, `ip`, and `username`. `device_type` defaults to `cisco_ios` when it is omitted.

## Logs and backups

| Run | Log | Backups |
| --- | --- | --- |
| `python netauto.py` | `logs/netauto.log` | `backups/<hostname>_running_<UTC timestamp>.txt` |
| `python netauto.py --demo` | `demo_logs/netauto-demo.log` | `demo_backups/<hostname>_running_<UTC timestamp>.txt` |

Directories are created on first use. Generated logs and backups are gitignored.

## Tests

From `network-automation-project`:

```bash
python -m unittest discover -s tests
```

## License

Educational and non-commercial use.
