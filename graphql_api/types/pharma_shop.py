import strawberry
from typing import Optional

@strawberry.type
class PharmaShopType:
    """GraphQL representation of a Pharmacy Shop (Safe fields only, no passwords!)."""
    shop_id: str
    shop_name: str
    owner_name: str
    shop_image: Optional[str]
    address: str
    latitude: float
    longitude: float
    is_verified: bool
    is_accepting_orders: bool
    rating: float
    phone: str
    whatsapp_number: Optional[str]
    license_number: str
    gstin_no: Optional[str]
    drug_license_upload: Optional[str]
    pan_card_upload: Optional[str]
    registration_certificate_upload: Optional[str]
    bank_account_no: Optional[str]
    bank_ifsc_code: Optional[str]
    bank_name: Optional[str]
    status: str
