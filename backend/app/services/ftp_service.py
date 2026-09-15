"""
Pure-FTPd management service.
Handles optional installation, service controls, virtual users, and directory jailing.
"""

import logging
import shlex
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ftp_account import FTPAccount, FTPAccountStatus
from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)


class FTPService:
    """Manages Pure-FTPd installation, daemon status, and virtual accounts."""

    async def get_status(self, db: Optional[AsyncSession] = None) -> dict:
        """Check Pure-FTPd installation and running status."""
        check_binary = await run_command("which pure-ftpd || test -f /usr/sbin/pure-ftpd && echo yes || echo no", shell=True)
        installed = "yes" in check_binary.output or "/pure-ftpd" in check_binary.output

        if not installed:
            return {
                "installed": False,
                "running": False,
                "version": None,
                "passive_port_range": "30000-30050",
                "accounts_count": 0,
            }

        # Check running status via systemctl or service
        svc_check = await run_command("systemctl is-active pure-ftpd 2>/dev/null || service pure-ftpd status 2>/dev/null", shell=True)
        running = "active" in svc_check.output or "is running" in svc_check.output

        # Get version
        ver_check = await run_command("pure-ftpd -v 2>&1 | head -1 || dpkg -s pure-ftpd 2>/dev/null | grep Version", shell=True)
        version = ver_check.output.strip() if ver_check.success else "Pure-FTPd"

        # Count accounts in DB if session provided
        accounts_count = 0
        if db:
            result = await db.execute(select(FTPAccount))
            accounts_count = len(result.scalars().all())

        return {
            "installed": installed,
            "running": running,
            "version": version,
            "passive_port_range": "30000-30050",
            "accounts_count": accounts_count,
        }

    async def install(self) -> dict:
        """Install Pure-FTPd and configure virtual user authentication & chroot."""
        setup_script = (
            "export DEBIAN_FRONTEND=noninteractive && "
            "apt-get update -qq && "
            "apt-get install -y -qq pure-ftpd pure-ftpd-common && "
            "mkdir -p /etc/pure-ftpd/conf /etc/pure-ftpd/auth && "
            "echo 'yes' > /etc/pure-ftpd/conf/ChrootEveryone && "
            "echo 'no' > /etc/pure-ftpd/conf/PAMAuthentication && "
            "echo 'no' > /etc/pure-ftpd/conf/UnixAuthentication && "
            "echo '/etc/pure-ftpd/pureftpd.pdb' > /etc/pure-ftpd/conf/PureDB && "
            "ln -sf /etc/pure-ftpd/conf/PureDB /etc/pure-ftpd/auth/60puredb 2>/dev/null || true && "
            "echo '33' > /etc/pure-ftpd/conf/MinUID && "
            "echo '30000 30050' > /etc/pure-ftpd/conf/PassivePortRange && "
            "echo 'yes' > /etc/pure-ftpd/conf/NoAnonymous && "
            "echo 'yes' > /etc/pure-ftpd/conf/DontResolve && "
            "ufw allow 21/tcp comment 'FTP' 2>/dev/null || true && "
            "ufw allow 30000:30050/tcp comment 'FTP Passive' 2>/dev/null || true && "
            "systemctl enable pure-ftpd 2>/dev/null || true && "
            "systemctl restart pure-ftpd 2>/dev/null || true"
        )

        res = await run_sudo(setup_script, shell=True, timeout=300)
        if not res.success:
            logger.error(f"Pure-FTPd installation failed: {res.stderr}")
            return {"success": False, "error": res.stderr or "Installation failed"}

        logger.info("Pure-FTPd installed and configured successfully")
        return {"success": True}

    async def uninstall(self) -> dict:
        """Stop and uninstall Pure-FTPd to keep server lightweight."""
        clean_script = (
            "systemctl stop pure-ftpd 2>/dev/null || true; "
            "systemctl disable pure-ftpd 2>/dev/null || true; "
            "apt-get purge -y pure-ftpd pure-ftpd-common 2>/dev/null || true; "
            "ufw delete allow 21/tcp 2>/dev/null || true; "
            "ufw delete allow 30000:30050/tcp 2>/dev/null || true"
        )
        res = await run_sudo(clean_script, shell=True, timeout=120)
        return {"success": res.success, "error": res.stderr if not res.success else None}

    async def service_action(self, action: str) -> dict:
        """Start, stop, or restart the Pure-FTPd daemon."""
        if action not in ("start", "stop", "restart"):
            return {"success": False, "error": "Invalid action"}
        res = await run_sudo(f"systemctl {action} pure-ftpd")
        return {"success": res.success, "error": res.stderr if not res.success else None}

    async def list_accounts(self, db: AsyncSession) -> list[FTPAccount]:
        """Fetch all registered FTP accounts."""
        result = await db.execute(select(FTPAccount).order_by(FTPAccount.created_at.desc()))
        return list(result.scalars().all())

    async def create_account(
        self,
        db: AsyncSession,
        user_id: int,
        username: str,
        password: str,
        directory: str,
        quota_mb: int = 0,
    ) -> FTPAccount:
        """Create a new virtual FTP user in PureDB and record in database."""
        # 1. Verify username uniqueness
        existing = await db.execute(select(FTPAccount).where(FTPAccount.username == username))
        if existing.scalar_one_or_none():
            raise ValueError(f"FTP user '{username}' already exists")

        # 2. Ensure target directory exists and has suitable permissions
        q_dir = shlex.quote(directory)
        q_user = shlex.quote(username)
        q_pass = shlex.quote(password)

        prep_dir_cmd = f"mkdir -p {q_dir} && chown -R www-data:www-data {q_dir} && chmod 755 {q_dir}"
        await run_sudo(prep_dir_cmd, shell=True)

        # 3. Add to PureDB using pure-pw
        quota_arg = f"-N {int(quota_mb)}" if quota_mb > 0 else ""
        add_user_cmd = (
            f"printf '%s\\n%s\\n' {q_pass} {q_pass} | "
            f"pure-pw useradd {q_user} -u www-data -g www-data -d {q_dir} {quota_arg} -m"
        )
        res = await run_sudo(add_user_cmd, shell=True)
        if not res.success:
            raise RuntimeError(f"pure-pw useradd failed: {res.stderr}")

        # 4. Save record in database
        account = FTPAccount(
            user_id=user_id,
            username=username,
            directory=directory,
            quota_mb=quota_mb,
            status=FTPAccountStatus.ACTIVE,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

    async def update_account(
        self,
        db: AsyncSession,
        account_id: int,
        password: Optional[str] = None,
        directory: Optional[str] = None,
        quota_mb: Optional[int] = None,
        status: Optional[str] = None,
    ) -> FTPAccount:
        """Update an existing FTP account's password, directory, quota, or status safely."""
        result = await db.execute(select(FTPAccount).where(FTPAccount.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("FTP account not found")

        q_acc_user = shlex.quote(account.username)

        # Update pure-pw virtual user
        if directory or quota_mb is not None:
            new_dir = directory or account.directory
            new_quota = quota_mb if quota_mb is not None else account.quota_mb
            quota_arg = f"-N {int(new_quota)}" if new_quota > 0 else "-N 0"
            q_new_dir = shlex.quote(new_dir)

            if directory:
                await run_sudo(f"mkdir -p {q_new_dir} && chown -R www-data:www-data {q_new_dir} && chmod 755 {q_new_dir}", shell=True)

            mod_cmd = f"pure-pw usermod {q_acc_user} -d {q_new_dir} {quota_arg} -m"
            await run_sudo(mod_cmd, shell=True)

            account.directory = new_dir
            account.quota_mb = new_quota

        if password:
            q_new_pass = shlex.quote(password)
            passwd_cmd = f"printf '%s\\n%s\\n' {q_new_pass} {q_new_pass} | pure-pw passwd {q_acc_user} -m"
            res = await run_sudo(passwd_cmd, shell=True)
            if not res.success:
                raise RuntimeError(f"pure-pw passwd failed: {res.stderr}")

        if status:
            account.status = FTPAccountStatus(status)

        await db.commit()
        await db.refresh(account)
        return account

    async def delete_account(self, db: AsyncSession, account_id: int) -> bool:
        """Delete an FTP account from PureDB and database."""
        result = await db.execute(select(FTPAccount).where(FTPAccount.id == account_id))
        account = result.scalar_one_or_none()
        if not account:
            return False

        # Remove from PureDB
        await run_sudo(f"pure-pw userdel '{account.username}' -m", shell=True)

        await db.delete(account)
        await db.commit()
        return True


# Singleton
ftp_service = FTPService()
