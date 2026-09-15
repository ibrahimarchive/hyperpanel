"""
Cron job management service.
Reads and writes system crontab entries per user.
"""

import logging
import re
import shlex
import tempfile
from typing import Optional

from app.utils.command import run_sudo, run_command, CommandResult

logger = logging.getLogger(__name__)

# Common cron schedule presets
CRON_PRESETS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "hourly": "0 * * * *",
    "daily": "0 0 * * *",
    "daily_3am": "0 3 * * *",
    "weekly": "0 0 * * 0",
    "monthly": "0 0 1 * *",
}

# Cron field constraints
CRON_FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day": (1, 31),
    "month": (1, 12),
    "weekday": (0, 7),  # 0 and 7 both = Sunday
}


class CronService:
    """Manages system crontab entries."""

    def validate_schedule(self, schedule: str) -> bool:
        """Validate a 5-field cron expression."""
        parts = schedule.strip().split()
        if len(parts) != 5:
            return False

        field_names = list(CRON_FIELD_RANGES.keys())
        for i, part in enumerate(parts):
            if not self._validate_field(part, CRON_FIELD_RANGES[field_names[i]]):
                return False
        return True

    def _validate_field(self, field: str, value_range: tuple) -> bool:
        """Validate a single cron field."""
        min_val, max_val = value_range

        # Wildcard
        if field == "*":
            return True

        # Step values: */N or N-M/S
        if "/" in field:
            parts = field.split("/")
            if len(parts) != 2:
                return False
            try:
                step = int(parts[1])
                if step < 1:
                    return False
            except ValueError:
                return False
            base = parts[0]
            if base == "*":
                return True
            return self._validate_field(base, value_range)

        # Ranges: N-M
        if "-" in field:
            parts = field.split("-")
            if len(parts) != 2:
                return False
            try:
                start, end = int(parts[0]), int(parts[1])
                return min_val <= start <= max_val and min_val <= end <= max_val
            except ValueError:
                return False

        # Lists: N,M,O
        if "," in field:
            return all(self._validate_field(p, value_range) for p in field.split(","))

        # Single value
        try:
            val = int(field)
            return min_val <= val <= max_val
        except ValueError:
            return False

    def describe_schedule(self, schedule: str) -> str:
        """Return a human-readable description of a cron schedule."""
        schedule = schedule.strip()

        # Check presets first
        descriptions = {
            "* * * * *": "Every minute",
            "*/5 * * * *": "Every 5 minutes",
            "*/15 * * * *": "Every 15 minutes",
            "*/30 * * * *": "Every 30 minutes",
            "0 * * * *": "Every hour",
            "0 0 * * *": "Daily at midnight",
            "0 3 * * *": "Daily at 3:00 AM",
            "0 0 * * 0": "Weekly on Sunday",
            "0 0 1 * *": "Monthly on the 1st",
        }

        if schedule in descriptions:
            return descriptions[schedule]

        return f"Custom: {schedule}"

    async def list_system_crontab(self, username: str = "root") -> list[dict]:
        """Read and parse the system crontab for a user safely."""
        q_user = shlex.quote(username)
        result = await run_sudo(f"crontab -l -u {q_user}")

        if not result.success:
            if "no crontab" in result.stderr.lower():
                return []
            logger.warning(f"Failed to read crontab for {username}: {result.stderr}")
            return []

        entries = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(None, 5)
            if len(parts) >= 6:
                schedule = " ".join(parts[:5])
                command = parts[5]
                entries.append({
                    "schedule": schedule,
                    "command": command,
                    "description": self.describe_schedule(schedule),
                })

        return entries

    async def _write_crontab(self, username: str, content: str) -> CommandResult:
        """Write crontab content via a temporary file."""
        q_user = shlex.quote(username)
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.write(content.strip() + "\n" if content.strip() else "")
            tmp_file = tf.name

        try:
            result = await run_sudo(f"crontab -u {q_user} {tmp_file}")
            return result
        finally:
            await run_sudo(f"rm -f {tmp_file}")

    async def add_to_crontab(self, username: str, schedule: str, command: str) -> dict:
        """Add a cron entry to the system crontab safely."""
        if not self.validate_schedule(schedule):
            return {"success": False, "error": "Invalid cron schedule expression"}

        q_user = shlex.quote(username)
        result = await run_sudo(f"crontab -l -u {q_user}")
        existing = ""
        if result.success:
            existing = result.stdout.strip()

        new_entry = f"{schedule} {command}"
        if existing:
            new_crontab = f"{existing}\n{new_entry}\n"
        else:
            new_crontab = f"{new_entry}\n"

        write_result = await self._write_crontab(username, new_crontab)

        if write_result.success:
            logger.info(f"Added cron job for {username}: {new_entry}")
        else:
            logger.error(f"Failed to add cron job: {write_result.stderr}")

        return {"success": write_result.success, "error": write_result.stderr if not write_result.success else None}

    async def remove_from_crontab(self, username: str, schedule: str, command: str) -> dict:
        """Remove a specific cron entry from the system crontab safely."""
        q_user = shlex.quote(username)
        result = await run_sudo(f"crontab -l -u {q_user}")
        if not result.success:
            return {"success": False, "error": "Could not read crontab"}

        target_line = f"{schedule} {command}"
        lines = result.stdout.strip().split("\n")
        new_lines = [l for l in lines if l.strip() != target_line]

        if len(new_lines) == len(lines):
            return {"success": False, "error": "Cron entry not found"}

        new_crontab = "\n".join(new_lines) + "\n" if new_lines else ""

        if new_crontab.strip():
            write_result = await self._write_crontab(username, new_crontab)
        else:
            write_result = await run_sudo(f"crontab -r -u {q_user}")

        return {"success": write_result.success}

    async def update_in_crontab(
        self,
        username: str,
        old_schedule: str,
        old_command: str,
        new_schedule: str,
        new_command: str,
    ) -> dict:
        """Update a cron entry by removing old and adding new."""
        if not self.validate_schedule(new_schedule):
            return {"success": False, "error": "Invalid cron schedule expression"}

        await self.remove_from_crontab(username, old_schedule, old_command)
        return await self.add_to_crontab(username, new_schedule, new_command)

    def get_presets(self) -> list[dict]:
        """Return a list of common cron schedule presets."""
        return [
            {"key": k, "schedule": v, "description": self.describe_schedule(v)}
            for k, v in CRON_PRESETS.items()
        ]


# Singleton
cron_service = CronService()
