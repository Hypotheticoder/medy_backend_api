from fastapi import APIRouter, Depends, HTTPException, status, Header, Form, UploadFile, File
from sqlalchemy.orm import Session
import logging
import os
import shutil
import firebase_admin
from firebase_admin import credentials, auth

from db import get_db
from utils.security import get_password_hash, verify_password, create_access_token

# Importing Models
from models.customer import CustomerUser, generate_customer_id
from models.pharma_shop import PharmaShopUser, generate_shop_id
from models.lab import LabUser, generate_lab_id

# Importing Schemas
from schemas.auth import (
    CustomerFirebaseLogin, 
    VendorLoginRequest, 
    TokenResponse,
    AdminCreateShopRequest,
    LabProfileResponse,
    AdminCreateLabRequest,
    CheckPhoneRequest
)

logger = logging.getLogger(__name__)

# ==========================================
# 🚀 INITIALIZE FIREBASE ADMIN
# ==========================================
# Ensure you have your downloaded JSON key in the root of your project!
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase-credentials.json")
        firebase_admin.initialize_app(cred)
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin: {e}")

router = APIRouter(prefix="/api/auth", tags=["Authentication & Onboarding"])

@router.post("/customer/check-phone")
def check_customer_phone(payload: CheckPhoneRequest, db: Session = Depends(get_db)):
    """
    Used by Flutter to check if a user exists BEFORE sending an OTP.
    Saves Firebase SMS costs by preventing unnecessary OTPs for dropped signups.
    """
    customer = db.query(CustomerUser).filter(CustomerUser.phone == payload.phone).first()
    return {
        "exists": customer is not None,
        "message": "User already registered" if customer else "New user"
    }

# ==========================================
# 1. CUSTOMER AUTHENTICATION (Firebase OTP)
# ==========================================
# 🚨 THE FIX: Replaced payload with a secure Authorization header
@router.post("/customer/login", response_model=TokenResponse)
def customer_login(authorization: str = Header(...), db: Session = Depends(get_db)):
    """
    Flutter app sends the Firebase ID Token in the Authorization header:
    "Bearer <firebase_id_token>"
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
    firebase_token = authorization.split("Bearer ")[1]
    
    try:
        # 1. Verify the token with Google's servers
        decoded_token = auth.verify_id_token(firebase_token)
        
        # 2. Extract the real UID and Phone Number from the verified token
        firebase_uid = decoded_token.get("uid")
        phone = decoded_token.get("phone_number")
        
        if not phone:
             raise HTTPException(status_code=400, detail="No phone number linked to this Firebase account")
             
    except Exception as e:
        logger.error(f"Firebase verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token")

    # 3. Find or Create the user in our PostgreSQL database
    customer = db.query(CustomerUser).filter(CustomerUser.phone == phone).first()
    
    if not customer:
        customer = CustomerUser(
            customer_id=generate_customer_id(),
            firebase_uid=firebase_uid,
            phone=phone,
            name="New User", # They can update this in their profile later
            status="active"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    elif customer.firebase_uid != firebase_uid:
        # Failsafe: Sync the UID if it changed (rare)
        customer.firebase_uid = firebase_uid
        db.commit()
    
    # 4. Generate Medy's own JWT Session Token
    access_token = create_access_token(data={"sub": customer.customer_id, "role": "customer"})
    
    return {
        "access_token": access_token, 
        "user_id": customer.customer_id, 
        "user_type": "customer"
    }

# ==========================================
# 2. ADMIN ROUTES (Creating Vendors)
# ==========================================
@router.post("/admin/register-shop")
def admin_register_shop(payload: AdminCreateShopRequest, db: Session = Depends(get_db)):
    """Admin route to onboard a pharmacy. Hashes the password securely."""
    # 1. Check if phone already exists
    existing = db.query(PharmaShopUser).filter(PharmaShopUser.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered to a shop.")
        
    # 2. Hash the raw password
    hashed_pwd = get_password_hash(payload.shop_password)
    
    # 3. Create the Shop (Dumping the Pydantic payload directly)
    shop_data = payload.model_dump(exclude={"shop_password"})
    new_shop = PharmaShopUser(
        shop_id=generate_shop_id(),
        shop_password=hashed_pwd,
        status="pending",
        is_verified=False,
        **shop_data # 🪄 Magic! Unpacks all the other fields automatically
    )
    
    db.add(new_shop)
    db.commit()
    db.refresh(new_shop)
    return {"status": "success", "message": "Shop created successfully", "shop_id": new_shop.shop_id}

@router.post("/admin/register-lab")
def admin_register_lab(
    phone: str = Form(...),
    owner_name: str = Form(...),
    lab_name: str = Form(...),
    address: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    license_number: str = Form(...),
    password: str = Form(...),
    pan_number: str = Form(...),
    nabl_accreditation_number: str = Form(...),
    gst_number: str = Form(None),
    emergency_contact_number: str = Form(None),
    whatsapp_number: str = Form(None),
    registration_certificate: UploadFile = File(...),
    bank_passbook: UploadFile = File(...),
    lab_image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Admin route to onboard a lab with file uploads. Hashes the password securely."""
    existing = db.query(LabUser).filter(LabUser.phone == phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered to a lab.")
        
    hashed_pwd = get_password_hash(password)
    
    lab_name_safe = "".join(c if c.isalnum() else "_" for c in lab_name)
    base_upload_path = os.path.join("uploads", lab_name_safe)
    os.makedirs(base_upload_path, exist_ok=True)

    def save_upload_file(upload_file: UploadFile, field_name: str) -> str:
        field_path = os.path.join(base_upload_path, field_name)
        os.makedirs(field_path, exist_ok=True)
        file_path = os.path.join(field_path, upload_file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return f"/uploads/{lab_name_safe}/{field_name}/{upload_file.filename}"

    registration_certificate_url = save_upload_file(registration_certificate, "registration_certificate")
    bank_passbook_url = save_upload_file(bank_passbook, "bank_passbook")
    lab_image_url = save_upload_file(lab_image, "lab_image") if lab_image else None

    new_lab = LabUser(
        lab_id=generate_lab_id(),
        phone=phone,
        owner_name=owner_name,
        lab_name=lab_name,
        address=address,
        latitude=latitude,
        longitude=longitude,
        license_number=license_number,
        password=hashed_pwd,
        pan_number=pan_number,
        nabl_accreditation_number=nabl_accreditation_number,
        gst_number=gst_number,
        emergency_contact_number=emergency_contact_number,
        whatsapp_number=whatsapp_number,
        registration_certificate_url=registration_certificate_url,
        bank_passbook_url=bank_passbook_url,
        lab_image=lab_image_url,
        status="pending",
        is_verified=False
    )
    
    db.add(new_lab)
    db.commit()
    db.refresh(new_lab)
    return {"status": "success", "message": "Lab created successfully", "lab_id": new_lab.lab_id}

# ==========================================
# 3. VENDOR LOGIN ROUTES
# ==========================================
@router.post("/shop/login", response_model=TokenResponse)
def shop_login(payload: VendorLoginRequest, db: Session = Depends(get_db)):
    """Pharmacy app uses this to log in and get a JWT token."""
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.phone == payload.phone).first()
    
    if not shop or not verify_password(payload.password, shop.shop_password):
        raise HTTPException(status_code=401, detail="Invalid phone number or password")
        
    if shop.status != "active" and shop.status != "pending":
        raise HTTPException(status_code=403, detail="Account is suspended.")

    access_token = create_access_token(data={"sub": shop.shop_id, "role": "shop"})
    return {"access_token": access_token, "user_id": shop.shop_id, "user_type": "shop"}

@router.post("/lab/login", response_model=TokenResponse)
def lab_login(payload: VendorLoginRequest, db: Session = Depends(get_db)):
    """Lab app uses this to log in and get a JWT token."""
    lab = db.query(LabUser).filter(LabUser.phone == payload.phone).first()
    
    if not lab or not verify_password(payload.password, lab.password):
        raise HTTPException(status_code=401, detail="Invalid phone number or password")
        
    if lab.status != "active" and lab.status != "pending":
        raise HTTPException(status_code=403, detail="Account is suspended.")

    access_token = create_access_token(data={"sub": lab.lab_id, "role": "lab"})
    return {"access_token": access_token, "user_id": lab.lab_id, "user_type": "lab"}

@router.get("/lab/get-by/{lab_id}", response_model=LabProfileResponse)
def get_lab_by_id(lab_id: str, db: Session = Depends(get_db)):
    """Fetch Lab Profile by ID"""
    lab = db.query(LabUser).filter(LabUser.lab_id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    return lab

@router.put("/lab/update-by/{lab_id}", response_model=LabProfileResponse)
def update_lab_profile(
    lab_id: str,
    email: str = Form(None),
    address: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    emergency_contact_number: str = Form(None),
    whatsapp_number: str = Form(None),
    is_accepting_bookings: bool = Form(None),
    lab_image: UploadFile = File(None),
    registration_certificate: UploadFile = File(None),
    bank_passbook: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Update Lab Profile settings (multipart)"""
    lab = db.query(LabUser).filter(LabUser.lab_id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
        
    if email is not None: lab.email = email
    if address is not None: lab.address = address
    if latitude is not None: lab.latitude = latitude
    if longitude is not None: lab.longitude = longitude
    if emergency_contact_number is not None: lab.emergency_contact_number = emergency_contact_number
    if whatsapp_number is not None: lab.whatsapp_number = whatsapp_number
    if is_accepting_bookings is not None: lab.is_accepting_bookings = is_accepting_bookings
    
    lab_name_safe = "".join(c if c.isalnum() else "_" for c in lab.lab_name)
    
    if lab_image:
        base_upload_path = os.path.join("uploads", lab_name_safe, "lab_image")
        os.makedirs(base_upload_path, exist_ok=True)
        file_path = os.path.join(base_upload_path, lab_image.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(lab_image.file, buffer)
        lab.lab_image = f"/uploads/{lab_name_safe}/lab_image/{lab_image.filename}"

    if registration_certificate:
        base_upload_path = os.path.join("uploads", lab_name_safe, "registration_certificate")
        os.makedirs(base_upload_path, exist_ok=True)
        file_path = os.path.join(base_upload_path, registration_certificate.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(registration_certificate.file, buffer)
        lab.registration_certificate_url = f"/uploads/{lab_name_safe}/registration_certificate/{registration_certificate.filename}"

    if bank_passbook:
        base_upload_path = os.path.join("uploads", lab_name_safe, "bank_passbook")
        os.makedirs(base_upload_path, exist_ok=True)
        file_path = os.path.join(base_upload_path, bank_passbook.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(bank_passbook.file, buffer)
        lab.bank_passbook_url = f"/uploads/{lab_name_safe}/bank_passbook/{bank_passbook.filename}"

    db.commit()
    db.refresh(lab)
    return lab
