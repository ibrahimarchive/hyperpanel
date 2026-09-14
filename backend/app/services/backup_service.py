"""
Backup and restore service.
Handles full server, per-site, and database backups using tar and mysqldump.
"""

import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.utils.command import run_sudo, run_command

logger = logging.getLogger(__name__)


class BackupService:
    """Manages server backups and restores."""

    def __init__(self):
        self.backups_dir = Path(settings.BACKUPS_DIR)

    async def ensure_backup_dir(self):
        """Ensure the backup directory exists."""
        await run_sudo(f"mkdir -p {self.backups_dir}")
        await run_sudo(f"chown hyperpanel:hyperpanel {self.backups_dir}")

    async def get_storage_info(self) -> dict:
        """Get backup storage usage information."""
        await self.ensure_backup_dir()

        result = await run_command(f"du -sb {self.backups_dir}")
        total_bytes = 0
        if result.success and result.output:
            try:
                total_bytes = int(result.output.split()[0])
            except (ValueError, IndexError):
                pass

        # Get disk free space
        disk_result = await run_command(f"df -B1 {self.backups_dir}")
        disk_free = 0
        disk_total = 0
        if disk_result.success:
            lines = disk_result.output.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    try:
                        disk_total = int(parts[1])
                        disk_free = int(parts[3])
                    except (ValueError, IndexError):
                        pass

        # Count backup files
        count_result = await run_command(f"find {self.backups_dir} -name '*.tar.gz' -o -name '*.sql.gz' | wc -l", shell=True)
        backup_count = 0
        if count_result.success:
            try:
                backup_count = int(count_result.output.strip())
            except ValueError:
                pass

        return {
            "used_bytes": total_bytes,
            "disk_free_bytes": disk_free,
            "disk_total_bytes": disk_total,
            "backup_count": backup_count,
            "backups_dir": str(self.backups_dir),
        }

    async def create_full_backup(self, user_id: int) -> dict:
        """Create a full server backup (websites + databases + configs)."""
        await self.ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_backup_{timestamp}.tar.gz"
        filepath = self.backups_dir / filename

        try:
            # Dump all MySQL databases
            dump_dir = self.backups_dir / f"_tmp_{timestamp}"
            await run_sudo(f"mkdir -p {dump_dir}")

            # Get list of databases
            db_result = await run_sudo(
                'mysql -N -e "SHOW DATABASES" | grep -Ev "^(information_schema|performance_schema|mysql|sys)$"',
                shell=True,
            )
            if db_result.success and db_result.output.strip():
                for db_name in db_result.output.strip().split("\n"):
                    db_name = db_name.strip()
                    if db_name:
                        await run_sudo(
                            f"mysqldump --single-transaction --routines --triggers {db_name} | gzip > {dump_dir}/{db_name}.sql.gz",
                            shell=True,
                        )

            # Copy Nginx configs
            await run_sudo(f"cp -r /etc/nginx/sites-available {dump_dir}/nginx_configs 2>/dev/null || true", shell=True)

            # Create tar.gz including websites + DB dumps + configs
            items_to_backup = f"{settings.WEBSITES_ROOT} {dump_dir}"
            await run_sudo(
                f"tar -czf {filepath} {items_to_backup} 2>/dev/null",
                shell=True,
                timeout=600,
            )

            # Cleanup temp directory
            await run_sudo(f"rm -rf {dump_dir}")

            # Get file size
            stat_result = await run_command(f"stat -c %s {filepath}")
            size_bytes = int(stat_result.output.strip()) if stat_result.success else 0

            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "size_bytes": size_bytes,
            }

        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            # Cleanup on failure
            await run_sudo(f"rm -rf {self.backups_dir}/_tmp_{timestamp}")
            return {"success": False, "error": str(e)}

    async def create_website_backup(self, website_name: str, docroot: str, database_name: Optional[str] = None) -> dict:
        """Create a backup for a specific website."""
        await self.ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = website_name.replace(".", "_").replace("/", "_")
        filename = f"site_{safe_name}_{timestamp}.tar.gz"
        filepath = self.backups_dir / filename

        try:
            items = docroot
            tmp_db_dump = None

            # Dump associated database if provided
            if database_name:
                tmp_db_dump = f"/tmp/{safe_name}_{timestamp}.sql.gz"
                await run_sudo(
                    f"mysqldump --single-transaction --routines --triggers {database_name} | gzip > {tmp_db_dump}",
                    shell=True,
                )
                items = f"{docroot} {tmp_db_dump}"

            await run_sudo(f"tar -czf {filepath} {items} 2>/dev/null", shell=True, timeout=300)

            # Cleanup temp DB dump
            if tmp_db_dump:
                await run_sudo(f"rm -f {tmp_db_dump}")

            stat_result = await run_command(f"stat -c %s {filepath}")
            size_bytes = int(stat_result.output.strip()) if stat_result.success else 0

            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "size_bytes": size_bytes,
            }

        except Exception as e:
            logger.error(f"Website backup failed: {e}")
            return {"success": False, "error": str(e)}

    async def create_database_backup(self, database_name: str) -> dict:
        """Create a backup of a single database."""
        await self.ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_{database_name}_{timestamp}.sql.gz"
        filepath = self.backups_dir / filename

        try:
            result = await run_sudo(
                f"mysqldump --single-transaction --routines --triggers {database_name} | gzip > {filepath}",
                shell=True,
                timeout=300,
            )

            if not result.success:
                return {"success": False, "error": result.stderr}

            stat_result = await run_command(f"stat -c %s {filepath}")
            size_bytes = int(stat_result.output.strip()) if stat_result.success else 0

            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "size_bytes": size_bytes,
            }

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {"success": False, "error": str(e)}

    async def restore_full_backup(self, filepath: str) -> dict:
        """Restore from a full backup."""
        try:
            result = await run_sudo(
                f"tar -xzf {filepath} -C /",
                shell=True,
                timeout=600,
            )

            if not result.success:
                return {"success": False, "error": result.stderr}

            # Restore databases from SQL dumps
            backup_tmp_dirs = await run_command(
                f"tar -tzf {filepath} | grep '.sql.gz' | head -20",
                shell=True,
            )
            if backup_tmp_dirs.success and backup_tmp_dirs.output.strip():
                for sql_file in backup_tmp_dirs.output.strip().split("\n"):
                    sql_file = sql_file.strip()
                    if sql_file.endswith(".sql.gz"):
                        db_name = Path(sql_file).stem.replace(".sql", "")
                        await run_sudo(f"mysql -e 'CREATE DATABASE IF NOT EXISTS `{db_name}`'")
                        await run_sudo(
                            f"zcat /{sql_file} | mysql {db_name}",
                            shell=True,
                            timeout=300,
                        )

            # Reload Nginx
            await run_sudo("nginx -t && systemctl reload nginx", shell=True)

            return {"success": True}

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {"success": False, "error": str(e)}

    async def restore_database_backup(self, filepath: str, database_name: str) -> dict:
        """Restore a database from a backup."""
        try:
            await run_sudo(f"mysql -e 'CREATE DATABASE IF NOT EXISTS `{database_name}`'")
            result = await run_sudo(
                f"zcat {filepath} | mysql {database_name}",
                shell=True,
                timeout=300,
            )

            return {"success": result.success, "error": result.stderr if not result.success else None}

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return {"success": False, "error": str(e)}

    async def delete_backup(self, filepath: str) -> dict:
        """Delete a backup file."""
        try:
            result = await run_sudo(f"rm -f {filepath}")
            return {"success": result.success}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_backup_file_size(self, filepath: str) -> int:
        """Get the size of a backup file."""
        result = await run_command(f"stat -c %s {filepath}")
        if result.success:
            try:
                return int(result.output.strip())
            except ValueError:
                pass
        return 0


# Singleton
backup_service = BackupService()
