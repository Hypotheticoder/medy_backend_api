import strawberry
from typing import Optional
from strawberry.scalars import JSON

@strawberry.type
class MedicineType:
    """GraphQL representation of the Medicine catalog."""
    medicine_id: str
    medicine_name: str
    manufacturer: Optional[str]
    pack_form: str
    pack_size: str
    medicine_category: str
    medicine_photo: Optional[str]
    medicine_description: Optional[str]
    medicine_composition: Optional[str]
    precautions: Optional[JSON] # Strawberry safely passes JSON objects to the frontend
    mrp: float
    discount_percent: Optional[float]
    final_selling_price: float
    prescription_required: bool
