from sqlalchemy.orm import Session
from models.distributor import DistributorUser
from schemas.distributor import DistributorCreate
import bcrypt # Assuming you are using bcrypt for password hashing

def get_distributor(db: Session, distributor_id: str):
    return db.query(DistributorUser).filter(DistributorUser.distributor_id == distributor_id).first()

def get_distributor_by_phone(db: Session, phone: str):
    return db.query(DistributorUser).filter(DistributorUser.phone == phone).first()

def create_distributor(db: Session, distributor: DistributorCreate):
    # Hash the password before saving
    hashed_password = bcrypt.hashpw(distributor.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    distributor_data = distributor.model_dump()
    distributor_data["password"] = hashed_password
    
    db_distributor = DistributorUser(**distributor_data)
    db.add(db_distributor)
    db.commit()
    db.refresh(db_distributor)
    return db_distributor
