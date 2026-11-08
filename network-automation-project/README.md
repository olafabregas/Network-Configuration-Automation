# NetAuto

Command-line Cisco IOS tasks: interface addresses, interface status, ping, running-config backup, and OSPF.

The repository [README](../README.md) is the full guide. From this directory:

```bash
python -m pip install -r requirements.txt
python netauto.py --demo
```

Use `python3` if `python` is not on your PATH. Python 3.10 or newer is required.

`--demo` runs a scripted walkthrough on a simulated R1/R2 lab. It does not open SSH, read `.env`, or ask for a password. Backups go to `demo_backups/` and the log to `demo_logs/netauto-demo.log`.

Open the same menu yourself with:

```bash
python netauto.py --demo --interactive
```

`python netauto.py` with no flag is the live Netmiko path. It uses `devices.yaml` and prompts for the device password.
