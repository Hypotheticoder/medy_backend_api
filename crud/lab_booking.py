from sqlalchemy.orm import Session
from models.lab_booking import LabBooking, generate_booking_id
from schemas.lab_booking_schemas import LabBookingCreate, LabBookingDetailsUpdate
from crud.earnings import generate_earning_record

def create_lab_booking(db: Session, customer_id: str, booking_data: LabBookingCreate) -> LabBooking:
    """Saves the customer's lab booking securely into the database."""
    # Convert Pydantic model to dict, handling nested items
    db_data = booking_data.model_dump()
    
    db_booking = LabBooking(
        booking_id=generate_booking_id(),
        customer_id=customer_id,
        booking_status="pending",
        payment_status="pending",
        **db_data
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def update_booking_status(db: Session, booking_id: str, new_status: str, cancellation_reason: str = None) -> LabBooking:
    """Called by the Pathology Lab when they update the status."""
    booking = db.query(LabBooking).filter(LabBooking.booking_id == booking_id).first()
    if booking:
        booking.booking_status = new_status
        if new_status == "cancelled" and cancellation_reason:
            booking.cancellation_reason = cancellation_reason
            
        db.commit()
        db.refresh(booking)
        
        if new_status in ["accepted", "sample_collected", "processing", "report_ready", "completed"]:
            generate_earning_record(
                db=db,
                vendor_id=booking.lab_id,
                vendor_type="lab",
                order_id=booking.booking_id,
                total_amount=booking.total_price
            )
            
    return booking

def attach_report_url(db: Session, booking_id: str, file_url: str) -> LabBooking:
    """Called when the Pathology Lab uploads the final PDF report."""
    booking = db.query(LabBooking).filter(LabBooking.booking_id == booking_id).first()
    if booking:
        booking.report_url = file_url
        booking.booking_status = "report_ready" # Auto-update status
        db.commit()
        db.refresh(booking)
        
        # 🚨 GENERATE EARNINGS 🚨
        # When the report is ready, the service is considered fully delivered.
        generate_earning_record(
            db=db,
            vendor_id=booking.lab_id,
            vendor_type="lab",
            order_id=booking.booking_id,
            total_amount=booking.total_price
        )
        
    return booking

def delete_lab_booking(db: Session, booking_id: str) -> bool:
    """Deletes a lab booking from the database."""
    booking = db.query(LabBooking).filter(LabBooking.booking_id == booking_id).first()
    if booking:
        db.delete(booking)
        db.commit()
        return True
    return False

def update_lab_booking_details(db: Session, booking_id: str, payload: LabBookingDetailsUpdate) -> LabBooking:
    booking = db.query(LabBooking).filter(LabBooking.booking_id == booking_id).first()
    if booking:
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(booking, key, value)
        db.commit()
        db.refresh(booking)
    return booking
