import uuid
from sqlalchemy.orm import Session
from db import SessionLocal
from models.advertisement import Advertisement
from datetime import datetime, timezone

db = SessionLocal()

ad = Advertisement(
    id=str(uuid.uuid4()),
    title="Welcome to Medy24",
    image_url="https://via.placeholder.com/600x400.png?text=Special+Offer+1",
    target_url="https://flutter.dev",
    is_active=True,
    created_at=datetime.now(timezone.utc)
)
db.add(ad)

ad2 = Advertisement(
    id=str(uuid.uuid4()),
    title="Lab Test Discount",
    image_url="https://via.placeholder.com/600x400.png?text=Lab+Test+Discount",
    target_url="https://flutter.dev",
    is_active=True,
    created_at=datetime.now(timezone.utc)
)
db.add(ad2)

db.commit()
print("Advertisements seeded.")
