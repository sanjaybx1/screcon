#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║              UNIFIED SCRECON v1.0                         ║
║   Integrates: Nmap · WPScan · Sublist3r · Recon-ng           ║
║              DNSenum · DNSrecon · Whois · Shodan             ║
║   Use ONLY on systems you own or have written permission      ║
╚══════════════════════════════════════════════════════════════╝
"""

import argparse
import subprocess
import sys
import os
import json
import datetime
import shutil
import re
import ipaddress
from pathlib import Path

# ─────────────────────────────────────────────
#  COLORS (terminal)
# ─────────────────────────────────────────────
class C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"
    MAGENTA = "\033[95m"

BANNER = f"""
{C.CYAN}{C.BOLD}
 ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗    ████████╗ ██████╗  ██████╗ ██╗     
 ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     
 ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║       ██║   ██║   ██║██║   ██║██║     
 ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║       ██║   ██║   ██║██║   ██║██║     
 ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║       ██║   ╚██████╔╝╚██████╔╝███████╗
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
{C.RESET}{C.DIM}                  Screcon — Unified Reconnaissance Framework v1.0
            Nmap · WPScan · Sublist3r · Recon-ng · DNSenum · DNSrecon
{C.RESET}"""

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def banner():
    print(BANNER)
    print(f"{C.RED}{C.BOLD}  ⚠  LEGAL NOTICE: Use ONLY on systems you own or have explicit written permission to test.{C.RESET}\n")

def section(title):
    width = 60
    print(f"\n{C.CYAN}{C.BOLD}{'─'*width}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}  {title}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}{'─'*width}{C.RESET}")

def info(msg):    print(f"{C.BLUE}[*]{C.RESET} {msg}")
def success(msg): print(f"{C.GREEN}[+]{C.RESET} {msg}")
def warn(msg):    print(f"{C.YELLOW}[!]{C.RESET} {msg}")
def error(msg):   print(f"{C.RED}[-]{C.RESET} {msg}")
def result(msg):  print(f"{C.WHITE}    {msg}{C.RESET}")

def tool_available(name):
    return shutil.which(name) is not None

def run_cmd(cmd, timeout=300):
    """Run a shell command and return (stdout, stderr, returncode)."""
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def validate_target(target):
    """Validate target is domain, IP, or CIDR."""
    # Try IP
    try:
        ipaddress.ip_address(target)
        return "ip"
    except ValueError:
        pass
    # Try CIDR
    try:
        ipaddress.ip_network(target, strict=False)
        return "cidr"
    except ValueError:
        pass
    # Try domain
    domain_re = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    )
    if domain_re.match(target):
        return "domain"
    return None

def consent_check(target):
    print(f"\n{C.RED}{C.BOLD}  AUTHORISATION CHECK{C.RESET}")
    print(f"  Target : {C.YELLOW}{target}{C.RESET}")
    print(f"  You must have explicit written permission to scan this target.")
    ans = input(f"\n  Do you confirm you are authorised to test {C.YELLOW}{target}{C.RESET}? [yes/no]: ").strip().lower()
    if ans != "yes":
        print(f"\n{C.RED}  Aborted. Always obtain written permission before scanning.{C.RESET}\n")
        sys.exit(0)

# ─────────────────────────────────────────────
#  MODULE RUNNERS
# ─────────────────────────────────────────────

def run_nmap(target, mode, results):
    section("NMAP — Port & Service Scan")
    profiles = {
        "quick":  f"nmap -T4 -F {target}",
        "full":   f"nmap -T4 -A -p- {target}",
        "stealth":f"nmap -sS -T2 -p- {target}",
        "vuln":   f"nmap -sV --script=vuln {target}",
        "udp":    f"nmap -sU --top-ports 100 {target}",
    }
    cmd = profiles.get(mode, profiles["quick"])
    info(f"Running: {cmd}")
    stdout, stderr, rc = run_cmd(cmd, timeout=600)
    if rc == 0 and stdout:
        for line in stdout.splitlines():
            result(line)
        results["nmap"] = {"command": cmd, "output": stdout, "status": "success"}
        success("Nmap scan complete.")
    else:
        error(f"Nmap failed or no output. {stderr[:200]}")
        results["nmap"] = {"command": cmd, "output": stderr, "status": "failed"}

def run_wpscan(target, api_key, results):
    section("WPSCAN — WordPress Vulnerability Scanner")
    if not tool_available("wpscan"):
        warn("wpscan not found. Install: gem install wpscan")
        results["wpscan"] = {"status": "skipped", "reason": "tool not installed"}
        return
    cmd = f"wpscan --url {target} --api-token {api_key} --enumerate vp,vt,u --random-user-agent"
    info(f"Running: wpscan --url {target} --api-token [REDACTED] --enumerate vp,vt,u")
    stdout, stderr, rc = run_cmd(cmd, timeout=300)
    clean_out = stdout or stderr
    for line in clean_out.splitlines():
        result(line)
    status = "success" if rc == 0 else "partial"
    results["wpscan"] = {"command": f"wpscan --url {target} --enumerate vp,vt,u", "output": clean_out, "status": status}
    success("WPScan complete.")

def run_sublist3r(target, results):
    section("SUBLIST3R — Subdomain Enumeration")
    if not tool_available("sublist3r"):
        warn("sublist3r not found. Install: pip install sublist3r")
        results["sublist3r"] = {"status": "skipped", "reason": "tool not installed"}
        return
    out_file = f"/tmp/sublist3r_{target}.txt"
    cmd = f"sublist3r -d {target} -o {out_file}"
    info(f"Running: {cmd}")
    stdout, stderr, rc = run_cmd(cmd, timeout=300)
    subdomains = []
    if os.path.exists(out_file):
        with open(out_file) as f:
            subdomains = [l.strip() for l in f if l.strip()]
        os.remove(out_file)
    for line in (stdout or stderr).splitlines():
        result(line)
    results["sublist3r"] = {"command": cmd, "subdomains": subdomains, "output": stdout, "status": "success" if rc == 0 else "partial"}
    success(f"Sublist3r found {len(subdomains)} subdomains.")

def run_dnsenum(target, results):
    section("DNSENUM — DNS Enumeration")
    if not tool_available("dnsenum"):
        warn("dnsenum not found. Install: apt install dnsenum")
        results["dnsenum"] = {"status": "skipped", "reason": "tool not installed"}
        return
    cmd = f"dnsenum --noreverse {target}"
    info(f"Running: {cmd}")
    stdout, stderr, rc = run_cmd(cmd, timeout=300)
    for line in (stdout or stderr).splitlines():
        result(line)
    results["dnsenum"] = {"command": cmd, "output": stdout or stderr, "status": "success" if rc == 0 else "partial"}
    success("DNSenum complete.")

def run_dnsrecon(target, results):
    section("DNSRECON — DNS Reconnaissance")
    if not tool_available("dnsrecon"):
        warn("dnsrecon not found. Install: apt install dnsrecon")
        results["dnsrecon"] = {"status": "skipped", "reason": "tool not installed"}
        return
    cmd = f"dnsrecon -d {target} -t std,brt,axfr"
    info(f"Running: {cmd}")
    stdout, stderr, rc = run_cmd(cmd, timeout=300)
    for line in (stdout or stderr).splitlines():
        result(line)
    results["dnsrecon"] = {"command": cmd, "output": stdout or stderr, "status": "success" if rc == 0 else "partial"}
    success("DNSrecon complete.")

def run_whois(target, results):
    section("WHOIS — Domain Registration Info")
    if not tool_available("whois"):
        warn("whois not found. Install: apt install whois")
        results["whois"] = {"status": "skipped", "reason": "tool not installed"}
        return
    cmd = f"whois {target}"
    info(f"Running: {cmd}")
    stdout, stderr, rc = run_cmd(cmd, timeout=60)
    for line in (stdout or "").splitlines()[:40]:
        result(line)
    results["whois"] = {"command": cmd, "output": stdout, "status": "success" if rc == 0 else "partial"}
    success("WHOIS complete.")

def run_reconng(target, results):
    section("RECON-NG — OSINT Framework")
    if not tool_available("recon-ng"):
        warn("recon-ng not found. Install: apt install recon-ng")
        results["screcon_ng"] = {"status": "skipped", "reason": "tool not installed"}
        return
    rc_script = f"""marketplace install all
workspaces create screcon_{target.replace('.','_')}
modules load recon/domains-hosts/hackertarget
options set SOURCE {target}
run
show hosts
exit
"""
    script_path = f"/tmp/reconng_{target}.rc"
    with open(script_path, "w") as f:
        f.write(rc_script)
    cmd = f"recon-ng -r {script_path}"
    info(f"Running recon-ng with hackertarget module on {target}")
    stdout, stderr, rc = run_cmd(cmd, timeout=300)
    if os.path.exists(script_path):
        os.remove(script_path)
    for line in (stdout or "").splitlines():
        result(line)
    results["screcon_ng"] = {"command": cmd, "output": stdout or stderr, "status": "success" if rc == 0 else "partial"}
    success("Recon-ng complete.")

def run_theHarvester(target, results):
    section("THEHARVESTER — Email & OSINT Harvesting")
    tool = "theHarvester" if tool_available("theHarvester") else ("theharvester" if tool_available("theharvester") else None)
    if not tool:
        warn("theHarvester not found. Install: apt install theharvester")
        results["theharvester"] = {"status": "skipped", "reason": "tool not installed"}
        return
    cmd = f"{tool} -d {target} -b all -l 200"
    info(f"Running: {cmd}")
    stdout, stderr, rc = run_cmd(cmd, timeout=300)
    for line in (stdout or "").splitlines():
        result(line)
    results["theharvester"] = {"command": cmd, "output": stdout or stderr, "status": "success" if rc == 0 else "partial"}
    success("theHarvester complete.")

# ─────────────────────────────────────────────
#  OUTPUT WRITERS
# ─────────────────────────────────────────────

def write_json(results, out_dir):
    path = out_dir / "screcon_report.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    success(f"JSON report saved → {path}")

def write_html(results, out_dir, target):
    ts = results.get("meta", {}).get("timestamp", "")
    modules = {k: v for k, v in results.items() if k != "meta"}

    def badge(status):
        colors = {"success": "#22c55e", "partial": "#f59e0b", "failed": "#ef4444", "skipped": "#6b7280"}
        color = colors.get(status, "#6b7280")
        return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;">{status.upper()}</span>'

    def module_card(name, data):
        status = data.get("status", "unknown")
        output = data.get("output", data.get("reason", ""))
        cmd = data.get("command", "")
        subdomains = data.get("subdomains", [])
        sd_html = ""
        if subdomains:
            sd_html = "<ul style='margin:8px 0 0 0;padding-left:18px;'>" + "".join(f"<li>{s}</li>" for s in subdomains) + "</ul>"
        out_html = ""
        if output:
            safe = output.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            out_html = f'<pre style="background:#0f172a;color:#94a3b8;padding:12px;border-radius:8px;font-size:12px;overflow-x:auto;max-height:400px;overflow-y:auto;">{safe}</pre>'
        cmd_html = f'<code style="font-size:12px;color:#94a3b8;">{cmd}</code>' if cmd else ""
        return f"""
        <div style="background:#1e293b;border-radius:12px;padding:20px;margin-bottom:16px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <h3 style="margin:0;color:#f1f5f9;font-size:16px;font-family:monospace;">{name.upper()}</h3>
            {badge(status)}
          </div>
          {cmd_html}
          {sd_html}
          {out_html}
        </div>"""

    cards_html = "".join(module_card(k, v) for k, v in modules.items())

    stats = {
        "Total Modules": len(modules),
        "Successful": sum(1 for v in modules.values() if v.get("status") == "success"),
        "Partial": sum(1 for v in modules.values() if v.get("status") == "partial"),
        "Skipped": sum(1 for v in modules.values() if v.get("status") == "skipped"),
    }

    stat_cards = "".join(f"""
      <div style="background:#0f172a;border-radius:10px;padding:16px 20px;text-align:center;">
        <div style="font-size:28px;font-weight:700;color:#38bdf8;">{v}</div>
        <div style="font-size:13px;color:#94a3b8;margin-top:4px;">{k}</div>
      </div>""" for k, v in stats.items())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recon Report — {target}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0a0f1e; color: #e2e8f0; font-family: 'Segoe UI', system-ui, sans-serif; padding: 40px 20px; }}
  a {{ color: #38bdf8; }}
  code {{ font-family: monospace; }}
</style>
</head>
<body>
<div style="max-width:960px;margin:0 auto;">

  <div style="border-bottom:1px solid #1e293b;padding-bottom:24px;margin-bottom:32px;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
      <div style="background:#38bdf8;width:4px;height:40px;border-radius:2px;"></div>
      <div>
        <h1 style="font-size:26px;font-weight:700;color:#f1f5f9;letter-spacing:-0.5px;">Recon Report</h1>
        <p style="color:#94a3b8;font-size:14px;margin-top:2px;">Target: <span style="color:#38bdf8;font-family:monospace;">{target}</span></p>
      </div>
    </div>
    <p style="color:#475569;font-size:13px;">Generated: {ts} &nbsp;|&nbsp; Tool: Screcon v1.0</p>
    <p style="color:#ef4444;font-size:12px;margin-top:8px;">⚠ This report is confidential. Use only on authorised targets.</p>
  </div>

  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:32px;">
    {stat_cards}
  </div>

  <h2 style="font-size:18px;font-weight:600;color:#f1f5f9;margin-bottom:16px;">Module Results</h2>
  {cards_html}

  <div style="margin-top:40px;padding-top:20px;border-top:1px solid #1e293b;text-align:center;color:#475569;font-size:12px;">
    Unified Screcon v1.0 &nbsp;·&nbsp; For authorised penetration testing only
  </div>
</div>
</body>
</html>"""

    path = out_dir / "screcon_report.html"
    with open(path, "w") as f:
        f.write(html)
    success(f"HTML report saved → {path}")

# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    banner()

    parser = argparse.ArgumentParser(
        prog="screcon",
        description="Screcon — Nmap, WPScan, Sublist3r, Recon-ng, DNSenum, DNSrecon, theHarvester",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-t", "--target",    required=True,  help="Target: domain, IP, or CIDR range")
    parser.add_argument("-m", "--modules",   default="all",  help="Modules to run (comma-separated):\n  all, nmap, wpscan, sublist3r, dnsenum, dnsrecon, whois, reconng, harvester\n  Example: -m nmap,wpscan,whois")
    parser.add_argument("-n", "--nmap-mode", default="quick",help="Nmap profile: quick | full | stealth | vuln | udp  (default: quick)")
    parser.add_argument("-o", "--output",    default=".",    help="Output directory for reports (default: current dir)")
    parser.add_argument("--no-html",         action="store_true", help="Skip HTML report")
    parser.add_argument("--no-json",         action="store_true", help="Skip JSON report")
    parser.add_argument("--skip-consent",    action="store_true", help="Skip authorisation prompt (use carefully)")

    args = parser.parse_args()
    target = args.target.strip()

    # Validate target
    target_type = validate_target(target)
    if not target_type:
        error(f"Invalid target: '{target}'. Provide a domain, IP, or CIDR range.")
        sys.exit(1)

    info(f"Target type detected: {target_type.upper()}")

    # Consent check
    if not args.skip_consent:
        consent_check(target)

    # Determine modules
    all_modules = ["nmap", "wpscan", "sublist3r", "dnsenum", "dnsrecon", "whois", "reconng", "harvester"]
    if args.modules.lower() == "all":
        modules = all_modules
    else:
        modules = [m.strip().lower() for m in args.modules.split(",")]
        invalid = [m for m in modules if m not in all_modules]
        if invalid:
            warn(f"Unknown modules ignored: {invalid}")
        modules = [m for m in modules if m in all_modules]

    # Domain-only tools
    domain_only = {"wpscan", "sublist3r", "dnsenum", "dnsrecon", "reconng", "harvester"}
    if target_type in ("ip", "cidr"):
        skipped = domain_only & set(modules)
        if skipped:
            warn(f"Skipping domain-only modules for IP/CIDR target: {skipped}")
            modules = [m for m in modules if m not in domain_only]

    # WPScan API key
    wpscan_key = None
    if "wpscan" in modules:
        print(f"\n{C.YELLOW}[WPScan]{C.RESET} You need your own WPScan API key.")
        print(f"  Get one free at: {C.CYAN}https://wpscan.com/register{C.RESET}")
        wpscan_key = input("  Enter your WPScan API key (or press Enter to skip): ").strip()
        if not wpscan_key:
            warn("No API key provided. WPScan will run with limited vulnerability data.")
            wpscan_key = ""

    # Output directory
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output) / f"screcon_{target.replace('/', '_').replace('.', '_')}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    info(f"Output directory: {out_dir}")

    # Results structure
    results = {
        "meta": {
            "target": target,
            "target_type": target_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "modules_run": modules,
            "tool": "Screcon v1.0"
        }
    }

    # ── Run modules ──
    section(f"STARTING RECON ON {target}")
    info(f"Modules: {', '.join(modules)}")

    if "nmap"      in modules: run_nmap(target, args.nmap_mode, results)
    if "wpscan"    in modules: run_wpscan(target, wpscan_key, results)
    if "sublist3r" in modules: run_sublist3r(target, results)
    if "dnsenum"   in modules: run_dnsenum(target, results)
    if "dnsrecon"  in modules: run_dnsrecon(target, results)
    if "whois"     in modules: run_whois(target, results)
    if "reconng"   in modules: run_reconng(target, results)
    if "harvester" in modules: run_theHarvester(target, results)

    # ── Write outputs ──
    section("GENERATING REPORTS")
    if not args.no_json: write_json(results, out_dir)
    if not args.no_html: write_html(results, out_dir, target)

    # ── Summary ──
    section("SCAN SUMMARY")
    for mod, data in results.items():
        if mod == "meta":
            continue
        status = data.get("status", "unknown")
        colour = {"success": C.GREEN, "partial": C.YELLOW, "failed": C.RED, "skipped": C.DIM}.get(status, C.WHITE)
        print(f"  {colour}{'●'}{C.RESET}  {mod.upper():15s} {colour}{status.upper()}{C.RESET}")

    print(f"\n{C.GREEN}{C.BOLD}  ✔ Recon complete. Reports saved to: {out_dir}{C.RESET}\n")


if __name__ == "__main__":
    main()
