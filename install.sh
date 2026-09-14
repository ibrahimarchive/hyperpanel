#!/bin/bash
# ══════════════════════════════════════════════════════════════
# HyperPanel — Automated 1-Command Installation Script
# Supports Ubuntu 22.04 / 24.04 LTS & Debian 11 / 12
# ══════════════════════════════════════════════════════════════

set -eo pipefail

# Non-interactive apt frontend
export DEBIAN_FRONTEND=noninteractive

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PANEL_DIR="${PANEL_DIR:-/opt/hyperpanel}"
PANEL_USER="${PANEL_USER:-hyperpanel}"
PANEL_PORT="${PANEL_PORT:-8443}"
PYTHON_VERSION="python3"

# Repository settings (can be overridden via environment variables)
REPO_URL="${REPO_URL:-https://github.com/ibrahimarchive/hyperpanel.git}"
BRANCH="${BRANCH:-main}"

echo -e "${CYAN}${BOLD}"
cat << 'EOF'
  ╦ ╦┬ ┬┌─┐┌─┐┬─┐╔═╗┌─┐┌┐┌┌─┐┬  
  ╠═╣└┬┘├─┘├┤ ├┬┘╠═╝├─┤│││├┤ │  
  ╩ ╩ ┴ ┴  └─┘┴└─╩  ┴ ┴┘└┘└─┘┴─┘
EOF
echo -e "${NC}"
echo -e "${BOLD}  Modern Server Control Panel — v1.0.0${NC}"
echo "  ──────────────────────────────────────────"
echo ""

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root:${NC}"
    echo -e "  sudo bash $0"
    echo -e "  or: curl -fsSL https://raw.githubusercontent.com/ibrahimarchive/hyperpanel/main/install.sh | sudo bash"
    exit 1
fi

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    echo -e "${RED}Error: Cannot detect OS release.${NC}"
    exit 1
fi

if [ "$OS" != "ubuntu" ] && [ "$OS" != "debian" ]; then
    echo -e "${RED}Error: Only Ubuntu and Debian are supported at this time.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ OS detected: $PRETTY_NAME${NC}"

# ── Step 1: Install system packages ──────────────────────
echo -e "\n${BLUE}[1/7] Installing required system packages...${NC}"

# Auto-repair any previously interrupted dpkg or apt operations
dpkg --configure -a 2>/dev/null || true
apt-get install -f -y -qq 2>/dev/null || true

apt-get update -qq

# Detect MySQL or MariaDB package available in distribution via simulation
DB_PKG=""
if [ "$OS" = "debian" ]; then
    if apt-get install -s default-mysql-server &>/dev/null; then
        DB_PKG="default-mysql-server"
    elif apt-get install -s mariadb-server &>/dev/null; then
        DB_PKG="mariadb-server"
    fi
else
    if apt-get install -s mysql-server &>/dev/null; then
        DB_PKG="mysql-server"
    elif apt-get install -s default-mysql-server &>/dev/null; then
        DB_PKG="default-mysql-server"
    elif apt-get install -s mariadb-server &>/dev/null; then
        DB_PKG="mariadb-server"
    fi
fi

if [ -z "$DB_PKG" ]; then
    DB_PKG="default-mysql-server"
fi

apt-get install -y -qq \
    curl \
    wget \
    git \
    rsync \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    nginx \
    "$DB_PKG" \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    ca-certificates

# Install Certbot & UFW (attempt installation, continue if satisfied)
apt-get install -y -qq certbot python3-certbot-nginx ufw 2>/dev/null || true

echo -e "${GREEN}✓ Core system packages installed (${DB_PKG})${NC}"

# ── Step 2: Install PHP runtime & extensions ─────────────
echo -e "\n${BLUE}[2/7] Installing PHP runtime and extensions...${NC}"
if [ "$OS" = "ubuntu" ]; then
    apt-get install -y -qq software-properties-common 2>/dev/null || true
    add-apt-repository -y ppa:ondrej/php 2>/dev/null || true
    apt-get update -qq
fi

# Try installing PHP 8.2; fallback to default php-fpm if not found
if apt-get install -s php8.2-fpm &>/dev/null && apt-get install -y -qq \
    php8.2-fpm php8.2-cli php8.2-mysql php8.2-curl php8.2-gd \
    php8.2-mbstring php8.2-xml php8.2-zip php8.2-bcmath php8.2-intl 2>/dev/null; then
    PHP_SVC="php8.2-fpm"
    echo -e "${GREEN}✓ PHP 8.2 installed${NC}"
else
    apt-get install -y -qq \
        php-fpm php-cli php-mysql php-curl php-gd \
        php-mbstring php-xml php-zip php-bcmath php-intl 2>/dev/null || \
    apt-get install -y -qq php-fpm php-cli php-mysql php-curl php-gd php-mbstring php-xml php-zip
    PHP_SVC=$(systemctl list-unit-files 'php*-fpm.service' 2>/dev/null | grep -o 'php[0-9.]*-fpm' | head -1 || echo "php-fpm")
    echo -e "${GREEN}✓ Default PHP installed (${PHP_SVC})${NC}"
fi

# Install WP-CLI (Official WordPress Command Line Manager)
if ! command -v wp &>/dev/null; then
    curl -sSL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp 2>/dev/null && chmod +x /usr/local/bin/wp || true
fi

# ── Step 3: Configure panel user & sudoers ───────────────
echo -e "\n${BLUE}[3/7] Setting up dedicated '${PANEL_USER}' user...${NC}"
if ! id "$PANEL_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$PANEL_DIR" "$PANEL_USER"
fi

# Grant hyperpanel passwordless sudo for service management
cat > /etc/sudoers.d/hyperpanel << EOF
# HyperPanel service management permissions
$PANEL_USER ALL=(ALL) NOPASSWD: ALL
EOF
chmod 0440 /etc/sudoers.d/hyperpanel

echo -e "${GREEN}✓ User '${PANEL_USER}' configured with sudo permissions${NC}"

# ── Step 4: Acquire HyperPanel source code ────────────────
echo -e "\n${BLUE}[4/7] Deploying HyperPanel source to ${PANEL_DIR}...${NC}"

# Detect if script was invoked from within a cloned repo or piped via curl
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
IS_LOCAL=false

if [ -f "$SCRIPT_DIR/backend/requirements.txt" ]; then
    IS_LOCAL=true
    SRC_DIR="$SCRIPT_DIR"
elif [ -f "$(pwd)/backend/requirements.txt" ]; then
    IS_LOCAL=true
    SRC_DIR="$(pwd)"
fi

mkdir -p "$PANEL_DIR"

if [ "$IS_LOCAL" = true ]; then
    echo -e "  Copying local workspace from: ${SRC_DIR}"
    rsync -a \
        --exclude 'venv/' \
        --exclude '.venv/' \
        --exclude 'backend/venv/' \
        --exclude '.env' \
        --exclude 'hyperpanel.db' \
        --exclude 'backend/hyperpanel.db' \
        --exclude '__pycache__/' \
        --exclude '.git/' \
        "$SRC_DIR/" "$PANEL_DIR/"
else
    echo -e "  Downloading from repository: ${REPO_URL} (${BRANCH})"
    if [ -d "$PANEL_DIR/.git" ]; then
        cd "$PANEL_DIR"
        git fetch origin "$BRANCH"
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        rm -rf "${PANEL_DIR:?}"/*
        git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$PANEL_DIR"
    fi
fi

# ── Step 5: Python environment & dependencies ───────────
echo -e "\n${BLUE}[5/7] Setting up Python virtual environment...${NC}"
cd "$PANEL_DIR/backend"

if [ ! -d "venv" ]; then
    $PYTHON_VERSION -m venv venv
fi

./venv/bin/pip install --upgrade pip setuptools wheel -q
./venv/bin/pip install -r requirements.txt -q

# Setup .env if not exists
if [ ! -f "$PANEL_DIR/backend/.env" ]; then
    cp .env.example .env
    SECRET_KEY=$(./venv/bin/python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/change-me-to-a-random-64-char-string/$SECRET_KEY/" .env
    sed -i "s/PANEL_PORT=8443/PANEL_PORT=$PANEL_PORT/" .env
fi

# Pre-initialize database & default admin user
./venv/bin/python3 -c "import asyncio
from app.database import init_db, async_session
from app.services.auth_service import create_admin_user

async def init():
    await init_db()
    async with async_session() as s:
        await create_admin_user(s)
        await s.commit()

asyncio.run(init())"

# Generate initial self-signed SSL certificate for panel
mkdir -p "$PANEL_DIR/ssl"
./venv/bin/python3 -c "
from app.services.panel_settings_service import panel_settings_service
panel_settings_service.generate_self_signed_cert('127.0.0.1')
" 2>/dev/null || true

echo -e "${GREEN}✓ Python environment, database, and SSL initialized${NC}"

# ── Step 6: Create system directories & permissions ─────
echo -e "\n${BLUE}[6/7] Configuring services and system directories...${NC}"

mkdir -p /var/www
mkdir -p /var/hyperpanel/backups
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Remove default nginx welcome site if present to avoid port 80 conflicts
rm -f /etc/nginx/sites-enabled/default

chown -R "$PANEL_USER:$PANEL_USER" "$PANEL_DIR"
chown -R "$PANEL_USER:$PANEL_USER" /var/hyperpanel
chown -R "$PANEL_USER:www-data" /var/www
chmod 755 "$PANEL_DIR"

# Configure Nginx reverse proxy for HyperPanel on PANEL_PORT with SSL & HTTP auto-redirect
cat > /etc/nginx/sites-available/hyperpanel.conf << EOF
# HyperPanel Management Server — Nginx Proxy
server {
    listen $PANEL_PORT ssl default_server;
    server_name _;

    ssl_certificate $PANEL_DIR/ssl/panel.crt;
    ssl_certificate_key $PANEL_DIR/ssl/panel.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    error_page 497 301 = https://\$host:\$server_port\$request_uri;

    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/hyperpanel.conf /etc/nginx/sites-enabled/hyperpanel.conf

# Enable and start auxiliary services
systemctl enable --now nginx 2>/dev/null || true
systemctl enable --now mysql 2>/dev/null || systemctl enable --now mariadb 2>/dev/null || true
if systemctl list-unit-files | grep -q "$PHP_SVC"; then
    systemctl enable --now "$PHP_SVC" 2>/dev/null || true
fi

# Configure UFW
if command -v ufw &>/dev/null; then
    if ufw status 2>/dev/null | grep -qw "inactive"; then
        ufw allow 22/tcp comment 'SSH' || true
        ufw allow 80/tcp comment 'HTTP' || true
        ufw allow 443/tcp comment 'HTTPS' || true
        ufw allow "$PANEL_PORT/tcp" comment 'HyperPanel' || true
        ufw --force enable || true
    else
        ufw allow 22/tcp || true
        ufw allow 80/tcp || true
        ufw allow 443/tcp || true
        ufw allow "$PANEL_PORT/tcp" || true
    fi
fi

# Create systemd service for HyperPanel (Internal ASGI binding to 127.0.0.1:8000)
cat > /etc/systemd/system/hyperpanel.service << EOF
[Unit]
Description=HyperPanel — Server Control Panel
After=network.target mysql.service mariadb.service nginx.service

[Service]
Type=simple
User=$PANEL_USER
Group=$PANEL_USER
WorkingDirectory=$PANEL_DIR/backend
Environment="PATH=$PANEL_DIR/backend/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$PANEL_DIR/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hyperpanel
systemctl restart hyperpanel
nginx -t && systemctl reload nginx 2>/dev/null || true
sleep 2

if systemctl is-active --quiet hyperpanel; then
    echo -e "${GREEN}✓ HyperPanel service created and running${NC}"
else
    echo -e "${YELLOW}! HyperPanel service started. If it takes a few seconds, verify with: systemctl status hyperpanel${NC}"
fi

# ── Step 7: Installation Summary ─────────────────────────
IP_ADDR=$(curl -s -4 --max-time 3 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}       ✅ HyperPanel Installed Successfully!${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Panel URL:${NC}      ${YELLOW}https://${IP_ADDR}:${PANEL_PORT}${NC}"
echo -e "  ${BOLD}Local URL:${NC}      ${YELLOW}https://127.0.0.1:${PANEL_PORT}${NC}"
echo -e "  ${BOLD}Username:${NC}       ${CYAN}admin${NC}"
echo -e "  ${BOLD}Password:${NC}       ${CYAN}changeme${NC}"
echo ""
echo -e "  ${RED}${BOLD}Important:${NC} Change the default administrator password after sign in!"
echo ""
echo -e "  ${BOLD}Service commands:${NC}"
echo -e "    systemctl status hyperpanel   # Check service status"
echo -e "    systemctl restart hyperpanel  # Restart panel"
echo -e "    journalctl -u hyperpanel -f   # View live logs"
echo -e "${CYAN}══════════════════════════════════════════════════════════${NC}"
echo ""
