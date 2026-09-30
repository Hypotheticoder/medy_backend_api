from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from db import get_db
from models.distributor import DistributorUser

router = APIRouter(prefix="/api/v1/admin/b2b", tags=["Super Admin - B2B Governance"])

class DistributorVerificationAction(BaseModel):
    is_approved: bool
    rejection_reason: Optional[str] = None

@router.get("/distributors/pending")
def list_pending_distributors(db: Session = Depends(get_db)):
    """Fetches all distributors awaiting KYC and drug license verification."""
    pending = db.query(DistributorUser).filter(
        DistributorUser.status == "pending",
        DistributorUser.is_verified == False
    ).order_by(DistributorUser.created_at.desc()).all()
    
    return [
        {
            "distributor_id": d.distributor_id,
            "company_name": d.company_name,
            "owner_name": d.owner_name,
            "phone": d.phone,
            "gstin_no": d.gstin_no,
            "pan_number": d.pan_number,
            "license_20b_url": d.wholesale_drug_license_20b,
            "license_21b_url": d.wholesale_drug_license_21b,
            "address": d.address,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in pending
    ]

@router.put("/distributors/{distributor_id}/verify")
def verify_distributor(
    distributor_id: str, 
    payload: DistributorVerificationAction, 
    db: Session = Depends(get_db)
):
    """Admin approves or rejects wholesale compliance documents."""
    distributor = db.query(DistributorUser).filter(DistributorUser.distributor_id == distributor_id).first()
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")

    if payload.is_approved:
        distributor.is_verified = True
        distributor.status = "active"
        message = f"Distributor {distributor.company_name} is now approved and live."
    else:
        distributor.is_verified = False
        distributor.status = "rejected"
        message = f"Distributor rejected. Reason: {payload.rejection_reason or 'Non-compliant documents'}"

    db.commit()
    db.refresh(distributor)
    
    return {
        "status": "success",
        "distributor_id": distributor.distributor_id,
        "account_status": distributor.status,
        "is_verified": distributor.is_verified,
        "message": message
    }
