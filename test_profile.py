import sys
from sqlalchemy.orm import Session
from db import SessionLocal
from models.customer import CustomerUser

db = SessionLocal()
customers = db.query(CustomerUser).all()
for c in customers:
    print(c.customer_id, c.profile_picture)
