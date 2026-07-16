from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
import os
import shutil

from utils.security import get_password_hash
from db import get_db
from models.pharma_shop import PharmaShopUser, generate_shop_id
from schemas.pharma_shop import PharmaShopCreate, PharmaShopUpdate

router = APIRouter(prefix="/api/rest/shops", tags=["REST - Pharmacy Back-Office"])
logger = logging.getLogger(__name__)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_shop(payload: PharmaShopCreate, db: Session = Depends(get_db)):
    """
    Step 1: Pharmacy submits their registration details. 
    They are saved with status="pending" and cannot receive orders until Admin approves.
    """
    try:
        # Check if phone already exists
        existing_shop = db.query(PharmaShopUser).filter(PharmaShopUser.phone == payload.phone).first()
        if existing_shop:
            raise HTTPException(status_code=400, detail="Phone number is already registered.")

        # Convert Pydantic payload to dictionary
        shop_data = payload.dict()
        
        # Pop the raw password and hash it securely!
        raw_password = shop_data.pop("shop_password")
        hashed_pw = get_password_hash(raw_password)

        new_shop = PharmaShopUser(
            shop_id=generate_shop_id(),
            shop_password=hashed_pw,
            **shop_data
        )
        
        db.add(new_shop)
        db.commit()
        db.refresh(new_shop)
        
        return {
            "status": "success",
            "message": "Registration successful. Your account is pending admin approval.",
            "shop_id": new_shop.shop_id
        }
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Database error: Duplicate email, phone, or license number.")
    except Exception as e:
        db.rollback()
        logger.error(f"Shop registration failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{shop_id}/update-profile")
async def update_shop_profile(shop_id: str, payload: PharmaShopUpdate, db: Session = Depends(get_db)):
    """
    Step 2: Pharmacy updates their profile (e.g., changing their WhatsApp number).
    """
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    update_data = payload.dict(exclude_unset=True) # Only update fields they actually sent
    
    for key, value in update_data.items():
        setattr(shop, key, value)
        
    db.commit()
    db.refresh(shop)
    
    return {"status": "success", "message": "Profile updated successfully"}

@router.put("/admin/{shop_id}/approve")
async def admin_approve_shop(shop_id: str, db: Session = Depends(get_db)):
    """
    Step 3: The Admin (You) reviews their uploaded documents and approves the shop.
    This switches them to 'active' and 'is_verified = True' so they can start getting bids.
    """
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")
        
    shop.status = "active"
    shop.is_verified = True
    
    db.commit()
    return {"status": "success", "message": f"Shop {shop.shop_name} is now live and verified!"}

@router.post("/{shop_id}/upload-documents")
async def upload_shop_documents(
    shop_id: str,
    shop_image: UploadFile = File(None),
    drug_license_upload: UploadFile = File(None),
    pan_card_upload: UploadFile = File(None),
    registration_certificate_upload: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Upload files for a specific shop. Files are saved to:
    uploads/<shop_name>/<field_name>/<filename>
    """
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found.")

    shop_name_safe = "".join(c if c.isalnum() else "_" for c in shop.shop_name)
    base_upload_path = os.path.join("uploads", shop_name_safe)
    os.makedirs(base_upload_path, exist_ok=True)

    def save_upload_file(upload_file: UploadFile, field_name: str) -> str:
        field_path = os.path.join(base_upload_path, field_name)
        os.makedirs(field_path, exist_ok=True)
        file_path = os.path.join(field_path, upload_file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        # Return URL path
        return f"/uploads/{shop_name_safe}/{field_name}/{upload_file.filename}"

    updates = {}
    if shop_image:
        updates["shop_image"] = save_upload_file(shop_image, "shop_image")
    if drug_license_upload:
        updates["drug_license_upload"] = save_upload_file(drug_license_upload, "drug_license_upload")
    if pan_card_upload:
        updates["pan_card_upload"] = save_upload_file(pan_card_upload, "pan_card_upload")
    if registration_certificate_upload:
        updates["registration_certificate_upload"] = save_upload_file(registration_certificate_upload, "registration_certificate_upload")

    if updates:
        for key, value in updates.items():
            setattr(shop, key, value)
        db.commit()
        db.refresh(shop)

    return {"status": "success", "message": "Documents uploaded successfully", "updates": updates}
