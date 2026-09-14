"""
DNS management service.
Manages DNS zones and records.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dns_record import DNSRecord
from app.utils.command import run_sudo

logger = logging.getLogger(__name__)


class DNSService:
    """Manages DNS records in the database and optionally syncs to BIND9/PowerDNS."""

    async def create_record(
        self,
        db: AsyncSession,
        domain_id: int,
        record_type: str,
        name: str,
        value: str,
        ttl: int = 3600,
        priority: Optional[int] = None,
    ) -> DNSRecord:
        """Create a DNS record."""
        record = DNSRecord(
            domain_id=domain_id,
            record_type=record_type,
            name=name,
            value=value,
            ttl=ttl,
            priority=priority,
        )
        db.add(record)
        await db.flush()
        logger.info(f"DNS record created: {record_type} {name} -> {value}")
        return record

    async def get_records(self, db: AsyncSession, domain_id: int) -> list:
        """Get all DNS records for a domain."""
        result = await db.execute(
            select(DNSRecord).where(DNSRecord.domain_id == domain_id)
        )
        return result.scalars().all()

    async def update_record(
        self,
        db: AsyncSession,
        record_id: int,
        **kwargs,
    ) -> Optional[DNSRecord]:
        """Update a DNS record."""
        result = await db.execute(select(DNSRecord).where(DNSRecord.id == record_id))
        record = result.scalar_one_or_none()
        if not record:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(record, key):
                setattr(record, key, value)

        await db.flush()
        return record

    async def delete_record(self, db: AsyncSession, record_id: int) -> bool:
        """Delete a DNS record."""
        result = await db.execute(select(DNSRecord).where(DNSRecord.id == record_id))
        record = result.scalar_one_or_none()
        if record:
            await db.delete(record)
            await db.flush()
            return True
        return False

    async def create_default_records(
        self, db: AsyncSession, domain_id: int, domain_name: str, server_ip: str
    ) -> list:
        """Create default DNS records for a new domain."""
        defaults = [
            ("A", "@", server_ip, 3600, None),
            ("A", "www", server_ip, 3600, None),
            ("MX", "@", f"mail.{domain_name}", 3600, 10),
            ("TXT", "@", "v=spf1 ip4:{} ~all".format(server_ip), 3600, None),
        ]

        records = []
        for rtype, name, value, ttl, priority in defaults:
            record = await self.create_record(
                db, domain_id, rtype, name, value, ttl, priority
            )
            records.append(record)

        return records


# Singleton
dns_service = DNSService()
