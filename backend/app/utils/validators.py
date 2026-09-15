"""
Input validation utilities.
"""

import re
from typing import Optional


def validate_domain(domain: str) -> bool:
    """Validate a domain name."""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_username(username: str) -> bool:
    """Validate a system username (Linux-compatible)."""
    pattern = r'^[a-z_][a-z0-9_-]{0,31}$'
    return bool(re.match(pattern, username))


def validate_database_name(name: str) -> bool:
    """Validate a MySQL database name."""
    pattern = r'^[a-zA-Z0-9_]{1,64}$'
    return bool(re.match(pattern, name))


def validate_port(port: int) -> bool:
    """Validate a network port number."""
    return 1 <= port <= 65535


import ipaddress

def validate_ip(ip: str) -> bool:
    """Validate an IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(ip.strip())
        return True
    except ValueError:
        return False


def validate_name(name: str) -> bool:
    """Validate a safe general identifier name (alphanumeric, dash, underscore)."""
    pattern = r'^[a-zA-Z0-9._-]{1,128}$'
    return bool(re.match(pattern, name))


def validate_cron_expression(expression: str) -> bool:
    """Basic validation of a cron expression (5 fields)."""
    parts = expression.strip().split()
    if len(parts) != 5:
        return False
    # Basic check: each field should contain valid cron characters
    valid_chars = re.compile(r'^[\d,\-\*/]+$')
    return all(valid_chars.match(p) for p in parts)


def sanitize_path(path: str, base_dir: str) -> Optional[str]:
    """
    Sanitize a file path to prevent directory traversal.
    Returns None if the path tries to escape the base directory.
    """
    from pathlib import Path as P
    try:
        base = P(base_dir).resolve()
        target = (base / path.lstrip("/\\")).resolve()
        if str(target).startswith(str(base)):
            return str(target)
        return None
    except (ValueError, OSError):
        return None

