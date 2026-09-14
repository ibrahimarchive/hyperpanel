#!/bin/bash
# ══════════════════════════════════════════════════════════════
# HyperPanel — Official Release Self-Update Script
# ══════════════════════════════════════════════════════════════

set -eo pipefail

PANEL_DIR="${PANEL_DIR:-/opt/hyperpanel}"
REPO_API="https://api.github.com/repos/ibrahimarchive/hyperpanel/releases/latest"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
cat << 'EOF'
  ╦ ╦┬ ┬┌─┐┌─┐┬─┐╔═╗┌─┐┌┐┌┌─┐┬  
  ╠═╣└┬┘├─┘├┤ ├┬┘╠═╝├─┤│││├┤ │  
  ╩ ╩ ┴ ┴  └─┘┴└─╩  ┴ ┴┘└┘└─┘┴─┘
EOF
echo -e "${NC}"
echo -e "${BOLD}  HyperPanel Official Release Updater${NC}"
echo "  ──────────────────────────────────────────"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root:${NC} sudo bash $0"
    exit 1
fi

TARGET_TAG="$1"

if [ -z "$TARGET_TAG" ]; then
    echo -e "Checking latest official release from GitHub..."
    LATEST_TAG=$(curl -s --max-time 5 "$REPO_API" | grep '"tag_name":' | head -1 | cut -d '"' -f 4 || true)
    if [ -n "$LATEST_TAG" ]; then
        TARGET_TAG="$LATEST_TAG"
        echo -e "${GREEN}✓ Latest release found: ${BOLD}${TARGET_TAG}${NC}"
    else
        echo -e "${YELLOW}! No official GitHub release tags found. Updating to latest on main branch...${NC}"
    fi
fi

cd "$PANEL_DIR"

echo -e "\n${CYAN}[1/4] Fetching latest tags and commits...${NC}"
git fetch --tags --force origin
git fetch --force origin main

if [ -n "$TARGET_TAG" ]; then
    echo -e "\n${CYAN}[2/4] Checking out release ${TARGET_TAG}...${NC}"
    git checkout -B "$TARGET_TAG" "tags/$TARGET_TAG" 2>/dev/null || git checkout -B "$TARGET_TAG" "$TARGET_TAG" 2>/dev/null || git reset --hard origin/main
else
    echo -e "\n${CYAN}[2/4] Pulling latest main...${NC}"
    git checkout -B main origin/main
    git reset --hard origin/main
fi

chmod +x install.sh update.sh 2>/dev/null || true

echo -e "\n${CYAN}[3/4] Updating Python dependencies & database...${NC}"
if [ -d "$PANEL_DIR/backend/venv" ]; then
    ./backend/venv/bin/pip install -r backend/requirements.txt -q
    ./backend/venv/bin/python3 -c "import asyncio; from app.database import init_db; asyncio.run(init_db())" 2>/dev/null || true
    ./backend/venv/bin/python3 -c "import asyncio; from app.services.panel_settings_service import panel_settings_service; asyncio.run(panel_settings_service.sync_nginx_config())" 2>/dev/null || true
fi

echo -e "\n${CYAN}[4/4] Reloading Nginx and restarting HyperPanel service...${NC}"
nginx -t && systemctl reload nginx 2>/dev/null || true
if systemctl is-active --quiet hyperpanel; then
    systemctl restart hyperpanel
    echo -e "${GREEN}✓ HyperPanel service restarted successfully${NC}"
else
    echo -e "${YELLOW}! HyperPanel systemd service is not currently running. Starting...${NC}"
    systemctl start hyperpanel || true
fi

echo ""
echo -e "${GREEN}${BOLD}✅ HyperPanel update complete!${NC}"
