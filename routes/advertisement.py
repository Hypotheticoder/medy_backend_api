import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from db import get_db
from models.advertisement import Advertisement
from schemas.advertisement import AdvertisementResponse

router = APIRouter(
    prefix="/advertisements",
    tags=["Advertisements"],
)

@router.get("/", response_model=List[AdvertisementResponse])
def get_active_advertisements(db: Session = Depends(get_db)):
    """Fetch all active advertisements."""
    return db.query(Advertisement).filter(Advertisement.is_active == True).all()

@router.post("/admin", response_model=AdvertisementResponse)
async def create_advertisement(
    title: str = Form(...),
    target_url: Optional[str] = Form(None),
    is_active: bool = Form(True),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create a new advertisement (Admin only)."""
    os.makedirs("uploads/advertisements", exist_ok=True)
    file_id = str(uuid.uuid4())
    file_ext = image.filename.split(".")[-1] if "." in image.filename else "jpg"
    file_path = f"uploads/advertisements/{file_id}.{file_ext}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = f"/{file_path}"
    
    ad = Advertisement(
        id=str(uuid.uuid4()),
        title=title,
        image_url=image_url,
        target_url=target_url,
        is_active=is_active
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return ad

@router.delete("/admin/{ad_id}")
def delete_advertisement(ad_id: str, db: Session = Depends(get_db)):
    """Delete an advertisement."""
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    db.delete(ad)
    db.commit()
    return {"message": "Advertisement deleted successfully"}
