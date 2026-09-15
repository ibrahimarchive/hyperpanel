"""
Unit tests for HyperPanel security validators, auth services, and command wrappers.
"""

import pytest
from app.utils.validators import (
    validate_domain,
    validate_username,
    validate_database_name,
    validate_port,
    validate_ip,
    validate_name,
    validate_cron_expression,
    sanitize_path,
)
from app.utils.command import _redact_command
from app.services.auth_service import (
    create_access_token,
    decode_token,
    revoke_token,
    is_token_revoked,
)
from app.models.user import User, UserRole


def test_domain_validation():
    assert validate_domain("example.com") is True
    assert validate_domain("sub.domain.co.uk") is True
    assert validate_domain("invalid_domain") is False
    assert validate_domain("http://example.com") is False
    assert validate_domain("example.com; rm -rf /") is False


def test_username_validation():
    assert validate_username("john") is True
    assert validate_username("user_123") is True
    assert validate_username("root") is True
    assert validate_username("user;id") is False
    assert validate_username("../../etc/passwd") is False


def test_database_name_validation():
    assert validate_database_name("my_db") is True
    assert validate_database_name("db123") is True
    assert validate_database_name("db; DROP DATABASE mysql;") is False
    assert validate_database_name("db' OR '1'='1") is False


def test_port_validation():
    assert validate_port(80) is True
    assert validate_port(8443) is True
    assert validate_port(0) is False
    assert validate_port(70000) is False


def test_ip_validation():
    assert validate_ip("127.0.0.1") is True
    assert validate_ip("192.168.1.1") is True
    assert validate_ip("::1") is True
    assert validate_ip("999.999.999.999") is False
    assert validate_ip("127.0.0.1; reboot") is False


def test_name_validation():
    assert validate_name("v1.0.0") is True
    assert validate_name("my-container-1") is True
    assert validate_name("test; rm -rf /") is False


def test_sanitize_path(tmp_path):
    base_dir = str(tmp_path)
    safe_file = sanitize_path("uploads/file.txt", base_dir)
    assert safe_file is not None
    assert str(safe_file).startswith(base_dir)

    escaped_file = sanitize_path("../../etc/passwd", base_dir)
    assert escaped_file is None


def test_command_redaction():
    cmd = "mysql -u root -pSecret123 -e 'SELECT 1'"
    redacted = _redact_command(cmd)
    assert "Secret123" not in redacted
    assert "[REDACTED]" in redacted

    cmd2 = "CREATE USER 'usr'@'localhost' IDENTIFIED BY 'Pass123!'"
    redacted2 = _redact_command(cmd2)
    assert "Pass123!" not in redacted2
    assert "[REDACTED]" in redacted2


def test_token_revocation():
    user = User(id=1, username="testadmin", role=UserRole.ADMIN)
    token = create_access_token(user)

    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "1"

    revoke_token(token)
    assert is_token_revoked(token) is True
    assert decode_token(token) is None
