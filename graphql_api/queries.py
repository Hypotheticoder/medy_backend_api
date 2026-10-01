import strawberry
from typing import List, Optional
from strawberry.types import Info
from sqlalchemy import or_, func

from graphql_api.types import MedicineType, OrderType, PharmaShopType, CartType
from graphql_api.types import LabBookingType, LabTestType, LabPackageType, MatchedTestType, MissingTestType, LabUserType, VendorLedgerType, DashboardEarningsType, FeaturedPackageType, B2BMedicineType
from graphql_api.types.b2b_types import DistributorCatalogItemType, B2BPurchaseOrderType
from graphql_api.types.lab_test import LabInventoryItemType

from models.medicine import Medicine
from models.order import Order
from models.pharma_shop import PharmaShopUser
from models.cart import Cart
from models.lab import LabUser
from models.lab_test import LabTest
from models.lab_test_pricing import LabTestPricing
from models.lab_booking import LabBooking
from models.distributor_inventory import DistributorInventory
from models.b2b_purchase_order import B2BPurchaseOrder
from models.b2b_cart import B2BCart
from graphql_api.types.b2b_types import B2BCartResponseType, NearbyDistributorType

@strawberry.type
class Query:
    
    @strawberry.field
    def get_popular_brands(self, info: Info, limit: int = 20) -> List[str]:
        """Fetches a list of popular manufacturers/brands."""
        db = info.context["db"]
        from models.medicine import Medicine
        brands = db.query(Medicine.manufacturer).filter(
            Medicine.manufacturer.isnot(None),
            Medicine.manufacturer != ""
        ).distinct().limit(limit).all()
        return [brand[0] for brand in brands if brand[0]]

    @strawberry.field
    def get_featured_packages(self, info: Info, limit: int = 5) -> List[FeaturedPackageType]:
        """Powers the 'Health Packages For You' carousel on the Home Screen."""
        db = info.context["db"]
        
        # 1. Find packages that are NOT lab-branded (Admin packages only)
        global_packages = db.query(LabTest).filter(
            LabTest.is_package == True,
            LabTest.category != "Lab Branded Packages"
        ).limit(limit).all()
        
        results = []
        for pkg in global_packages:
            # 2. Find the cheapest price any lab is currently offering for this package
            cheapest_pricing = db.query(func.min(LabTestPricing.customer_selling_price)).filter(
                LabTestPricing.test_id == pkg.test_id
            ).scalar()
            
            # Default to 0 if no lab is selling it yet
            starting_price = cheapest_pricing if cheapest_pricing is not None else 0.0
            
            results.append(FeaturedPackageType(
                test_id=pkg.test_id,
                test_name=pkg.test_name,
                number_of_parameters=pkg.number_of_parameters,
                starting_price=starting_price,
                category=pkg.category
            ))
            
        return results
    
    @strawberry.field
    def search_medicines(
        self, 
        info: Info, 
        query: Optional[str] = None, 
        category: Optional[str] = None,
        limit: int = 20, 
        offset: int = 0
    ) -> List[MedicineType]:
        """
        Allows the Flutter app to search the global catalog by name or category.
        Usage: query { searchMedicines(query: "Dolo", limit: 10) { medicineName mrp } }
        """
        db = info.context["db"]
        db_query = db.query(Medicine)
        
        if query:
            from sqlalchemy import case
            # Case-insensitive search using ILIKE
            db_query = db_query.filter(Medicine.medicine_name.ilike(f"%{query}%"))
            # Sort exact matches first, then prefix matches, then others
            db_query = db_query.order_by(
                case(
                    (Medicine.medicine_name.ilike(query), 1),
                    (Medicine.medicine_name.ilike(f"{query} %"), 2),
                    (Medicine.medicine_name.ilike(f"{query}%"), 3),
                    else_=4
                ),
                Medicine.medicine_name.asc()
            )
        
        if category:
            db_query = db_query.filter(Medicine.medicine_category == category)
            
        return db_query.offset(offset).limit(limit).all()

    @strawberry.field
    def get_my_order_history(self, info: Info, customer_id: str, limit: int = 10) -> List[OrderType]:
        """
        Fetches the order history for a specific customer.
        """
        db = info.context["db"]
        return db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.created_at.desc()).limit(limit).all()

    @strawberry.field
    def get_medicine_by_id(self, info: Info, medicine_id: str) -> Optional[MedicineType]:
        db = info.context["db"]
        return db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()

    @strawberry.field
    def get_shop_profile(self, info: Info, shop_id: str) -> Optional[PharmaShopType]:
        """
        Allows the customer to click on a bidding pharmacy and see their profile/rating.
        """
        db = info.context["db"]
        return db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == shop_id).first()

    @strawberry.field
    def get_lab_profile(self, info: Info, lab_id: str) -> Optional[LabUserType]:
        """
        Allows the customer (or the lab app itself) to fetch a lab's profile.
        """
        db = info.context["db"]
        return db.query(LabUser).filter(LabUser.lab_id == lab_id).first()


    @strawberry.field
    def get_active_shops_nearby(self, info: Info, lat: float, lng: float) -> List[PharmaShopType]:
        """
        Fetches shops to show on the map (Basic implementation).
        In production, you'd use PostGIS (ST_Distance) here.
        """
        db = info.context["db"]
        # Basic filter returning highly rated verified shops that are online
        return db.query(PharmaShopUser).filter(
            PharmaShopUser.is_verified == True,
            PharmaShopUser.is_accepting_orders == True
        ).order_by(PharmaShopUser.rating.desc()).limit(10).all()

    @strawberry.field
    def get_my_cart(self, info: Info, customer_id: str) -> CartType:
        """
        Fetches the customer's cart for the UI Badge or Cart Screen.
        """
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        
        if not cart:
            # Ghost cart generation: If they don't have a cart, return an empty one
            # so the Flutter app doesn't crash with a Null error.
            return CartType(
                cart_id="empty",
                customer_id=customer_id,
                items=[],
                total_price=0.0,
                updated_at=None
            )
        return cart

    # ==========================================
    # LAB SEARCH QUERIES
    # ==========================================

    @strawberry.field
    def get_all_global_tests(self, info: Info, limit: int = 20, offset: int = 0) -> List[LabTestType]:
        db = info.context["db"]
        return db.query(LabTest).order_by(LabTest.test_name.asc()).offset(offset).limit(limit).all()
        
    @strawberry.field
    def get_core_test_by_id(self, info: Info, test_id: str) -> Optional[LabTestType]:
        db = info.context["db"]
        return db.query(LabTest).filter(LabTest.test_id == test_id).first()


    @strawberry.field
    def get_lab_test_categories(self, info: Info, limit: int = 20) -> List[str]:
        """Fetches a list of unique lab test categories."""
        db = info.context["db"]
        from models.lab_test import LabTest
        categories = db.query(LabTest.category).filter(
            LabTest.category.isnot(None),
            LabTest.category != ""
        ).distinct().limit(limit).all()
        return [cat[0] for cat in categories if cat[0]]

    @strawberry.field
    def search_lab_tests(self, info: Info, query: str = "", limit: int = 20, offset: int = 0) -> List[LabTestType]:
        """
        Smart Search: Looks inside the test name, category, description, AND hidden search tags!
        If they type "sugar", it will catch the "sugar" tag inside the HbA1c test.
        """
        db = info.context["db"]
        search_term = f"%{query}%"
        
        return db.query(LabTest).filter(
            or_(
                LabTest.test_name.ilike(search_term),
                LabTest.category.ilike(search_term),
                LabTest.description.ilike(search_term),
                LabTest.search_tags.ilike(search_term) 
            )
        ).order_by(
            LabTest.is_profile.desc(), 
            LabTest.test_name.asc()
        ).offset(offset).limit(limit).all()

    @strawberry.field
    def find_labs_for_selected_tests(self, info: Info, test_ids: List[str]) -> List[LabPackageType]:
        """
        The Magic Cart Algorithm. 
        Takes a list of test_ids the customer wants, and finds the best labs for them.
        """
        if not test_ids:
            return []

        db = info.context["db"]
        
        # 1. Fetch the Global Info for the requested tests (so we know their names)
        requested_tests = db.query(LabTest).filter(LabTest.test_id.in_(test_ids)).all()
        test_dict = {t.test_id: t.test_name for t in requested_tests}
        
        # 2. Fetch all pricing rows where labs offer ANY of these tests
        pricings = db.query(LabTestPricing).filter(LabTestPricing.test_id.in_(test_ids)).all()
        
        if not pricings:
            return [] # Nobody offers any of these tests!
            
        # 3. Group the pricings by Lab
        lab_offerings = {}
        for p in pricings:
            if p.lab_id not in lab_offerings:
                lab_offerings[p.lab_id] = []
            lab_offerings[p.lab_id].append(p)
            
        # 4. Fetch the Lab details for the labs we found
        lab_ids = list(lab_offerings.keys())
        labs = db.query(LabUser).filter(LabUser.lab_id.in_(lab_ids)).all()
        lab_dict = {l.lab_id: l for l in labs}
        
        # 5. Build the Packages!
        packages = []
        for lab_id, offerings in lab_offerings.items():
            lab_info = lab_dict.get(lab_id)
            if not lab_info:
                continue
                
            matched = []
            total_price = 0.0
            offered_test_ids = set()
            
            # Add the matched ones
            for offer in offerings:
                matched.append(MatchedTestType(
                    test_id=offer.test_id,
                    test_name=test_dict.get(offer.test_id, "Unknown Test"),
                    price=offer.customer_selling_price
                ))
                total_price += offer.customer_selling_price
                offered_test_ids.add(offer.test_id)
                
            # Find the missing ones
            missing = []
            for req_id in test_ids:
                if req_id not in offered_test_ids:
                    missing.append(MissingTestType(
                        test_id=req_id,
                        test_name=test_dict.get(req_id, "Unknown Test")
                    ))
            
            is_full_match = len(missing) == 0
            
            packages.append(LabPackageType(
                lab_id=lab_id,
                lab_name=lab_info.lab_name,
                rating=lab_info.rating,
                total_price=round(total_price, 2),
                matched_tests=matched,
                missing_tests=missing,
                is_full_match=is_full_match,
                match_count=len(matched)
            ))
            
        # 6. Smart Sorting: Full matches first, then by most matches, then cheapest
        packages.sort(key=lambda x: (
            not x.is_full_match, # False (Full match) comes before True
            -x.match_count,      # Higher matches come first
            x.total_price        # Lower price comes first
        ))
        
        return packages

    @strawberry.field
    def get_lab_inventory(self, info: Info, lab_id: str, limit: int = 20, offset: int = 0) -> List[LabInventoryItemType]:
        """Shows all tests a specific lab offers. Useful if a customer visits a lab's profile."""
        db = info.context["db"]
        
        # Join LabTest and LabTestPricing
        results = db.query(LabTest, LabTestPricing).join(
            LabTestPricing, LabTest.test_id == LabTestPricing.test_id
        ).filter(
            LabTestPricing.lab_id == lab_id
        ).offset(offset).limit(limit).all()
        
        inventory = []
        for test, pricing in results:
            inventory.append(LabInventoryItemType(
                id=pricing.id,
                test_id=test.test_id,
                test_name=test.test_name,
                category=test.category,
                description=test.description,
                is_profile=test.is_profile,
                number_of_parameters=test.number_of_parameters,
                sample_type=test.sample_type,
                search_tags=test.search_tags,
                fasting_required=test.fasting_required,
                fasting_hours=test.fasting_hours,
                pre_test_info=test.pre_test_info,
                is_package=test.is_package,
                included_tests=test.included_tests,
                discount_percent=round(((pricing.mrp - pricing.customer_selling_price) / pricing.mrp * 100), 2) if pricing.mrp > 0 else 0.0,
                final_price=pricing.customer_selling_price,
                customer_selling_price=pricing.customer_selling_price,
                mrp=pricing.mrp,
                lab_id=pricing.lab_id
            ))
        return inventory
        
    @strawberry.field
    def tests_by_lab(self, info: Info, lab_id: str, limit: int = 5) -> List[LabInventoryItemType]:
        """Alias for get_lab_inventory specifically tailored for the FetchMoreFromLab query."""
        # pyrefly: ignore [unexpected-keyword]
        return self.get_lab_inventory(info=info, lab_id=lab_id, limit=limit, offset=0)


    # ==========================================
    # LAB BOOKING HISTORY
    # ==========================================
    
    @strawberry.field
    def get_my_lab_bookings(self, info: Info, customer_id: str, limit: int = 10) -> List[LabBookingType]:
        """
        Used by the Flutter app's "My Lab Tests" tab to show the history 
        of all their bookings, statuses, and download the PDF report URLs.
        """
        db = info.context["db"]
        return db.query(LabBooking).filter(
            LabBooking.customer_id == customer_id
        ).order_by(LabBooking.created_at.desc()).limit(limit).all()

    # ==========================================
    # NEW: VENDOR EARNINGS DASHBOARD
    # ==========================================
    
    @strawberry.field
    def get_vendor_earnings_dashboard(self, info: Info, vendor_id: str, vendor_type: str) -> DashboardEarningsType:
        """
        Works for BOTH Labs and Pharmacies!
        vendor_type must be either 'lab' or 'pharmacy'
        """
        from models.vendor_ledger import VendorLedger
        db = info.context["db"]
        
        # 1. Fetch all rows for this specific vendor
        ledgers = db.query(VendorLedger).filter(
            VendorLedger.vendor_id == vendor_id,
            VendorLedger.vendor_type == vendor_type
        ).order_by(VendorLedger.created_at.desc()).all()
        
        total_earnings = 0.0
        
        # 2. Simple addition, no pending logic!
        for row in ledgers:
            total_earnings += row.vendor_earning
                
        # 3. Format the recent transactions without the settlement status
        recent_txns = []
        for row in ledgers[:10]:
            recent_txns.append(VendorLedgerType(
                ledger_id=row.ledger_id,
                order_id=row.order_id,
                total_customer_paid=row.total_customer_paid,
                vendor_earning=row.vendor_earning,
                created_at=row.created_at.isoformat() if row.created_at else ""
            ))
            
        return DashboardEarningsType(
            total_lifetime_earnings=round(total_earnings, 2),
            total_orders_completed=len(ledgers),
            recent_transactions=recent_txns
        )

    # ==========================================
    # B2B SEARCH QUERIES
    # ==========================================
    
    @strawberry.field
    def get_my_b2b_cart(self, info: Info) -> B2BCartResponseType:
        db: Session = info.context["db"]
        shop = info.context.get("shop")
        if not shop:
            raise Exception("Unauthorized")
            
        cart = db.query(B2BCart).filter(B2BCart.shop_id == shop.shop_id).first()
        if not cart:
            return B2BCartResponseType(cart_id="empty", active_distributor_id=None, total_estimated_price=0.0, items_json=[])
            
        return B2BCartResponseType(cart_id=cart.cart_id, active_distributor_id=cart.active_distributor_id, total_estimated_price=cart.total_estimated_price, items_json=cart.items)

    @strawberry.field
    def search_b2b_medicines(self, info: Info, query: str, lat: float, lng: float) -> List[B2BMedicineType]:
        db = info.context["db"]
        
        # Search the master catalog
        medicines = db.query(Medicine).filter(
            Medicine.medicine_name.ilike(f"%{query}%")
        ).limit(20).all()

        # Inject coordinates into the context for the nested resolver
        info.context["search_lat"] = lat
        info.context["search_lng"] = lng

        return [
            B2BMedicineType(
                medicine_id=med.medicine_id,
                medicine_name=med.medicine_name,
                pack_size=med.pack_size,
                manufacturer=med.manufacturer
            )
            for med in medicines
        ]

    @strawberry.field
    def get_distributor_catalog(self, info: Info, distributor_id: str, limit: int = 50, offset: int = 0) -> List[DistributorCatalogItemType]:
        db = info.context["db"]
        
        # Join Inventory with the Master Medicine catalog
        results = db.query(
            DistributorInventory, 
            Medicine
        ).join(
            Medicine, DistributorInventory.medicine_id == Medicine.medicine_id
        ).filter(
            DistributorInventory.distributor_id == distributor_id,
            DistributorInventory.is_active == True,
            DistributorInventory.available_stock_boxes > 0
        ).offset(offset).limit(limit).all()

        return [
            DistributorCatalogItemType(
                inventory_id=inv.inventory_id,
                medicine_id=med.medicine_id,
                medicine_name=med.medicine_name,
                pack_size=med.pack_size,
                manufacturer=med.manufacturer,
                batch_number=inv.batch_number,
                ptr=inv.ptr,
                mrp=inv.mrp,
                available_stock_boxes=inv.available_stock_boxes,
                moq=inv.moq
            )
            for inv, med in results
        ]

    @strawberry.field
    def get_b2b_orders(self, info: Info, shop_id: str) -> List[B2BPurchaseOrderType]:
        db = info.context["db"]
        
        orders = db.query(B2BPurchaseOrder).filter(
            B2BPurchaseOrder.shop_id == shop_id
        ).order_by(B2BPurchaseOrder.created_at.desc()).all()

        return [
            B2BPurchaseOrderType(
                po_id=order.po_id,
                subtotal=order.subtotal,
                total_invoice_amount=order.total_invoice_amount,
                po_status=order.po_status,
                payment_terms=order.payment_terms,
                created_at=order.created_at.isoformat(),
                # Store raw JSON to be processed by the field resolver
                items_json=order.items, 
                # Store the ID to be resolved into the DistributorSummaryType
                distributor_id=order.distributor_id 
            )
            for order in orders
        ]

    @strawberry.field
    def get_nearby_distributors(self, info: Info, lat: float, lng: float) -> List[NearbyDistributorType]:
        db = info.context["db"]
        from sqlalchemy import func
        from models.distributor import DistributorUser
        
        distance = (
            6371 * func.acos(
                func.cos(func.radians(lat)) * func.cos(func.radians(DistributorUser.latitude)) *
                func.cos(func.radians(DistributorUser.longitude) - func.radians(lng)) +
                func.sin(func.radians(lat)) * func.sin(func.radians(DistributorUser.latitude))
            )
        )
        
        results = db.query(
            DistributorUser, distance.label("dist")
        ).filter(
            DistributorUser.status == "approved",
            DistributorUser.is_accepting_orders == True,
            distance <= 50.0
        ).order_by(distance.asc()).all()
        
        # Fallback if no approved ones exist, for testing/demo
        if not results:
            results = db.query(
                DistributorUser, distance.label("dist")
            ).filter(
                distance <= 50.0
            ).order_by(distance.asc()).all()
            
        return [
            NearbyDistributorType(
                distributor_id=r[0].distributor_id,
                company_name=r[0].company_name,
                phone=r[0].phone,
                address=r[0].address,
                distance_km=float(r[1] or 0.0)
            )
            for r in results
        ]
