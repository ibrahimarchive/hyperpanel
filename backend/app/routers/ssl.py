"""
SSL Certificate API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.ssl_cert import SSLCertificate, CertType, CertStatus
from app.models.domain import Domain
from app.models.activity_log import ActivityLog
from app.schemas.ssl import SSLIssueRequest, SSLUploadRequest
from app.services.ssl_service import ssl_service
from app.services.nginx_service import nginx_service

router = APIRouter(prefix="/api/ssl", tags=["SSL/TLS"])


@router.get("")
async def list_certificates(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SSLCertificate).order_by(SSLCertificate.created_at.desc())
    )
    certs = result.scalars().all()

    return [
        {
            "id": c.id, "domain_name": c.domain_name,
            "cert_type": c.cert_type.value if hasattr(c.cert_type, 'value') else c.cert_type,
            "status": c.status.value if hasattr(c.status, 'value') else c.status,
            "issuer": c.issuer,
            "issued_at": c.issued_at.isoformat() if c.issued_at else None,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "auto_renew": c.auto_renew,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in certs
    ]


@router.post("/issue", status_code=status.HTTP_201_CREATED)
async def issue_certificate(
    data: SSLIssueRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Issue a Let's Encrypt certificate for a domain."""
    # Find the domain
    domain_result = await db.execute(
        select(Domain).where(Domain.name == data.domain_name)
    )
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found in panel")

    # Issue certificate
    result = await ssl_service.issue_letsencrypt(data.domain_name, user.email)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "SSL issuance failed"))

    # Save certificate record
    cert = SSLCertificate(
        domain_id=domain.id,
        website_id=data.website_id,
        domain_name=data.domain_name,
        cert_type=CertType.LETS_ENCRYPT,
        status=CertStatus.ACTIVE,
        cert_path=result["cert_path"],
        key_path=result["key_path"],
        chain_path=result.get("chain_path"),
        issuer="Let's Encrypt",
        auto_renew=data.auto_renew,
    )
    db.add(cert)

    # Update Nginx config with SSL
    await nginx_service.update_ssl_config(
        data.domain_name,
        result["cert_path"],
        result["key_path"],
        result.get("chain_path"),
    )

    log = ActivityLog(
        user_id=user.id, action="ssl.issue", category="ssl",
        description=f"Issued SSL certificate for '{data.domain_name}'",
        resource_type="ssl", resource_name=data.domain_name,
    )
    db.add(log)

    await db.flush()
    return {"message": f"SSL certificate issued for '{data.domain_name}'"}


@router.delete("/{cert_id}")
async def delete_certificate(
    cert_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SSLCertificate).where(SSLCertificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    await ssl_service.delete_certificate(cert.domain_name)
    await db.delete(cert)

    return {"message": f"Certificate for '{cert.domain_name}' deleted"}
