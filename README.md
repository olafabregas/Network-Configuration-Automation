# NetAuto – Network Automation CLI Tool

NetAuto is a modular Python-based automation tool designed to streamline common operational tasks on Cisco IOS devices.  
It provides a structured command-line workflow for configuration changes, troubleshooting, and routine device operations, built with maintainability and clarity in mind.

---

## 1. Overview

NetAuto enables engineers to automate repetitive network tasks using a simple CLI interface.  
The tool interacts with routers over SSH, using a device inventory and environment variables to maintain separation between code, configuration, and credentials.

Key design principles include:

- Modular architecture  
- Safe configuration workflows  
- Clear input validation  
- Structured logging  
- Extensibility for future features  

NetAuto is suitable for use in lab environments, GNS3 simulations, and small-scale operational networks.

---

## 2. Features

### Device Operations
- Configure interface IPv4 address and subnet mask  
- Display interface operational status  
- Conduct router-initiated ping tests  
- Backup running configuration with timestamped filenames  
- Configure OSPF (process ID, router ID, network/wildcard, area)

### System-Level Features
- Multi-device inventory through `devices.yaml`  
- Secure credential prompting via `getpass`  
- Centralized logging with file + console output  
- Automatic creation of log and backup directories  
- Error handling for timeout, authentication, and invalid input  
- Clean shutdown of SSH sessions  

---

## 3. Project Structure
netauto/
├── netauto.py
├── netauto_lib/
│ ├── config_loader.py
│ ├── connection.py
│ ├── logging_setup.py
│ ├── operations.py
│ ├── utils.py
│ └── init.py
├── devices.yaml
├── .env
├── config.example.env
└── requirements.txt

- `netauto.py` — main CLI entrypoint  
- `config_loader.py` — environment + inventory loader  
- `connection.py` — SSH connection management (Netmiko)  
- `logging_setup.py` — file + console logging configuration  
- `operations.py` — interface, OSPF, ping, and backup operations  
- `utils.py` — device picker and helper utilities  

---

## 4. Installation

### Install dependencies
```bash
pip install -r requirements.txt

Configure environment variables
Create a .env file or use interactive prompts.

Configure device inventory
Example devices.yaml:

devices:
  - name: R1
    ip: 192.0.2.10
    device_type: cisco_ios
    username: admin

  - name: R2
    ip: 192.0.2.11
    device_type: cisco_ios
    username: admin
```
---

## 5. Usage
Run the tool:

python netauto.py
Menu options include:

Configure interface

Show interface status

Test ping

Backup running config

Configure OSPF

Exit

All operations are logged automatically.

---

## 6. Logging & Backups
Logs stored under:

logs/netauto.log
Backups stored under:

backups/<hostname>_running_<timestamp>.txt
This ensures traceability for all operations performed.

---

## 7. Design Considerations
NetAuto was built with the following priorities:

Modularity: Clear separation of responsibilities across modules

Maintainability: Readable, predictable code layout

Security: Credentials are never stored; prompted each run

Extensibility: New operations can be added easily

Accuracy: Validation for IPv4, subnet masks, integers, and OSPF inputs

The codebase reflects patterns used in practical network automation workflows.

---

## 8. Future Enhancements
Planned improvements may include:

Batch configuration capabilities

Multi-device parallel execution

Additional troubleshooting commands

Integration with structured inventories (e.g., YAML groups)

Support for configuration templating

---

## 9. License
This project is available for educational and non-commercial use.
