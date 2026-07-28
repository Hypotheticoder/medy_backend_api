from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from db import get_db
from models.lab_package import LabPackage
from schemas.lab_package_schemas import LabPackageCreate, LabPackageUpdate, LabPackageResponse
from typing import List

router = APIRouter(prefix="/api/rest/test-packages", tags=["REST - Test Packages"])
logger = logging.getLogger(__name__)

@router.post("/create", response_model=LabPackageResponse)
def create_test_package(payload: LabPackageCreate, db: Session = Depends(get_db)):
    try:
        new_package = LabPackage(**payload.model_dump())
        db.add(new_package)
        db.commit()
        db.refresh(new_package)
        return new_package
    except Exception as e:
        logger.error(f"Failed to create package: {e}")
        raise HTTPException(status_code=500, detail="Could not create package")

@router.get("/get-by-lab/{lab_id}")
def get_packages_by_lab(lab_id: str, db: Session = Depends(get_db)):
    packages = db.query(LabPackage).filter(LabPackage.lab_id == lab_id).all()
    # The frontend expects {"data": [...]}
    return {"data": [pkg for pkg in packages]}

@router.get("/get-by/{package_id}", response_model=LabPackageResponse)
def get_package_by_id(package_id: str, db: Session = Depends(get_db)):
    package = db.query(LabPackage).filter(LabPackage.package_id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    return package

@router.put("/update-by/{package_id}", response_model=LabPackageResponse)
def update_test_package(package_id: str, payload: LabPackageUpdate, db: Session = Depends(get_db)):
    package = db.query(LabPackage).filter(LabPackage.package_id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(package, key, value)
        
    db.commit()
    db.refresh(package)
    return package

@router.delete("/delete-by/{package_id}")
def delete_test_package(package_id: str, db: Session = Depends(get_db)):
    package = db.query(LabPackage).filter(LabPackage.package_id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    db.delete(package)
    db.commit()
    return {"status": "success", "message": "Package deleted successfully"}
