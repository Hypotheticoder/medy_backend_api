import csv
import io
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from db import get_db
from models.distributor import DistributorUser
from models.distributor_inventory import DistributorInventory
from models.medicine import Medicine
from models.b2b_purchase_order import B2BPurchaseOrder
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/distributor", tags=["Distributor Web Admin"])
logger = logging.getLogger(__name__)

# ==========================================
# 1. AUTH DEPENDENCY FOR DISTRIBUTORS
# ==========================================
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/distributor/login")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def get_current_distributor(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DistributorUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        distributor_id: str = payload.get("sub")
        role: str = payload.get("role")
        if not distributor_id or role != "distributor":
            raise HTTPException(status_code=401, detail="Invalid distributor credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    distributor = db.query(DistributorUser).filter(DistributorUser.distributor_id == distributor_id).first()
    if not distributor or not distributor.is_verified:
        raise HTTPException(status_code=403, detail="Distributor account not verified or inactive")
        
    return distributor

# ==========================================
# 2. BULK CSV INVENTORY UPLOAD (Marg/ERP Sync)
# ==========================================
@router.post("/inventory/bulk-upload")
async def bulk_upload_inventory(
    file: UploadFile = File(...),
    distributor: DistributorUser = Depends(get_current_distributor),
    db: Session = Depends(get_db)
):
    """
    Parses ERP CSV export and syncs with DistributorInventory.
    Expected CSV columns:
    medicine_name, batch_number, expiry_date (YYYY-MM-DD), ptr, mrp, stock_boxes, moq, gst_percentage
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    contents = await file.read()
    decoded = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    required = ["medicine_name", "batch_number", "expiry_date", "ptr", "mrp", "stock_boxes"]
    missing = [r for r in required if r not in headers]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required CSV columns: {missing}")

    actual_to_lower = {h: h.strip().lower() for h in (reader.fieldnames or [])}

    created_count = 0
    updated_count = 0
    skipped_rows = []

    for idx, row in enumerate(reader, start=1):
        clean_row = {actual_to_lower[k]: v.strip() for k, v in row.items() if k}
        med_name = clean_row.get("medicine_name")
        batch_no = clean_row.get("batch_number")

        if not med_name or not batch_no:
            skipped_rows.append({"row": idx, "reason": "Missing medicine name or batch number"})
            continue

        # 1. Match against master medicine dictionary
        master_med = db.query(Medicine).filter(Medicine.medicine_name.ilike(med_name)).first()
        if not master_med:
            skipped_rows.append({"row": idx, "medicine": med_name, "reason": "Medicine not found in Medy24 catalog"})
            continue

        # 2. Parse numbers and date
        try:
            ptr = float(clean_row.get("ptr", 0.0))
            mrp = float(clean_row.get("mrp", master_med.mrp))
            stock = int(clean_row.get("stock_boxes", 0))
            moq = int(clean_row.get("moq", 1))
            gst = float(clean_row.get("gst_percentage", 12.0))
            expiry = datetime.strptime(clean_row.get("expiry_date"), "%Y-%m-%d")
        except ValueError as e:
            skipped_rows.append({"row": idx, "medicine": med_name, "reason": f"Data parse error: {str(e)}"})
            continue

        # 3. Upsert: Update if distributor already has this batch, otherwise insert
        existing_item = db.query(DistributorInventory).filter(
            DistributorInventory.distributor_id == distributor.distributor_id,
            DistributorInventory.medicine_id == master_med.medicine_id,
            DistributorInventory.batch_number == batch_no
        ).first()

        if existing_item:
            existing_item.ptr = ptr
            existing_item.mrp = mrp
            existing_item.available_stock_boxes = stock
            existing_item.moq = moq
            existing_item.expiry_date = expiry
            existing_item.gst_percentage = gst
            existing_item.is_active = stock > 0
            updated_count += 1
        else:
            new_inv = DistributorInventory(
                distributor_id=distributor.distributor_id,
                medicine_id=master_med.medicine_id,
                batch_number=batch_no,
                expiry_date=expiry,
                ptr=ptr,
                mrp=mrp,
                gst_percentage=gst,
                available_stock_boxes=stock,
                moq=moq,
                is_active=stock > 0
            )
            db.add(new_inv)
            created_count += 1

    db.commit()

    return {
        "status": "success",
        "newly_added": created_count,
        "updated": updated_count,
        "skipped": len(skipped_rows),
        "skipped_details": skipped_rows[:10]  # Return first 10 skipped items for debugging
    }

# ==========================================
# 3. WHOLESALE ORDER FULFILLMENT
# ==========================================
class UpdatePOStatusRequest(BaseModel):
    new_status: str  # accepted, invoiced, dispatched, delivered, cancelled
    delivery_notes: Optional[str] = None

@router.get("/orders")
def get_incoming_purchase_orders(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    distributor: DistributorUser = Depends(get_current_distributor),
    db: Session = Depends(get_db)
):
    """Lists all incoming POs from local pharmacies."""
    query = db.query(B2BPurchaseOrder).filter(B2BPurchaseOrder.distributor_id == distributor.distributor_id)
    if status_filter:
        query = query.filter(B2BPurchaseOrder.po_status == status_filter)

    orders = query.order_by(B2BPurchaseOrder.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "po_id": o.po_id,
            "shop_id": o.shop_id,
            "items_count": len(o.items) if isinstance(o.items, list) else 0,
            "subtotal": o.subtotal,
            "cgst_amount": o.cgst_amount,
            "sgst_amount": o.sgst_amount,
            "total_invoice_amount": o.total_invoice_amount,
            "payment_terms": o.payment_terms,
            "po_status": o.po_status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": o.items
        }
        for o in orders
    ]

@router.put("/orders/{po_id}/status")
def update_po_status(
    po_id: str,
    payload: UpdatePOStatusRequest,
    distributor: DistributorUser = Depends(get_current_distributor),
    db: Session = Depends(get_db)
):
    """Updates order status as the warehouse packs and dispatches the delivery van."""
    po = db.query(B2BPurchaseOrder).filter(
        B2BPurchaseOrder.po_id == po_id,
        B2BPurchaseOrder.distributor_id == distributor.distributor_id
    ).first()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    valid_statuses = ["placed", "accepted", "invoiced", "dispatched", "delivered", "cancelled"]
    if payload.new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {valid_statuses}")

    if payload.new_status == "cancelled" and po.po_status != "cancelled":
        # Restore deducted stock back to inventory
        items = po.items if isinstance(po.items, list) else []
        for item in items:
            inventory = db.query(DistributorInventory).filter(
                DistributorInventory.inventory_id == item.get("inventory_id")
            ).first()
            if inventory:
                inventory.available_stock_boxes += item.get("qty_boxes", 0)
                if not inventory.is_active and inventory.available_stock_boxes > 0:
                    inventory.is_active = True

    po.po_status = payload.new_status
    if payload.delivery_notes:
        po.delivery_notes = payload.delivery_notes
    if payload.new_status == "delivered":
        po.delivered_at = datetime.utcnow()

    db.commit()
    db.refresh(po)

    return {"status": "success", "po_id": po.po_id, "updated_status": po.po_status}

@router.get("/dashboard/summary")
def get_distributor_dashboard_summary(
    distributor: DistributorUser = Depends(get_current_distributor),
    db: Session = Depends(get_db)
):
    orders = db.query(B2BPurchaseOrder).filter(
        B2BPurchaseOrder.distributor_id == distributor.distributor_id
    ).all()

    total_gross_revenue = sum(o.total_invoice_amount for o in orders if o.po_status not in ["cancelled", "rejected"])
    pending_dispatch = sum(1 for o in orders if o.po_status in ["placed", "accepted", "invoiced"])
    delivered_orders = sum(1 for o in orders if o.po_status == "delivered")
    
    # Net-15 / Net-30 Outstanding Credit
    unpaid_credit_dues = sum(
        o.total_invoice_amount for o in orders 
        if o.payment_terms in ["net_15", "net_30"] and o.payment_status == "pending" and o.po_status != "cancelled"
    )

    # Low stock alert (batches with less than 10 boxes remaining)
    low_stock_count = db.query(DistributorInventory).filter(
        DistributorInventory.distributor_id == distributor.distributor_id,
        DistributorInventory.is_active == True,
        DistributorInventory.available_stock_boxes <= 10
    ).count()

    return {
        "total_revenue": round(total_gross_revenue, 2),
        "delivered_orders": delivered_orders,
        "pending_dispatch": pending_dispatch,
        "outstanding_credit_dues": round(unpaid_credit_dues, 2),
        "low_stock_batches": low_stock_count
    }
