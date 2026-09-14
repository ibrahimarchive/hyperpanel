"""
Safe subprocess command execution wrapper.
All system commands must go through this module for security and logging.
"""

import asyncio
import logging
import shlex
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a command execution."""
    returncode: int
    stdout: str
    stderr: str
    success: bool

    @property
    def output(self) -> str:
        return self.stdout.strip()


async def run_command(
    command: str,
    shell: bool = False,
    cwd: Optional[str] = None,
    timeout: int = 60,
    env: Optional[dict] = None,
) -> CommandResult:
    """
    Execute a system command asynchronously.
    
    Args:
        command: Command string to execute
        shell: Whether to run through shell (avoid if possible)
        cwd: Working directory
        timeout: Timeout in seconds
        env: Additional environment variables
    
    Returns:
        CommandResult with stdout, stderr, returncode
    """
    logger.info(f"Executing command: {command}")

    try:
        if shell:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
        else:
            args = shlex.split(command)
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )

        result = CommandResult(
            returncode=process.returncode or 0,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            success=process.returncode == 0,
        )

        if not result.success:
            logger.warning(
                f"Command failed (rc={result.returncode}): {command}\n"
                f"stderr: {result.stderr}"
            )

        return result

    except asyncio.TimeoutError:
        logger.error(f"Command timed out after {timeout}s: {command}")
        try:
            process.kill()
        except Exception:
            pass
        return CommandResult(
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            success=False,
        )
    except Exception as e:
        logger.error(f"Command execution failed: {command} — {e}")
        return CommandResult(
            returncode=-1,
            stdout="",
            stderr=str(e),
            success=False,
        )


async def run_sudo(command: str, **kwargs) -> CommandResult:
    """Execute a command with sudo privileges."""
    return await run_command(f"sudo {command}", **kwargs)


async def check_service_status(service_name: str) -> dict:
    """Check the status of a systemd service."""
    result = await run_command(f"systemctl is-active {service_name}")
    is_active = result.output == "active"

    result_enabled = await run_command(f"systemctl is-enabled {service_name}")
    is_enabled = result_enabled.output == "enabled"

    return {
        "name": service_name,
        "active": is_active,
        "enabled": is_enabled,
        "status": result.output,
    }
