"""
Domain and DNS management API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.models.domain import Domain, DomainStatus
from app.models.dns_record import DNSRecord
from app.models.activity_log import ActivityLog
from app.schemas.domain import DomainCreate, DomainUpdate
from app.schemas.dns import DNSRecordCreate, DNSRecordUpdate
from app.services.dns_service import dns_service

router = APIRouter(prefix="/api/domains", tags=["Domains"])
dns_router = APIRouter(prefix="/api/dns", tags=["DNS"])


# ── Domain Routes ──────────────────────────────────────────────

@router.get("")
async def list_domains(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Domain)
    if user.role != UserRole.ADMIN:
        query = query.where(Domain.user_id == user.id)

    result = await db.execute(query.order_by(Domain.created_at.desc()))
    domains = result.scalars().all()

    return [
        {
            "id": d.id, "name": d.name,
            "status": d.status.value if hasattr(d.status, 'value') else d.status,
            "registrar": d.registrar,
            "expiry_date": d.expiry_date.isoformat() if d.expiry_date else None,
            "dns_managed": d.dns_managed,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in domains
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_domain(
    data: DomainCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Domain).where(Domain.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Domain '{data.name}' already exists")

    domain = Domain(
        user_id=user.id,
        name=data.name,
        registrar=data.registrar,
        expiry_date=data.expiry_date,
        nameservers=data.nameservers,
        dns_managed=data.dns_managed,
    )
    db.add(domain)
    await db.flush()
    await db.refresh(domain)

    # Create default DNS records
    if data.dns_managed == "local":
        await dns_service.create_default_records(db, domain.id, data.name, "0.0.0.0")

    log = ActivityLog(
        user_id=user.id, action="domain.create", category="domain",
        description=f"Added domain '{data.name}'",
        resource_type="domain", resource_name=data.name,
    )
    db.add(log)

    return {"id": domain.id, "name": domain.name, "message": "Domain added successfully"}


@router.delete("/{domain_id}")
async def delete_domain(
    domain_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    if user.role != UserRole.ADMIN and domain.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete DNS records
    await db.execute(
        select(DNSRecord).where(DNSRecord.domain_id == domain_id)
    )
    dns_records = (await db.execute(
        select(DNSRecord).where(DNSRecord.domain_id == domain_id)
    )).scalars().all()
    for record in dns_records:
        await db.delete(record)

    await db.delete(domain)
    return {"message": f"Domain '{domain.name}' deleted"}


# ── DNS Routes ──────────────────────────────────────────────────

@dns_router.get("/{domain_id}/records")
async def list_dns_records(
    domain_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = await dns_service.get_records(db, domain_id)
    return [
        {
            "id": r.id, "domain_id": r.domain_id,
            "record_type": r.record_type.value if hasattr(r.record_type, 'value') else r.record_type,
            "name": r.name, "value": r.value,
            "ttl": r.ttl, "priority": r.priority,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@dns_router.post("/records", status_code=status.HTTP_201_CREATED)
async def create_dns_record(
    data: DNSRecordCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await dns_service.create_record(
        db, data.domain_id, data.record_type,
        data.name, data.value, data.ttl, data.priority,
    )
    return {"id": record.id, "message": "DNS record created"}


@dns_router.put("/records/{record_id}")
async def update_dns_record(
    record_id: int,
    data: DNSRecordUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await dns_service.update_record(
        db, record_id,
        record_type=data.record_type,
        name=data.name,
        value=data.value,
        ttl=data.ttl,
        priority=data.priority,
    )
    if not record:
        raise HTTPException(status_code=404, detail="DNS record not found")
    return {"message": "DNS record updated"}


@dns_router.delete("/records/{record_id}")
async def delete_dns_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await dns_service.delete_record(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="DNS record not found")
    return {"message": "DNS record deleted"}
