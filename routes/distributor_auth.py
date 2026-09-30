import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import EmailStr, BaseModel
from typing import Optional

from db import get_db
from models.distributor import DistributorUser
from utils.security import get_password_hash, verify_password, create_access_token
from utils.id_gen import generate_ulid

router = APIRouter(prefix="/api/v1/distributor/auth", tags=["Distributor Auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_distributor(
    company_name: str = Form(...),
    owner_name: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    address: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    gstin_no: str = Form(...),
    pan_number: str = Form(...),
    email: Optional[EmailStr] = Form(None),
    bank_account_no: Optional[str] = Form(None),
    bank_ifsc_code: Optional[str] = Form(None),
    license_20b_doc: UploadFile = File(...),
    license_21b_doc: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Onboard a wholesale distributor. Account starts in 'pending' status 
    until Super Admin verifies Form 20B and 21B licenses.
    """
    # Duplicate check
    existing = db.query(DistributorUser).filter(
        (DistributorUser.phone == phone) | 
        (DistributorUser.gstin_no == gstin_no)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Distributor with this phone or GSTIN already exists.")

    dist_id = generate_ulid("DS")
    safe_name = "".join(c if c.isalnum() else "_" for c in company_name)
    base_upload_path = os.path.join("uploads", "distributors", safe_name)
    os.makedirs(base_upload_path, exist_ok=True)

    def save_file(upload_file: UploadFile, subfolder: str) -> str:
        folder = os.path.join(base_upload_path, subfolder)
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f"{dist_id}_{upload_file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return f"/{file_path}"

    url_20b = save_file(license_20b_doc, "license_20b")
    url_21b = save_file(license_21b_doc, "license_21b")

    new_distributor = DistributorUser(
        distributor_id=dist_id,
        phone=phone,
        email=email,
        company_name=company_name,
        owner_name=owner_name,
        password=get_password_hash(password),
        address=address,
        latitude=latitude,
        longitude=longitude,
        gstin_no=gstin_no.upper().strip(),
        pan_number=pan_number.upper().strip(),
        wholesale_drug_license_20b=url_20b,
        wholesale_drug_license_21b=url_21b,
        bank_account_no=bank_account_no,
        bank_ifsc_code=bank_ifsc_code,
        status="pending",
        is_verified=False
    )
    
    db.add(new_distributor)
    db.commit()
    db.refresh(new_distributor)
    
    return {
        "status": "success",
        "message": "Registration submitted. Pending Super Admin verification.",
        "distributor_id": new_distributor.distributor_id
    }


class DistributorLoginPayload(BaseModel):
    phone: str
    password: str

@router.post("/login")
def distributor_login(payload: DistributorLoginPayload, db: Session = Depends(get_db)):
    """Logs in verified distributors and issues a scoped JWT."""
    distributor = db.query(DistributorUser).filter(DistributorUser.phone == payload.phone).first()
    
    if not distributor or not verify_password(payload.password, distributor.password):
        raise HTTPException(status_code=401, detail="Invalid phone or password.")
        
    if not distributor.is_verified:
        raise HTTPException(status_code=403, detail="Account is pending verification by Super Admin.")
        
    if distributor.status != "active":
        raise HTTPException(status_code=403, detail="Account suspended.")

    access_token = create_access_token(data={"sub": distributor.distributor_id, "role": "distributor"})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "distributor_id": distributor.distributor_id,
        "company_name": distributor.company_name
    }
