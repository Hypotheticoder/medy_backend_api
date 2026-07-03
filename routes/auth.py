from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import logging
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
def admin_register_lab(payload: AdminCreateLabRequest, db: Session = Depends(get_db)):
    """Admin route to onboard a lab. Hashes the password securely."""
    existing = db.query(LabUser).filter(LabUser.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered to a lab.")
        
    hashed_pwd = get_password_hash(payload.password)
    
    lab_data = payload.model_dump(exclude={"password"})
    new_lab = LabUser(
        lab_id=generate_lab_id(),
        password=hashed_pwd,
        status="pending",
        is_verified=False,
        **lab_data # 🪄 Magic! Unpacks all the fields
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
