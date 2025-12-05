##NetAuto – Network Automation CLI Tool
NetAuto is a modular Python-based automation utility designed to streamline common operational tasks on Cisco IOS devices.
It provides a simple command‑line workflow for configuring interfaces, performing connectivity tests, managing OSPF settings, and backing up device configurations — all over secure SSH connections.

The project emphasizes clarity, maintainability, and production‑aligned engineering practices.

1. Overview
NetAuto serves as a lightweight automation orchestrator intended for lab environments, GNS3 topologies, and small‑scale operational scenarios.
Using a structured device inventory (devices.yaml) and environment variables, the tool provides:

Consistent and safe configuration workflows

Clean separation between logic, device definitions, and environment data

Centralized logging

Modular extensibility for future operations

The implementation intentionally mirrors real-world network automation patterns to demonstrate practical engineering competency.

2. Key Features
Device Operations
Interface configuration (IPv4 + subnet mask)

Display interface operational status

Router‑initiated ping testing

Timestamped configuration backup

OSPF configuration including:

Process ID

Router ID

Network/wildcard specification

Area assignment

System-Level Features
Multi‑device inventory support

Secure credential handling (prompted)

Structured logging to file + console

Input validation for all operational prompts

Graceful error and exception handling

Automatic creation of backup and log directories

3. Project Structure
netauto/
├── netauto.py
├── netauto_lib/
│   ├── config_loader.py
│   ├── connection.py
│   ├── logging_setup.py
│   ├── operations.py
│   ├── utils.py
│   └── __init__.py
├── devices.yaml
├── .env
├── config.example.env
└── requirements.txt
Each module provides a single responsibility, ensuring both readability and ease of future enhancements.

4. Installation
Dependencies
pip install -r requirements.txt
Environment Setup
You may either:

Populate .env using config.example.env, or

Allow the CLI to prompt for credentials interactively

Inventory Setup
Define devices in devices.yaml:

devices:
  - name: R1
    ip: 192.0.2.10
    device_type: cisco_ios
    username: admin

  - name: R2
    ip: 192.0.2.11
    device_type: cisco_ios
    username: admin
5. Usage
Run the CLI:

python netauto.py
Select a device, then choose from the menu options:

Configure interface

Show interface status

Test ping

Backup running config

Configure OSPF

Exit

The tool maintains consistent logging for all operations.

6. Logging and Backups
All logs are stored under:

logs/netauto.log
Backups are saved with timestamped filenames:

backups/<hostname>_running_YYYYMMDD-HHMMSS.txt
This ensures operational traceability and reproducibility.

7. Design Considerations
NetAuto was built with several engineering goals:

Modularity: Clear separation of configuration loading, connection handling, operational logic, and user utilities

Reliability: Defensive input validation to prevent malformed configurations

Maintainability: Predictable directory structure and cohesive function boundaries

Extensibility: New operations can be added as isolated functions inside operations.py

Security: Credentials are never stored; they are prompted securely at runtime

This mirrors patterns used in practical network automation workflows.

8. License
This project may be used, studied, and modified freely for educational and non-commercial purposes.

