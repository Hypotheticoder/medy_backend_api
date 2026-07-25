from datetime import datetime
from typing import Optional, List
import strawberry

@strawberry.type
class LabTestPricingType:
    """Represents a specific lab's pricing and logistics for a test."""
    id: str
    lab_id: str
    test_id: str
    mrp: float
    discount_percent: float
    final_price: float
    turnaround_time_hours: int
    home_collection_available: bool
    walk_in_available: bool

@strawberry.type
class LabTestType:
    """GraphQL representation of the Global Lab Test Catalog."""
    test_id: str
    test_name: str
    category: str
    description: Optional[str]
    is_profile: bool
    number_of_parameters: int
    sample_type: Optional[str]
    search_tags: Optional[str] # Added for completeness
    fasting_required: bool
    fasting_hours: Optional[str]
    pre_test_info: Optional[str]

# ==========================================
# NEW: SMART MATCHING TYPES
# ==========================================
@strawberry.type
class MatchedTestType:
    test_id: str
    test_name: str
    price: float

@strawberry.type
class MissingTestType:
    test_id: str
    test_name: str

@strawberry.type
class LabPackageType:
    """The genius response type for the multi-test cart."""
    lab_id: str
    lab_name: str
    rating: float
    total_price: float
    matched_tests: List[MatchedTestType]
    missing_tests: List[MissingTestType]
    is_full_match: bool
    match_count: int
