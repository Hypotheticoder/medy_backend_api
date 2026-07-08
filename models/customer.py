from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList
from db import Base
import uuid

def generate_customer_id():
    return f"CUST-{uuid.uuid4().hex[:8].upper()}"

class CustomerUser(Base):
    __tablename__ = "customer_users"

    customer_id = Column(String, primary_key=True, index=True, default=generate_customer_id)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True)
    profile_picture = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False) # active, suspended, deleted
    saved_addresses = Column(MutableList.as_mutable(JSON), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "phone": self.phone,
            "name": self.name,
            "email": self.email,
            "profile_picture": self.profile_picture,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
