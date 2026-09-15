"""
Firewall management service.
Manages UFW (Uncomplicated Firewall) rules.
"""

import logging
import shlex
import re
from typing import Optional

from app.utils.command import run_sudo

logger = logging.getLogger(__name__)


class FirewallService:
    """Manages UFW firewall rules."""

    async def get_status(self) -> dict:
        """Get UFW status and configuration."""
        result = await run_sudo("ufw status verbose")
        if not result.success:
            return {"enabled": False, "error": result.stderr}

        enabled = "Status: active" in result.stdout
        default_incoming = "deny"
        default_outgoing = "allow"

        for line in result.stdout.split("\n"):
            if "Default:" in line:
                if "incoming" in line.lower():
                    default_incoming = "deny" if "deny" in line.lower() else "allow"
                if "outgoing" in line.lower():
                    default_outgoing = "allow" if "allow" in line.lower() else "deny"

        return {
            "enabled": enabled,
            "default_incoming": default_incoming,
            "default_outgoing": default_outgoing,
            "raw_output": result.stdout,
        }

    async def enable(self) -> dict:
        """Enable UFW."""
        result = await run_sudo("ufw --force enable")
        return {"success": result.success, "output": result.stdout}

    async def disable(self) -> dict:
        """Disable UFW."""
        result = await run_sudo("ufw --force disable")
        return {"success": result.success, "output": result.stdout}

    async def add_rule(
        self,
        action: str,
        port: str,
        protocol: str = "tcp",
        source_ip: Optional[str] = None,
    ) -> dict:
        """Add a firewall rule safely."""
        safe_action = action.lower() if action.lower() in ("allow", "deny", "reject", "limit") else "allow"
        safe_protocol = protocol.lower() if protocol.lower() in ("tcp", "udp", "both") else "tcp"
        q_port = shlex.quote(str(port).strip())

        if source_ip and re.match(r"^[\d\.:a-fA-F/]+$", source_ip.strip()):
            q_ip = shlex.quote(source_ip.strip())
            cmd = f"ufw {safe_action} from {q_ip} to any port {q_port} proto {safe_protocol}"
        elif safe_protocol == "both":
            cmd = f"ufw {safe_action} {q_port}"
        else:
            cmd = f"ufw {safe_action} {q_port}/{safe_protocol}"

        result = await run_sudo(cmd)
        logger.info(f"Firewall rule added: {cmd} — success: {result.success}")
        return {"success": result.success, "output": result.stdout, "error": result.stderr if not result.success else None}

    async def delete_rule(self, rule_number: int) -> dict:
        """Delete a firewall rule by its number."""
        safe_num = int(rule_number)
        result = await run_sudo(f"ufw --force delete {safe_num}")
        return {"success": result.success}

    async def delete_rule_by_spec(
        self, action: str, port: str, protocol: str = "tcp", source_ip: Optional[str] = None
    ) -> dict:
        """Delete a rule by its specification safely."""
        safe_action = action.lower() if action.lower() in ("allow", "deny", "reject", "limit") else "allow"
        safe_protocol = protocol.lower() if protocol.lower() in ("tcp", "udp", "both") else "tcp"
        q_port = shlex.quote(str(port).strip())

        if source_ip and re.match(r"^[\d\.:a-fA-F/]+$", source_ip.strip()):
            q_ip = shlex.quote(source_ip.strip())
            cmd = f"ufw delete {safe_action} from {q_ip} to any port {q_port} proto {safe_protocol}"
        elif safe_protocol == "both":
            cmd = f"ufw delete {safe_action} {q_port}"
        else:
            cmd = f"ufw delete {safe_action} {q_port}/{safe_protocol}"

        result = await run_sudo(cmd)
        return {"success": result.success}

    async def list_rules(self) -> list:
        """Parse and list UFW rules in a structured format."""
        result = await run_sudo("ufw status numbered")
        if not result.success:
            return []

        rules = []
        # Parse lines like: [ 1] 22/tcp                     ALLOW IN    Anywhere
        pattern = r'\[\s*(\d+)\]\s+(.+?)\s+(ALLOW|DENY|LIMIT|REJECT)\s+(IN|OUT)\s+(.*)'
        for line in result.stdout.split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                number, port_info, action, direction, source = match.groups()
                rules.append({
                    "number": int(number),
                    "port": port_info.strip(),
                    "action": action.lower(),
                    "direction": direction.lower(),
                    "source": source.strip() if source.strip() else "Anywhere",
                })

        return rules

    async def reset(self) -> dict:
        """Reset all UFW rules to defaults."""
        result = await run_sudo("ufw --force reset")
        return {"success": result.success}


# Singleton
firewall_service = FirewallService()
