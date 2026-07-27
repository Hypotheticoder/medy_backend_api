from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import razorpay
import os
from db import get_db
from models.payment import PaymentTransaction
from schemas.payment_schemas import RazorpayOrderCreate, RazorpayVerifyRequest, RazorpayOrderResponse
from crud.payment import create_payment_record, get_transaction_by_rzp_order_id, mark_payment_successful

router = APIRouter(prefix="/api/payments/razorpay", tags=["Razorpay Payments"])

# Your Razorpay Credentials (Store these securely in your .env file)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_your_key_here")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "your_secret_here")

# Initialize the official Razorpay Client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@router.post("/create-order", response_model=RazorpayOrderResponse)
def create_razorpay_order(payload: RazorpayOrderCreate, db: Session = Depends(get_db)):
    """
    Step 1: Flutter app says the customer wants to checkout.
    """
    try:
        # 🚨 CRITICAL: Razorpay expects the amount in PAISE, not Rupees. 
        amount_in_paise = int(payload.amount * 100)
        
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": payload.internal_receipt_id,
            "payment_capture": 1 # 1 = Automatically capture the money
        }
        
        # 1. Ask Razorpay to create the order
        razorpay_order = client.order.create(data=order_data)
        
        # 2. Save this intent in our PostgreSQL database using our clean CRUD function
        create_payment_record(
            db=db, 
            order_id=payload.internal_receipt_id, 
            razorpay_order_id=razorpay_order["id"], 
            amount=payload.amount
        )
        
        # 3. Return the Razorpay Order ID to the Flutter app!
        return {
            "status": "success",
            "razorpay_order_id": razorpay_order["id"],
            "amount": payload.amount,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
def verify_payment(payload: RazorpayVerifyRequest, db: Session = Depends(get_db)):
    """
    Step 2: After the UI payment screen closes, Flutter sends the data here.
    """
    try:
        # 1. Use Razorpay's SDK to verify the cryptographically signed response
        client.utility.verify_payment_signature({
            'razorpay_order_id': payload.razorpay_order_id,
            'razorpay_payment_id': payload.razorpay_payment_id,
            'razorpay_signature': payload.razorpay_signature
        })
        
        # 2. If it doesn't crash, the payment is 100% genuine! Update our DB.
        transaction = get_transaction_by_rzp_order_id(db, payload.razorpay_order_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found in our database")
            
        mark_payment_successful(
            db=db, 
            transaction=transaction, 
            payment_id=payload.razorpay_payment_id, 
            signature=payload.razorpay_signature
        )
        
        # 🚨 TODO: Update your `MedicineOrder` or `LabBooking` status to "paid" right here!
        
        return {"status": "success", "message": "Payment securely verified and captured."}
        
    except razorpay.errors.SignatureVerificationError:
        # Hackers tried to fake a payment success
        raise HTTPException(status_code=400, detail="Invalid Payment Signature. Fraud detected.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
