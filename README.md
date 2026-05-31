# Screcon v1.0

A single-command reconnaissance framework integrating:
**Nmap · WPScan · Sublist3r · Recon-ng · DNSenum · DNSrecon · theHarvester · Whois**

> ⚠ **Legal Notice:** Use ONLY on systems you own or have **explicit written permission** to test.
> Unauthorised scanning is illegal in most jurisdictions.

---

## Requirements

| OS | Supported |
|----|-----------|
| Kali Linux | ✅ Recommended |
| Ubuntu 20.04+ | ✅ |
| Debian 11+ | ✅ |
| Windows WSL (Ubuntu) | ✅ |

- Python 3.8+
- Root / sudo (for nmap raw socket scans)
- WPScan API key — **your own key required** (free at https://wpscan.com/register)

---

## Installation

```bash
# Clone or place files in a directory, then:
sudo bash install.sh
```

The installer will:
- Install all tools via apt, gem, and pip
- Place `screcon` in `/usr/local/bin` (available system-wide)
- Verify each tool is working

---

## Usage

### Basic syntax
```bash
screcon -t <target> [options]
```

### Arguments

| Flag | Description | Example |
|------|-------------|---------|
| `-t` | Target (domain, IP, CIDR) | `-t example.com` |
| `-m` | Modules to run | `-m nmap,wpscan,whois` |
| `-n` | Nmap scan profile | `-n full` |
| `-o` | Output directory | `-o /home/user/reports` |
| `--no-html` | Skip HTML report | |
| `--no-json` | Skip JSON report | |
| `--skip-consent` | Skip authorisation prompt | |

### Module names

| Module | Tool | Domain | IP | CIDR |
|--------|------|--------|----|------|
| `nmap` | Nmap | ✅ | ✅ | ✅ |
| `wpscan` | WPScan | ✅ | ❌ | ❌ |
| `sublist3r` | Sublist3r | ✅ | ❌ | ❌ |
| `dnsenum` | DNSenum | ✅ | ❌ | ❌ |
| `dnsrecon` | DNSrecon | ✅ | ❌ | ❌ |
| `whois` | Whois | ✅ | ✅ | ❌ |
| `reconng` | Recon-ng | ✅ | ❌ | ❌ |
| `harvester` | theHarvester | ✅ | ❌ | ❌ |

### Nmap profiles

| Profile | Command | Use case |
|---------|---------|----------|
| `quick` | `-T4 -F` | Fast top-100 ports |
| `full` | `-T4 -A -p-` | All 65535 ports + OS/service detection |
| `stealth` | `-sS -T2 -p-` | SYN scan, slow and quiet |
| `vuln` | `-sV --script=vuln` | Vulnerability scripts |
| `udp` | `-sU --top-ports 100` | Top 100 UDP ports |

---

## Examples

### Full recon on a domain
```bash
screcon -t example.com -m all -n full -o ~/reports
```

### Quick scan — nmap + whois only
```bash
screcon -t example.com -m nmap,whois -n quick
```

### WordPress site audit
```bash
screcon -t example.com -m wpscan,sublist3r,whois
```

### IP address scan
```bash
screcon -t 192.168.1.1 -m nmap,whois -n full
```

### CIDR range scan
```bash
screcon -t 192.168.1.0/24 -m nmap -n quick
```

### DNS-focused recon
```bash
screcon -t example.com -m dnsenum,dnsrecon,sublist3r
```

### Save reports to a specific folder
```bash
screcon -t example.com -m all -o /home/pentester/engagements/client1
```

---

## Output

Each scan creates a timestamped folder:
```
recon_example_com_20250101_120000/
├── recon_report.html    ← Professional dark-theme report (open in browser)
└── recon_report.json    ← Machine-readable structured data
```

Terminal output is live as each module runs.

---

## WPScan API Key

WPScan requires your own API key to fetch vulnerability data.

1. Register free at: https://wpscan.com/register
2. When the tool prompts **"Enter your WPScan API key"**, paste it in
3. Without a key, WPScan still runs but returns limited vulnerability info

---

## Adding New Tools

To extend the tool, add a new function in `screcon.py`:

```python
def run_mytool(target, results):
    section("MYTOOL — Description")
    if not tool_available("mytool"):
        warn("mytool not found.")
        results["mytool"] = {"status": "skipped", "reason": "tool not installed"}
        return
    cmd = f"mytool -target {target}"
    stdout, stderr, rc = run_cmd(cmd, timeout=120)
    for line in stdout.splitlines():
        result(line)
    results["mytool"] = {"command": cmd, "output": stdout, "status": "success" if rc == 0 else "partial"}
```

Then add it to the module runner section in `main()`.

---

## Troubleshooting

**nmap requires root for SYN scans:**
```bash
sudo screcon -t example.com -m nmap -n stealth
```

**sublist3r not in PATH after pip install:**
```bash
pip3 install sublist3r
# or manually:
cd /opt && git clone https://github.com/aboul3la/Sublist3r.git
sudo ln -s /opt/Sublist3r/sublist3r.py /usr/local/bin/sublist3r
```

**wpscan not found:**
```bash
gem install wpscan
# or on Kali:
apt install wpscan
```

**recon-ng modules missing:**
```bash
recon-ng
> marketplace install all
```

---

## Disclaimer

This tool is intended for **authorised penetration testing and security research only**.
The authors accept no responsibility for misuse. Always obtain written permission before scanning any target.
