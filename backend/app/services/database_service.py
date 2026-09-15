"""
Database management service.
Manages MySQL/MariaDB databases and users.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from app.utils.command import CommandResult, run_command, run_sudo

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages MySQL/MariaDB databases and users."""

    async def _run_mysql_query(self, sql: str) -> CommandResult:
        """Execute a MySQL query reliably via a temp file piped to sudo mysql."""
        tmp_path = None
        try:
            fd, tmp_path = tempfile.mkstemp(prefix="hp_sql_", suffix=".sql")
            with os.fdopen(fd, "w") as f:
                f.write(sql)
            cmd = f"mysql < {tmp_path}"
            result = await run_sudo(cmd, shell=True)
            return result
        except Exception as e:
            logger.error(f"MySQL query execution failed: {e}")
            return CommandResult(returncode=-1, stdout="", stderr=str(e), success=False)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    async def create_database(
        self, name: str, charset: str = "utf8mb4", collation: str = "utf8mb4_unicode_ci"
    ) -> dict:
        """Create a new MySQL database."""
        sql = f"CREATE DATABASE IF NOT EXISTS `{name}` CHARACTER SET {charset} COLLATE {collation};"
        result = await self._run_mysql_query(sql)
        if result.success:
            logger.info(f"Database '{name}' created successfully")
            return {"success": True, "name": name}
        return {"success": False, "error": result.stderr or result.stdout}

    async def drop_database(self, name: str) -> dict:
        """Drop a MySQL database."""
        sql = f"DROP DATABASE IF EXISTS `{name}`;"
        result = await self._run_mysql_query(sql)
        if result.success:
            logger.info(f"Database '{name}' dropped")
            return {"success": True}
        return {"success": False, "error": result.stderr or result.stdout}

    async def get_database_size(self, name: str) -> int:
        """Get the size of a database in bytes."""
        sql = (
            f"SELECT SUM(data_length + index_length) "
            f"FROM information_schema.tables WHERE table_schema = '{name}';"
        )
        result = await self._run_mysql_query(sql)
        if result.success and result.output and result.output != "NULL":
            try:
                # Output may contain column header; grab the last numeric line
                for line in reversed(result.output.strip().split("\n")):
                    line = line.strip()
                    if line and line != "NULL":
                        return int(float(line))
            except ValueError:
                return 0
        return 0

    async def list_databases(self) -> list:
        """List all user databases (excluding system databases)."""
        result = await self._run_mysql_query("SHOW DATABASES;")
        if result.success:
            system_dbs = {"information_schema", "mysql", "performance_schema", "sys", "Database"}
            return [db.strip() for db in result.output.split("\n") if db.strip() and db.strip() not in system_dbs]
        return []

    async def create_user(
        self, username: str, password: str, host: str = "localhost"
    ) -> dict:
        """Create a MySQL user."""
        sql = f"CREATE USER IF NOT EXISTS '{username}'@'{host}' IDENTIFIED BY '{password}';"
        result = await self._run_mysql_query(sql)
        if result.success:
            logger.info(f"Database user '{username}'@'{host}' created")
            return {"success": True}
        return {"success": False, "error": result.stderr or result.stdout}

    async def drop_user(self, username: str, host: str = "localhost") -> dict:
        """Drop a MySQL user."""
        sql = f"DROP USER IF EXISTS '{username}'@'{host}';"
        result = await self._run_mysql_query(sql)
        return {"success": result.success, "error": result.stderr or result.stdout if not result.success else None}

    async def grant_privileges(
        self,
        username: str,
        database: str,
        privileges: str = "ALL",
        host: str = "localhost",
    ) -> dict:
        """Grant privileges on a database to a user."""
        sql = f"GRANT {privileges} ON `{database}`.* TO '{username}'@'{host}'; FLUSH PRIVILEGES;"
        result = await self._run_mysql_query(sql)
        return {"success": result.success, "error": result.stderr or result.stdout if not result.success else None}

    async def revoke_privileges(
        self, username: str, database: str, host: str = "localhost"
    ) -> dict:
        """Revoke all privileges from a user on a database."""
        sql = f"REVOKE ALL PRIVILEGES ON `{database}`.* FROM '{username}'@'{host}'; FLUSH PRIVILEGES;"
        result = await self._run_mysql_query(sql)
        return {"success": result.success}

    async def export_database(self, name: str, output_path: str) -> dict:
        """Export a database using mysqldump."""
        cmd = f"mysqldump --single-transaction --quick {name} > {output_path}"
        result = await run_sudo(cmd, shell=True, timeout=600)
        if result.success and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return {"success": True, "path": output_path}
        return {"success": False, "error": result.stderr or "mysqldump produced empty output or failed"}

    async def import_database(self, name: str, input_path: str) -> dict:
        """Import a SQL file into a database."""
        cmd = f"mysql {name} < {input_path}"
        result = await run_sudo(cmd, shell=True, timeout=600)
        return {"success": result.success, "error": result.stderr if not result.success else None}

    async def get_adminer_status(self) -> dict:
        """Check if Adminer is installed on the system."""
        adminer_path = Path("/var/www/html/adminer.php")
        return {
            "installed": adminer_path.exists(),
            "path": str(adminer_path) if adminer_path.exists() else None,
            "url": "/adminer.php",
        }

    async def install_adminer(self) -> dict:
        """Download and install single-file lightweight Adminer."""
        target_dir = Path("/var/www/html")
        target_file = target_dir / "adminer.php"
        await run_sudo(f"mkdir -p {target_dir}")
        download_cmd = (
            f"curl -sSL https://github.com/vrana/adminer/releases/download/v4.8.1/adminer-4.8.1.php "
            f"-o {target_file} && chown www-data:www-data {target_file} && chmod 644 {target_file}"
        )
        result = await run_sudo(download_cmd, shell=True)
        if result.success:
            return {"success": True, "url": "/adminer.php", "message": "Adminer installed successfully"}
        return {"success": False, "error": result.stderr or "Failed to download Adminer"}


# Singleton
database_service = DatabaseService()
