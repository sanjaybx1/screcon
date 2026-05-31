#!/bin/bash
# ══════════════════════════════════════════════════════════════
#   Unified Screcon — Installer
#   Supports: Kali Linux · Ubuntu · Debian · WSL
# ══════════════════════════════════════════════════════════════

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[*]${RESET} $1"; }
success() { echo -e "${GREEN}[+]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[-]${RESET} $1"; }

echo -e "${CYAN}${BOLD}"
echo "  ┌─────────────────────────────────────────────┐"
echo "  │   Unified Screcon — Installer v1.0       │"
echo "  └─────────────────────────────────────────────┘"
echo -e "${RESET}"

# ── Root check ──
if [ "$EUID" -ne 0 ]; then
    error "Please run as root: sudo bash install.sh"
    exit 1
fi

# ── Update package lists ──
info "Updating package lists..."
apt-get update -qq

# ── APT tools ──
APT_TOOLS=("nmap" "whois" "dnsenum" "dnsrecon" "recon-ng" "theharvester" "python3" "python3-pip" "ruby" "ruby-dev")

info "Installing APT packages..."
for tool in "${APT_TOOLS[@]}"; do
    if dpkg -l "$tool" &>/dev/null; then
        success "$tool already installed"
    else
        info "Installing $tool..."
        apt-get install -y -qq "$tool" && success "$tool installed" || warn "$tool install failed — install manually"
    fi
done

# ── WPScan via gem ──
info "Installing WPScan (Ruby gem)..."
if command -v wpscan &>/dev/null; then
    success "wpscan already installed"
else
    gem install wpscan && success "wpscan installed" || warn "wpscan install failed — install manually: gem install wpscan"
fi

# ── Sublist3r via pip ──
info "Installing Sublist3r (pip)..."
if command -v sublist3r &>/dev/null; then
    success "sublist3r already installed"
else
    pip3 install sublist3r -q && success "sublist3r installed" || {
        warn "pip install failed. Trying from GitHub..."
        cd /opt && git clone https://github.com/aboul3la/Sublist3r.git &>/dev/null
        pip3 install -r /opt/Sublist3r/requirements.txt -q
        ln -sf /opt/Sublist3r/sublist3r.py /usr/local/bin/sublist3r
        success "sublist3r installed from GitHub"
    }
fi

# ── Python deps for screcon.py ──
info "Installing Python dependencies..."
pip3 install requests dnspython -q && success "Python deps installed"

# ── Install screcon itself ──
info "Installing screcon..."
INSTALL_PATH="/usr/local/bin/screcon"
cp "$(dirname "$0")/screcon.py" "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"

# Add shebang fix just in case
sed -i '1s|.*|#!/usr/bin/env python3|' "$INSTALL_PATH"
success "screcon installed at $INSTALL_PATH"

# ── Verify all tools ──
echo ""
echo -e "${CYAN}${BOLD}  ── Tool Verification ──${RESET}"
TOOLS=("nmap" "wpscan" "sublist3r" "dnsenum" "dnsrecon" "whois" "recon-ng" "theharvester")
ALL_OK=true
for t in "${TOOLS[@]}"; do
    if command -v "$t" &>/dev/null; then
        echo -e "  ${GREEN}✔${RESET}  $t"
    else
        echo -e "  ${YELLOW}✗${RESET}  $t ${YELLOW}(not found — install manually)${RESET}"
        ALL_OK=false
    fi
done

echo ""
if $ALL_OK; then
    success "All tools ready!"
else
    warn "Some tools missing — see above. Recon tool will skip unavailable modules."
fi

echo -e "\n${GREEN}${BOLD}  Installation complete!${RESET}"
echo -e "  Run: ${CYAN}screcon -h${RESET} to see usage\n"
