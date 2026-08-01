from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import logging
import json

from db import get_db
from crud.lab_booking import create_lab_booking
from schemas.lab_booking_schemas import LabBookingCreate
from models.lab import LabUser
from routes.websockets import redis_manager 

router = APIRouter(prefix="/api/rest/lab-bookings", tags=["REST - Lab Bookings"])
logger = logging.getLogger(__name__)

@router.post("/book")
async def place_lab_booking(
    customer_id: str, 
    payload: LabBookingCreate,
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Called by the Flutter app when the user hits 'Confirm Booking'.
    Saves the booking and instantly pings the Lab via WebSockets.
    """
    # 1. Verify the Lab exists
    lab = db.query(LabUser).filter(LabUser.lab_id == payload.lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Selected Lab not found")

    # 2. Create the Booking using our clean CRUD function
    new_booking = create_lab_booking(db, customer_id, payload)

    # 3. Fire a Redis WebSocket Ping to the specific Lab so their phone rings!
    async def notify_lab():
        await redis_manager.connect()
        # Publish directly to this specific lab's channel
        channel_name = f"lab_orders:{new_booking.lab_id}"
        await redis_manager.redis_client.publish(
            channel_name, 
            json.dumps({
                "type": "NEW_LAB_BOOKING",
                "booking": new_booking.to_dict()
            })
        )

    background_tasks.add_task(notify_lab)

    # Return success and the Lab's phone number so the success screen can show the "Call Now" button!
    return {
        "status": "success",
        "booking_id": new_booking.booking_id,
        "lab_phone": lab.phone,
        "message": "Booking confirmed and sent to the lab."
    }

from crud.lab_booking import update_booking_status, delete_lab_booking, update_lab_booking_details
from schemas.lab_booking_schemas import LabBookingStatusUpdate, LabBookingDetailsUpdate

@router.put("/status/{booking_id}")
def update_lab_booking_status(booking_id: str, payload: LabBookingStatusUpdate, db: Session = Depends(get_db)):
    """
    Called by the Lab to update the booking state (e.g. sample_collected, processing).
    """
    updated_booking = update_booking_status(db, booking_id, payload.new_status, payload.cancellation_reason)
    if not updated_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        "status": "success",
        "message": f"Booking status updated to {payload.new_status}",
        "booking": updated_booking.to_dict()
    }

@router.put("/details/{booking_id}")
def update_booking_details(booking_id: str, payload: LabBookingDetailsUpdate, db: Session = Depends(get_db)):
    """
    Called by the Lab to update the booking details (patient info, price, payment mode).
    """
    updated_booking = update_lab_booking_details(db, booking_id, payload)
    if not updated_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        "status": "success",
        "message": "Booking details updated",
        "booking": updated_booking.to_dict()
    }

@router.delete("/{booking_id}")
def delete_booking(booking_id: str, db: Session = Depends(get_db)):
    """
    Deletes a lab booking by ID.
    """
    success = delete_lab_booking(db, booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    return {
        "status": "success",
        "message": "Booking deleted successfully"
    }

from models.lab_booking import LabBooking

@router.get("/lab/{lab_id}")
def get_bookings_by_lab(lab_id: str, db: Session = Depends(get_db)):
    bookings = db.query(LabBooking).filter(LabBooking.lab_id == lab_id).all()
    return {
        "count": len(bookings),
        "lab_id": lab_id,
        "bookings": [b.to_dict() for b in bookings]
    }

@router.get("/customer/{customer_id}")
def get_bookings_by_customer(customer_id: str, db: Session = Depends(get_db)):
    bookings = db.query(LabBooking).filter(LabBooking.customer_id == customer_id).order_by(LabBooking.created_at.desc()).all()
    return {
        "count": len(bookings),
        "customer_id": customer_id,
        "bookings": [b.to_dict() for b in bookings]
    }

@router.get("/{booking_id}")
def get_booking_details(booking_id: str, db: Session = Depends(get_db)):
    booking = db.query(LabBooking).filter(LabBooking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking.to_dict()
