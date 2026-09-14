"""
Firewall API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User
from app.models.firewall_rule import FirewallRule, RuleAction, RuleProtocol
from app.models.activity_log import ActivityLog
from app.schemas.firewall import FirewallRuleCreate
from app.services.firewall_service import firewall_service

router = APIRouter(prefix="/api/firewall", tags=["Firewall"])


@router.get("/status")
async def get_firewall_status(user: User = Depends(require_admin)):
    """Get firewall status."""
    status_info = await firewall_service.get_status()
    rules = await firewall_service.list_rules()
    return {**status_info, "rules_count": len(rules)}


@router.get("/rules")
async def list_firewall_rules(
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all firewall rules."""
    # Get rules from UFW
    ufw_rules = await firewall_service.list_rules()
    
    # Get panel-managed rules from DB
    result = await db.execute(select(FirewallRule).order_by(FirewallRule.created_at.desc()))
    db_rules = result.scalars().all()

    return {
        "ufw_rules": ufw_rules,
        "managed_rules": [
            {
                "id": r.id,
                "action": r.action.value if hasattr(r.action, 'value') else r.action,
                "protocol": r.protocol.value if hasattr(r.protocol, 'value') else r.protocol,
                "port": r.port,
                "source_ip": r.source_ip,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in db_rules
        ],
    }


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def add_firewall_rule(
    data: FirewallRuleCreate,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a firewall rule."""
    result = await firewall_service.add_rule(
        data.action, data.port, data.protocol, data.source_ip
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to add rule"))

    rule = FirewallRule(
        action=RuleAction(data.action),
        protocol=RuleProtocol(data.protocol),
        port=data.port,
        source_ip=data.source_ip,
        description=data.description,
    )
    db.add(rule)

    log = ActivityLog(
        user_id=user.id, action="firewall.add_rule", category="firewall",
        description=f"Added firewall rule: {data.action} {data.port}/{data.protocol}",
    )
    db.add(log)

    await db.flush()
    await db.refresh(rule)
    return {"id": rule.id, "message": "Firewall rule added"}


@router.delete("/rules/{rule_id}")
async def delete_firewall_rule(
    rule_id: int,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a firewall rule."""
    result = await db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    action_val = rule.action.value if hasattr(rule.action, 'value') else rule.action
    proto_val = rule.protocol.value if hasattr(rule.protocol, 'value') else rule.protocol
    await firewall_service.delete_rule_by_spec(action_val, rule.port, proto_val, rule.source_ip)

    await db.delete(rule)
    return {"message": "Firewall rule deleted"}


@router.post("/toggle")
async def toggle_firewall(
    enable: bool,
    user: User = Depends(require_admin),
):
    """Enable or disable the firewall."""
    if enable:
        result = await firewall_service.enable()
    else:
        result = await firewall_service.disable()
    return result
