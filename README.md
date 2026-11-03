# Kali Linux MCP Server (Docker)

An enterprise-ready, containerized [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server providing Large Language Models (LLMs) and AI agents with direct, sandboxed access to Kali Linux penetration testing, reconnaissance, and enumeration capabilities.

---

## Architecture & Features

```
┌───────────────────────────────────────┐
│ AI Client (Antigravity / Claude / etc)│
└──────────────────┬────────────────────┘
                   │ MCP stdio (JSON-RPC)
                   ▼
┌───────────────────────────────────────┐
│        run-mcp.sh Runner              │
│ (Auto-checks/starts Kali container)   │
└──────────────────┬────────────────────┘
                   │ docker exec -i
                   ▼
┌────────────────────────────────────────────────────────┐
│  Docker Container: kali-mcp (kalilinux/kali-rolling)   │
│                                                        │
│  • FastMCP Python Server (/app/server.py)              │
│  • Core Recon: nmap, whois, dig, whatweb, searchsploit │
│  • Web App Pentesting: nikto, gobuster, ffuf, sqlmap   │
│  • Cracking & Bruteforce: hydra, john, hashcat         │
│  • Exploitation: metasploit-framework (msfconsole)     │
│  • Network: tcpdump, netcat, socat                     │
│  • Terminal: kali_exec (arbitrary bash command runner) │
│  • Package Manager: kali_install_package (dynamic apt) │
│                                                        │
│  Mounted Volume: ./workspace -> /workspace             │
└────────────────────────────────────────────────────────┘
```

### Available MCP Tools

| Tool | Category | Description |
| :--- | :--- | :--- |
| `kali_exec` | Terminal | Execute arbitrary bash commands, pipelines, and scripts inside Kali. |
| `kali_system_info` | Diagnostic | View Kali OS version, kernel, network interfaces, and installed tool status. |
| `kali_install_package` | Package Manager | Install Debian/Kali packages dynamically with `apt-get` on demand. |
| `kali_read_file` | Filesystem | Read file contents from inside the Kali filesystem or `/workspace`. |
| `kali_write_file` | Filesystem | Write scripts, wordlists, payloads, or configs inside the container. |
| `nmap_scan` | Network Scan | Perform port scans, version detection, OS fingerprinting, and script scans. |
| `nikto_scan` | Web Vulnerability | Scan web servers for known vulnerabilities, dangerous files, and misconfigurations. |
| `gobuster_dir` | Directory Brute-Force | Brute-force web directories and filenames using wordlists. |
| `ffuf_scan` | Web Fuzzing | Fast web fuzzer supporting parameter and directory discovery with `FUZZ`. |
| `sqlmap_scan` | Database Injection | Automated detection and exploitation of SQL injection vulnerabilities. |
| `whois_lookup` | Reconnaissance | Query domain and IP ownership, registrant, and ASN information. |
| `dns_lookup` | DNS Intelligence | Query DNS records (`A`, `MX`, `TXT`, `NS`, `SOA`, `ANY`) via `dig`. |
| `whatweb_scan` | Web Fingerprinting | Detect CMS, web servers, embedded analytics, and tech stack versions. |
| `searchsploit_query` | Exploit DB | Query the local Exploit Database for public vulnerabilities and exploits. |
| `hydra_crack` | Network Brute-Force | Brute-force credentials over SSH, FTP, HTTP, SMB, and other services. |
| `john_crack` | Hash Cracking | Crack inline password hashes using John the Ripper and wordlists. |
| `hashcat_crack` | Hash Cracking | Crack password hashes using Hashcat with specified hash modes. |
| `metasploit_run` | Exploitation | Run Metasploit Framework commands and modules via `msfconsole -x`. |
| `tcpdump_sniff` | Traffic Capture | Capture network traffic packets on container interfaces. |

---

## Getting Started

### Prerequisites
- Docker Engine or Docker Desktop running on macOS or Linux.
- `NET_RAW` / `NET_ADMIN` capabilities (enabled by default in runner).

### Installation & Build

1. Clone or navigate to the repository:
   ```bash
   cd /Users/jtbeers/Code/kali-mcp
   ```

2. Build the Docker container image:
   ```bash
   docker build -t kali-mcp:latest .
   ```

3. Test running the MCP server directly:
   ```bash
   ./run-mcp.sh
   ```

---

## MCP Client Configuration

### 1. Google Antigravity (`~/.gemini/antigravity-cli/mcp_config.json`)
Add `kali` to `mcpServers`:
```json
{
  "mcpServers": {
    "kali": {
      "command": "/Users/jtbeers/Code/kali-mcp/run-mcp.sh"
    }
  }
}
```

### 2. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "kali": {
      "command": "/Users/jtbeers/Code/kali-mcp/run-mcp.sh"
    }
  }
}
```

### 3. Cursor / VS Code / Other MCP Clients
Command: `/Users/jtbeers/Code/kali-mcp/run-mcp.sh`

---

## Persistent Workspace & Files

The directory `./workspace` on the host machine is automatically mounted into `/workspace` inside the Kali container.
Any scan reports, PCAP files, output dumps, or scripts written inside `/workspace` immediately appear on your host machine.

---

## Interactive Shell Access

To open an interactive bash shell in the running Kali container at any time:
```bash
docker exec -it kali-mcp bash
```

---

## Security Disclaimer

This software is intended for educational, CTF, and authorized security assessment purposes only. Never execute scans or exploits against targets without explicit, documented permission from the target owner.
