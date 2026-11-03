#!/usr/bin/env python3
"""
Kali Linux MCP Server
Exposes Kali Linux penetration testing, reconnaissance, enumeration, and terminal capabilities
to LLMs via the Model Context Protocol (MCP).
"""

import os
import sys
import shlex
import subprocess
import tempfile
import logging
from typing import Optional

# Setup logging to stderr so stdout is reserved for JSON-RPC MCP messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("kali-mcp")

try:
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer("KaliLinuxMCP")
except (ImportError, ModuleNotFoundError):
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("KaliLinuxMCP")

WORKSPACE_DIR = os.environ.get("KALI_WORKSPACE", "/workspace")


def run_command(cmd: list[str] | str, timeout: int = 300, cwd: str = WORKSPACE_DIR) -> str:
    """Execute a command safely with timeout handling and formatted output."""
    try:
        if isinstance(cmd, str):
            logger.info("Executing bash string: %s (cwd=%s, timeout=%ds)", cmd, cwd, timeout)
            res = subprocess.run(
                cmd,
                shell=True,
                executable="/bin/bash",
                cwd=cwd if os.path.isdir(cwd) else None,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        else:
            logger.info("Executing cmd list: %s (cwd=%s, timeout=%ds)", " ".join(cmd), cwd, timeout)
            res = subprocess.run(
                cmd,
                cwd=cwd if os.path.isdir(cwd) else None,
                capture_output=True,
                text=True,
                timeout=timeout
            )

        output = res.stdout
        if res.stderr:
            output += f"\n[stderr]:\n{res.stderr}"
        if res.returncode != 0:
            output += f"\n[Process exited with code {res.returncode}]"

        return output if output.strip() else "[Command executed successfully with no output]"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except FileNotFoundError as e:
        return f"Error: Binary not found: {e}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


# ==============================================================================
# 1. GENERAL COMMAND EXECUTION & SYSTEM TOOLS
# ==============================================================================

@mcp.tool()
def kali_exec(command: str, cwd: str = "/workspace", timeout: int = 300) -> str:
    """
    Execute any arbitrary bash command inside the Kali Linux environment.
    Use this for complex pipelines, interactive tools, scripting, or utilities without dedicated tools.
    """
    return run_command(command, timeout=timeout, cwd=cwd)


@mcp.tool()
def kali_system_info() -> str:
    """
    Get detailed information about the Kali Linux container:
    kernel version, architecture, network interfaces, memory/disk usage, and installed tool availability.
    """
    script = """
    echo "=== OS & Kernel ==="
    cat /etc/os-release | grep -E 'PRETTY_NAME|VERSION='
    uname -a
    echo ""
    echo "=== Network Interfaces ==="
    ip -br a 2>/dev/null || ifconfig -s 2>/dev/null || ip a
    echo ""
    echo "=== Disk & Memory ==="
    df -h / /workspace 2>/dev/null
    free -m 2>/dev/null || cat /proc/meminfo | grep -E 'MemTotal|MemAvailable'
    echo ""
    echo "=== Core Tools Status ==="
    for tool in nmap nikto gobuster ffuf dirb sqlmap hydra john hashcat whatweb whois dig tcpdump searchsploit msfconsole; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo "[✓] $tool: $(command -v $tool)"
        else
            echo "[✗] $tool: not found"
        fi
    done
    """
    return run_command(script, timeout=30)


@mcp.tool()
def kali_install_package(packages: str, timeout: int = 600) -> str:
    """
    Dynamically install Debian/Kali packages inside the running container using apt-get.
    Example: packages='wireshark tshark sublist3r'
    """
    cmd = f"apt-get update && apt-get install -y --no-install-recommends {packages}"
    return run_command(cmd, timeout=timeout)


# ==============================================================================
# 2. FILESYSTEM & WORKSPACE OPERATIONS
# ==============================================================================

@mcp.tool()
def kali_read_file(path: str, max_lines: int = 300) -> str:
    """
    Read the contents of a file inside Kali Linux (e.g. scan logs, configs, output files).
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
            if f.readline():
                content += f"\n... [Output truncated at {max_lines} lines]"
            return content
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


@mcp.tool()
def kali_write_file(path: str, content: str) -> str:
    """
    Write or overwrite text content to a file inside Kali Linux (e.g. scripts, payloads, wordlists, configs).
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{path}'."
    except Exception as e:
        return f"Error writing file '{path}': {str(e)}"


# ==============================================================================
# 3. RECONNAISSANCE & INFORMATION GATHERING
# ==============================================================================

@mcp.tool()
def whois_lookup(target: str, timeout: int = 30) -> str:
    """
    Perform a WHOIS query on an IP address or domain name to discover owner, ASN, and registrar details.
    """
    return run_command(["whois", target], timeout=timeout)


@mcp.tool()
def dns_lookup(domain: str, record_type: str = "ANY", timeout: int = 30) -> str:
    """
    Query DNS records for a domain using dig.
    Record types can be: A, AAAA, MX, TXT, NS, SOA, CNAME, or ANY.
    """
    return run_command(["dig", "+noall", "+answer", domain, record_type], timeout=timeout)


@mcp.tool()
def whatweb_scan(target_url: str, timeout: int = 60) -> str:
    """
    Fingerprint web technologies, CMS, server software, and analytics using WhatWeb.
    """
    return run_command(["whatweb", "-v", target_url], timeout=timeout)


@mcp.tool()
def searchsploit_query(query: str, timeout: int = 60) -> str:
    """
    Query the local Exploit Database archive (SearchSploit) for public exploits matching a software/version.
    """
    return run_command(["searchsploit", query], timeout=timeout)


# ==============================================================================
# 4. NETWORK & PORT SCANNING
# ==============================================================================

@mcp.tool()
def nmap_scan(target: str, flags: str = "-sV -F", timeout: int = 600) -> str:
    """
    Run an Nmap scan against a host or network.
    Flags examples:
      - Quick scan: '-sV -F'
      - Standard ports with service detection: '-sV -sC -p 1-1000'
      - Full TCP scan: '-sS -p-'
      - OS detection + Traceroute: '-A'
    """
    cmd = ["nmap"] + shlex.split(flags) + [target]
    return run_command(cmd, timeout=timeout)


# ==============================================================================
# 5. WEB APPLICATION ENUMERATION & VULNERABILITY SCANNING
# ==============================================================================

@mcp.tool()
def nikto_scan(target_url: str, options: str = "-Tuning 123", timeout: int = 600) -> str:
    """
    Run a Nikto web server vulnerability assessment scan against a target URL.
    """
    cmd = ["nikto", "-h", target_url] + shlex.split(options)
    return run_command(cmd, timeout=timeout)


@mcp.tool()
def gobuster_dir(
    target_url: str,
    wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    additional_args: str = "-q",
    timeout: int = 600
) -> str:
    """
    Perform directory and file brute-forcing using Gobuster.
    """
    cmd = ["gobuster", "dir", "-u", target_url, "-w", wordlist] + shlex.split(additional_args)
    return run_command(cmd, timeout=timeout)


@mcp.tool()
def ffuf_scan(
    target_url: str,
    wordlist: str = "/usr/share/wordlists/dirb/common.txt",
    additional_args: str = "-s",
    timeout: int = 600
) -> str:
    """
    Run FFUF (Fuzz Faster U Fool) for high-performance web fuzzing.
    The target_url must contain the keyword 'FUZZ' (e.g. 'http://example.com/FUZZ').
    """
    cmd = ["ffuf", "-u", target_url, "-w", wordlist] + shlex.split(additional_args)
    return run_command(cmd, timeout=timeout)


@mcp.tool()
def sqlmap_scan(target_url: str, params: str = "--batch --dbs", timeout: int = 600) -> str:
    """
    Run SQLMap to detect and exploit SQL injection vulnerabilities automatically.
    Default runs non-interactively with '--batch --dbs'.
    """
    cmd = ["sqlmap", "-u", target_url] + shlex.split(params)
    return run_command(cmd, timeout=timeout)


# ==============================================================================
# 6. PASSWORD CRACKING & BRUTE FORCING
# ==============================================================================

@mcp.tool()
def hydra_crack(
    target: str,
    service: str,
    user: str,
    wordlist: str = "/usr/share/wordlists/rockyou.txt",
    additional_args: str = "",
    timeout: int = 600
) -> str:
    """
    Run THC-Hydra to test or brute-force network credentials (e.g., ssh, ftp, http-get, smb).
    """
    cmd = ["hydra", "-l", user, "-P", wordlist] + shlex.split(additional_args) + [target, service]
    return run_command(cmd, timeout=timeout)


@mcp.tool()
def john_crack(
    hash_string: str,
    format: str = "",
    wordlist: str = "/usr/share/wordlists/rockyou.txt",
    timeout: int = 600
) -> str:
    """
    Crack a password hash string using John the Ripper.
    Optional format specifies hash format (e.g., 'raw-md5', 'raw-sha256', 'bcrypt').
    """
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(hash_string.strip() + "\n")
        temp_path = f.name

    try:
        cmd = ["john", f"--wordlist={wordlist}"]
        if format:
            cmd.append(f"--format={format}")
        cmd.append(temp_path)
        return run_command(cmd, timeout=timeout)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@mcp.tool()
def hashcat_crack(
    hash_string: str,
    hash_mode: str = "0",
    wordlist: str = "/usr/share/wordlists/rockyou.txt",
    timeout: int = 600
) -> str:
    """
    Crack a password hash using Hashcat.
    hash_mode: 0 (MD5), 1000 (NTLM), 1400 (SHA-256), etc.
    """
    cmd = ["hashcat", "-m", hash_mode, "-a", "0", hash_string, wordlist, "--potfile-disable"]
    return run_command(cmd, timeout=timeout)


# ==============================================================================
# 7. EXPLOITATION & TRAFFIC ANALYSIS
# ==============================================================================

@mcp.tool()
def metasploit_run(commands: str, timeout: int = 600) -> str:
    """
    Execute commands in msfconsole non-interactively using the '-x' flag.
    Example: commands='use auxiliary/scanner/portscan/tcp; set RHOSTS 192.168.1.1; run; exit'
    """
    if "exit" not in commands:
        commands = commands + "; exit"
    cmd = ["msfconsole", "-q", "-x", commands]
    return run_command(cmd, timeout=timeout)


@mcp.tool()
def tcpdump_sniff(
    interface: str = "eth0",
    count: int = 10,
    filter: str = "",
    timeout: int = 30
) -> str:
    """
    Capture a specific number of network packets using tcpdump.
    """
    cmd = ["tcpdump", "-i", interface, "-c", str(count), "-n"]
    if filter:
        cmd.extend(shlex.split(filter))
    return run_command(cmd, timeout=timeout)


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

if __name__ == "__main__":
    logger.info("Starting Kali Linux FastMCP Server over stdio transport...")
    mcp.run(transport="stdio")
