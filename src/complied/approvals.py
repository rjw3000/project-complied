"""Pure approval policy. Authentication and persistence remain unimplemented."""
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class Purpose(Enum):
    FILING = "filing"
    PAYMENT = "payment"

@dataclass(frozen=True)
class Package:
    entity: str
    jurisdiction: str
    period: str
    version: str
    amount: Decimal
    destination: str

@dataclass(frozen=True)
class Approval:
    package: Package
    purpose: Purpose
    actor: str
    revoked: bool = False

def may_execute(package: Package, approval: Approval | None, purpose: Purpose,
                *, adapter_verified: bool, unresolved_exceptions: int,
                outcome_unknown: bool = False) -> bool:
    """Deny stale, wrong-purpose, unverified, or ambiguous operations."""
    return bool(
        approval is not None and approval.actor and not approval.revoked
        and approval.package == package and approval.purpose is purpose
        and adapter_verified and unresolved_exceptions == 0
        and not outcome_unknown and package.amount.is_finite()
        and package.amount >= 0
        and all((package.entity, package.jurisdiction, package.period,
                 package.version, package.destination))
    )
