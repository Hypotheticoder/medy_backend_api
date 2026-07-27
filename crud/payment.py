from sqlalchemy.orm import Session
from models.payment import PaymentTransaction

def create_payment_record(db: Session, order_id: str, razorpay_order_id: str, amount: float) -> PaymentTransaction:
    """Saves the initial 'created' intent to the database."""
    new_transaction = PaymentTransaction(
        order_id=order_id,
        razorpay_order_id=razorpay_order_id,
        amount=amount,
        status="created"
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def get_transaction_by_rzp_order_id(db: Session, razorpay_order_id: str) -> PaymentTransaction:
    """Finds the pending transaction when Razorpay sends the success signal."""
    return db.query(PaymentTransaction).filter(PaymentTransaction.razorpay_order_id == razorpay_order_id).first()

def mark_payment_successful(db: Session, transaction: PaymentTransaction, payment_id: str, signature: str):
    """Updates the ledger to prove the money arrived securely."""
    transaction.razorpay_payment_id = payment_id
    transaction.razorpay_signature = signature
    transaction.status = "paid"
    db.commit()
    db.refresh(transaction)
    return transaction
