# HyperPanel

A modern, fast, and minimalistic server control panel built with **FastAPI (Python 3.11+)** and a lightweight **vanilla HTML/CSS/JS** SPA frontend.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![OS](https://img.shields.io/badge/os-Ubuntu%20%7C%20Debian-E95420?logo=ubuntu)

---

## ⚡ 1-Command Installation

Run this single command on your clean **Ubuntu (22.04 / 24.04)** or **Debian (11 / 12)** server:

```bash
curl -fsSL https://raw.githubusercontent.com/ibrahimarchive/hyperpanel/main/install.sh | sudo bash
```

*Or using `wget`:*

```bash
wget -qO- https://raw.githubusercontent.com/ibrahimarchive/hyperpanel/main/install.sh | sudo bash
```

> [!NOTE]
> If you have forked or cloned this repository under your own account, set `REPO_URL`:
> ```bash
> REPO_URL="https://github.com/<your-username>/hyperpanel.git" curl -fsSL https://raw.githubusercontent.com/<your-username>/hyperpanel/main/install.sh | sudo -E bash
> ```

### What the 1-Command Installer Does Automatically:
1. Installs Nginx, MySQL Server, Python 3 + venv, Certbot, UFW, PHP-FPM, and core build tools.
2. Creates an isolated `hyperpanel` system user with passwordless `sudo` privileges for system services.
3. Clones the repository to `/opt/hyperpanel` and sets up a dedicated Python virtual environment.
4. Generates a secure cryptographic secret key in `.env`.
5. Pre-initializes the database and provisions the default administrator account.
6. Sets up and enables the `hyperpanel` systemd service (`systemctl enable --now hyperpanel`).
7. Configures UFW firewall rules for SSH (22), HTTP (80), HTTPS (443), and HyperPanel (8443).
8. Prints your server IP and login credentials.

---

## 🔑 Accessing the Panel

Once installation completes, open your browser and navigate to:

```
http://<your-server-ip>:8443
```

- **Default Username:** `admin`
- **Default Password:** `changeme`

> [!IMPORTANT]
> **Change the default password immediately** after signing in from the User Management or Settings tab, and enable Two-Factor Authentication (2FA).

---

## 💡 Lightweight & Modular Architecture

HyperPanel is engineered to be **exceptionally fast and lean**. Unlike legacy monolithic control panels that load dozens of background daemons by default, HyperPanel starts with a minimal footprint (~50MB RAM).

Services such as **Docker Engine**, **BillionMail (Mail Server)**, **Pure-FTPd (FTP Server)**, and **Adminer (Web GUI)** are **100% optional on-demand modules**:
- **Zero background footprint**: No background daemon runs until you explicitly install it from the panel.
- **One-Click Installation**: Install Docker, BillionMail, Pure-FTPd, or Adminer directly from their dedicated panel pages with automated configuration.
- **One-Click Uninstallation**: Cleanly remove any add-on at any time to return your server to its minimal footprint.

---

## ✨ Features

### 🌐 Core Web & Database Hosting
- 📊 **Dashboard** — Real-time CPU, RAM, disk usage, and network bandwidth streaming.
- 🌐 **Website Management** — Nginx virtual hosts for PHP (multiple versions), Node.js, Python apps, and static HTML.
- 🚀 **1-Click WordPress Deployer** — Automated WordPress core download, database provisioning, cryptographically secure `wp-config.php` salt generation, and Nginx PHP-FPM fastcgi vhost setup.
- 🗄️ **Database Management & Adminer** — Full MySQL/MariaDB database and user CRUD with privilege grants, 1-click `.sql` dump export & file import, and optional lightweight single-file Adminer Web GUI.
- 🌍 **Domain & DNS Manager** — Manage primary domains, subdomains, document roots, and DNS records (A, AAAA, CNAME, MX, TXT, SRV).
- 🔒 **SSL/TLS Certificates** — Automated Let's Encrypt certificate issuance and automatic renewal.
- 📁 **File Manager** — Web-based explorer to browse, edit, upload, download, and extract archives.

### 🧩 Modular & Optional Add-ons
- 🐳 **Docker Management** *(Optional)* — Container lifecycle (create, start, stop, restart, delete, live logs), Docker image management (pull, remove), and 1-click Docker Engine install/uninstall.
- 📧 **Mail Server via BillionMail** *(Optional)* — Enterprise email stack (Postfix SMTP, Dovecot IMAP/POP3, Rspamd spam filter, Roundcube Webmail) and email marketing campaign suite with DNS guidance (SPF, DKIM, DMARC, MX) and 1-click install/uninstall.
- 📁 **FTP Accounts via Pure-FTPd** *(Optional)* — Ultra-lightweight (<10MB RAM) virtual FTP/FTPS server with PureDB encrypted users, secure chroot directory jailing, passive port range (30000–30050), and quota limits.
- 🗄️ **Adminer Database Web GUI** *(Optional)* — Fast, ultra-lightweight (<1MB) single-file PHP database management interface with zero background processes.

### 🛡️ Security, DevTools & Operations
- 🌐 **Panel Network & Access** — Bind panel to custom domain or IP, configure custom listening port (`1024–65535`) with automated firewall synchronization.
- 🛡️ **Panel SSL** — HTTPS encryption for the control panel with 10-year certificate generator, custom PEM CRT/KEY import, validity period tracking, and issuer monitoring.
- 🔑 **Authentication & Security** — Manage panel administrator username and password directly with integrated Two-Factor Authentication (2FA / TOTP).
- 🔐 **Two-Factor Authentication (2FA / TOTP)** — RFC 6238 time-based one-time password security for user accounts, QR code onboarding, and login challenge protection.
- 💻 **Web Terminal** — Secure in-browser root shell access powered by xterm.js via WebSocket PTY connection.
- 🛡️ **Firewall (UFW)** — View active rules, open/close ports, and toggle firewall status with one click.
- 🚫 **Fail2Ban Integration** — Intrusion detection, jail status, and IP ban/unban management.
- ⏰ **Cron Jobs** — Visual crontab management, schedule presets, and job execution controls.
- 💾 **Backup & Restore** — Per-site and full server backup archives with remote export and restore.
- ⚙️ **Service Manager** — Start, stop, restart, and monitor systemd services (Nginx, MySQL, PHP-FPM, Pure-FTPd, Redis, etc.).
- 🔍 **Process Manager & Log Viewer** — Live process monitoring, kill signals, and searchable log viewer for system and services.
- 📜 **Audit & Activity Logs** — Complete security trail of panel actions and logins.
- 👥 **User Management & RBAC** — Multi-user support with `admin`, `reseller`, and `client` roles.
- 🎨 **Dark / Light Mode** — Modern design system with smooth theme transitions.
- ⌨️ **Command Palette** — Press <kbd>Ctrl</kbd> + <kbd>K</kbd> to quickly search and navigate across modules.

---

## 🛠️ Alternative Installation Methods

### Option A: From a Cloned Repository

```bash
git clone https://github.com/ibrahimarchive/hyperpanel.git
cd hyperpanel
sudo bash install.sh
```

### Option B: Local Development Setup (Windows / Linux / macOS)

To run the panel locally for development:

```bash
# 1. Navigate to backend
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Start the FastAPI server (serves both API and frontend SPA)
python -m app.main
```

The frontend SPA and backend API are both served at **`http://localhost:8443`**.

---

## 🚀 Service Management Commands

```bash
# Check status
sudo systemctl status hyperpanel

# Restart panel
sudo systemctl restart hyperpanel

# Stop panel
sudo systemctl stop hyperpanel

# View live systemd logs
sudo journalctl -u hyperpanel -f
```

---

## 🔄 Updating HyperPanel

HyperPanel uses an **official GitHub Release-based update system** so that regular repository commits or work-in-progress code never trigger unwanted updates.

### Option 1: One-Click Update via Control Panel (Recommended)
1. Go to **Settings** in the HyperPanel dashboard.
2. Under **System Updates**, click **Check for Updates**.
3. When an official release is available, review the release notes and click **Update to Latest Release**.
4. The panel updates itself in the background and automatically reloads when the service restarts.

### Option 2: Command-Line Updater
Run the included update script on your server:
```bash
sudo bash /opt/hyperpanel/update.sh
```
*To pin to a specific release tag:*
```bash
sudo bash /opt/hyperpanel/update.sh v1.0.1
```

---

## 📁 Project Structure

```
hyperpanel/
├── backend/
│   ├── app/
│   │   ├── models/         # SQLAlchemy ORM models (User, Website, Domain, FTPAccount, etc.)
│   │   ├── schemas/        # Pydantic schemas for request/response validation
│   │   ├── services/       # Core & modular logic (Nginx, MySQL, Docker, WordPress, TOTP, etc.)
│   │   ├── routers/        # FastAPI route controllers (Websites, DB, Docker, Email, FTP, Auth, etc.)
│   │   ├── middleware/     # JWT authentication and RBAC middleware
│   │   └── utils/          # Subprocess wrappers, validators, templates
│   ├── templates/          # Jinja2 templates for Nginx vhost configs
│   ├── requirements.txt    # Python dependencies (FastAPI, uvicorn, qrcode, pillow, etc.)
│   ├── .env.example        # Environment variable template
│   └── hyperpanel.db       # SQLite database (auto-generated)
├── frontend/               # Vanilla Single Page Application (SPA)
│   ├── css/                # Modular CSS design system (variables, components, pages)
│   ├── js/                 # Modular vanilla JS (router, API client)
│   │   └── pages/          # Individual view controllers (dashboard, terminal, websites, databases, etc.)
│   ├── assets/             # SVGs, icons, and logos
│   ├── index.html          # Login view with 2FA TOTP prompt
│   └── dashboard.html      # Main panel dashboard & view container
├── .gitattributes          # Line-ending normalization (LF for shell scripts)
├── .gitignore              # Clean ignore patterns (venv, .env, *.db, pycache, plan/)
├── install.sh              # 1-command automated installer script
├── update.sh               # Official release self-updater script
├── LICENSE                 # GNU GPL-3.0 License
└── README.md               # Documentation
```

---

## 📄 License
 
This project is licensed under the [GNU General Public License v3.0 (GPL-3.0)](LICENSE).
