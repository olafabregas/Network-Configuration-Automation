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

