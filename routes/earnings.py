from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from db import get_db
from schemas.earnings_schemas import VendorLedgerResponse, VendorEarningsSummary
from crud.earnings import get_vendor_ledger, get_vendor_earnings_summary

router = APIRouter(prefix="/api/rest/earnings", tags=["REST - Earnings & Vendor Ledger"])
logger = logging.getLogger(__name__)

@router.get("/lab/{lab_id}", response_model=List[VendorLedgerResponse])
def get_lab_ledger(lab_id: str, db: Session = Depends(get_db)):
    """Fetch the complete transaction history and earnings for a lab."""
    try:
        ledger = get_vendor_ledger(db, lab_id)
        return ledger
    except Exception as e:
        logger.error(f"Failed to fetch ledger for lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch earnings.")

@router.get("/lab/{lab_id}/summary", response_model=VendorEarningsSummary)
def get_lab_earnings_summary(lab_id: str, db: Session = Depends(get_db)):
    """Fetch the total aggregated earnings, pending, and settled amounts."""
    try:
        summary = get_vendor_earnings_summary(db, lab_id)
        return summary
    except Exception as e:
        logger.error(f"Failed to fetch earnings summary for lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch earnings summary.")
