import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from db import Base

class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    target_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
