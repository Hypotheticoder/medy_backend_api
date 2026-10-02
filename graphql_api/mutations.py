import strawberry
import uuid
from strawberry.types import Info
from strawberry.scalars import JSON
from typing import Optional

from graphql_api.types.cart import CartType
from graphql_api.types.medicine import MedicineType
from models.cart import Cart
from models.medicine import Medicine
from models.customer import CustomerUser
from models.b2b_cart import B2BCart
from models.b2b_purchase_order import B2BPurchaseOrder
from models.distributor_inventory import DistributorInventory
from graphql_api.types.b2b_types import B2BCartResponseType, B2BPurchaseOrderType, B2BRazorpayOrderType

@strawberry.type
class Mutation:
    
    @strawberry.mutation
    def add_to_cart(self, info: Info, customer_id: str, medicine_id: str, quantity: int = 1) -> CartType:
        """Adds a medicine to the customer's cart or increments quantity if it exists."""
        db = info.context["db"]
        
        # Verify medicine exists
        medicine = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
        if not medicine:
            raise Exception("Medicine not found")
            
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        
        # If cart doesn't exist, create it
        if not cart:
            cart = Cart(customer_id=customer_id, items=[], total_price=0.0)
            db.add(cart)
            db.flush() # To get it added to session before modifying JSON
            
        import copy
        from sqlalchemy.orm.attributes import flag_modified
        items = copy.deepcopy(cart.items) if cart.items else []
        
        # Check if item already in cart
        found = False
        for item in items:
            if item.get("medicine_id") == medicine_id:
                item["quantity"] += quantity
                found = True
                break
                
        if not found:
            items.append({
                "medicine_id": medicine.medicine_id,
                "medicine_name": medicine.medicine_name,
                "pack_size": medicine.pack_size,
                "price": medicine.final_selling_price,
                "quantity": quantity
            })
            
        cart.items = items
        
        # Recalculate total price
        cart.total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.items)
        
        flag_modified(cart, "items")
        db.commit()
        db.refresh(cart)
        return cart

    @strawberry.mutation
    def update_cart_quantity(self, info: Info, customer_id: str, medicine_id: str, quantity: int) -> CartType:
        """Updates the quantity of a specific item in the cart. If quantity is 0, removes the item."""
        import copy
        from sqlalchemy.orm.attributes import flag_modified
        
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        items = copy.deepcopy(cart.items) if cart.items else []
        
        if quantity <= 0:
            items = [item for item in items if item.get("medicine_id") != medicine_id]
        else:
            for item in items:
                if item.get("medicine_id") == medicine_id:
                    item["quantity"] = quantity
                    break
                    
        cart.items = items
        cart.total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.items)
        
        flag_modified(cart, "items")
        db.commit()
        db.refresh(cart)
        return cart

    @strawberry.mutation
    def remove_from_cart(self, info: Info, customer_id: str, medicine_id: str) -> CartType:
        """Removes a medicine completely from the customer's cart."""
        from sqlalchemy.orm.attributes import flag_modified
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        items = [item for item in cart.items if item.get("medicine_id") != medicine_id]
        cart.items = items
        cart.total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.items)
        
        flag_modified(cart, "items")
        db.commit()
        db.refresh(cart)
        return cart

    @strawberry.mutation
    def clear_cart(self, info: Info, customer_id: str) -> CartType:
        """Clears all items from the cart."""
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        cart.items = []
        cart.total_price = 0.0
        
        db.commit()
        db.refresh(cart)
        return cart

    @strawberry.mutation
    def add_saved_address(
        self, 
        info: Info, 
        customer_id: str, 
        address_type: str, 
        address_1: str, 
        street_address: str, 
        latitude: float, 
        longitude: float,
        is_default: bool = False
    ) -> JSON:
        """Adds a new saved address to the customer's profile."""
        db = info.context["db"]
        customer = db.query(CustomerUser).filter(CustomerUser.customer_id == customer_id).first()
        if not customer:
            raise Exception("Customer not found")
            
        addresses = customer.saved_addresses.copy() if customer.saved_addresses else []
        
        new_address = {
            "address_id": str(uuid.uuid4()),
            "address_type": address_type,
            "address_1": address_1,
            "street_address": street_address,
            "latitude": latitude,
            "longitude": longitude,
            "is_default": is_default
        }
        
        if is_default:
            for addr in addresses:
                addr["is_default"] = False
                
        addresses.append(new_address)
        customer.saved_addresses = addresses
        
        db.commit()
        db.refresh(customer)
        
        return new_address

    @strawberry.mutation
    def delete_saved_address(
        self,
        info: Info,
        customer_id: str,
        address_id: str
    ) -> bool:
        """Deletes a saved address from the customer's profile."""
        db = info.context["db"]
        customer = db.query(CustomerUser).filter(CustomerUser.customer_id == customer_id).first()
        if not customer:
            raise Exception("Customer not found")
            
        if not customer.saved_addresses:
            return False
            
        initial_length = len(customer.saved_addresses)
        customer.saved_addresses = [addr for addr in customer.saved_addresses if addr.get("address_id") != address_id]
        
        if len(customer.saved_addresses) == initial_length:
            return False # Nothing was deleted
            
        db.commit()
        return True

    @strawberry.mutation
    def update_medicine(
        self,
        info: Info,
        medicine_id: str,
        medicine_name: Optional[str] = None,
        medicine_category: Optional[str] = None,
        pack_size: Optional[str] = None,
        mrp: Optional[float] = None,
        final_selling_price: Optional[float] = None,
        prescription_required: Optional[bool] = None,
    ) -> MedicineType:
        """Updates a medicine in the global catalog."""
        db = info.context["db"]
        medicine = db.query(Medicine).filter(Medicine.medicine_id == medicine_id).first()
        if not medicine:
            raise Exception("Medicine not found")
            
        if medicine_name is not None:
            medicine.medicine_name = medicine_name
        if medicine_category is not None:
            medicine.medicine_category = medicine_category
        if pack_size is not None:
            medicine.pack_size = pack_size
        if mrp is not None:
            medicine.mrp = mrp
        if final_selling_price is not None:
            medicine.final_selling_price = final_selling_price
        if prescription_required is not None:
            medicine.prescription_required = prescription_required
            
        db.commit()
        db.refresh(medicine)
        return medicine

    # ==========================================
    # B2B CART AND CHECKOUT MUTATIONS
    # ==========================================

    @strawberry.mutation
    def add_to_b2b_cart(self, info: Info, distributor_id: str, inventory_id: str, qty_boxes: int, ptr: float) -> B2BCartResponseType:
        db = info.context["db"]
        shop = info.context.get("shop")
        if not shop:
            raise Exception("Unauthorized: You must be logged in as a verified pharmacy.")

        cart = db.query(B2BCart).filter(B2BCart.shop_id == shop.shop_id).first()
        
        if not cart:
            cart = B2BCart(shop_id=shop.shop_id)
            db.add(cart)
            
        # The Swiggy Check: Enforce single distributor
        if cart.active_distributor_id and cart.active_distributor_id != distributor_id:
            if len(cart.items) > 0:
                raise Exception("Cart contains items from another distributor. Clear it first.")
                
        cart.active_distributor_id = distributor_id
        
        import copy
        from sqlalchemy.orm.attributes import flag_modified
        items = copy.deepcopy(cart.items) if cart.items else []

        new_item = {
            "inventory_id": inventory_id,
            "qty_boxes": qty_boxes,
            "ptr": ptr,
            "gst_percentage": 12.0 # Standard pharma slab
        }
        
        items.append(new_item)
        cart.items = items
        
        if cart.total_estimated_price is None:
            cart.total_estimated_price = 0.0
            
        cart.total_estimated_price += (ptr * qty_boxes)
        
        flag_modified(cart, "items")
        db.commit()
        db.refresh(cart)
        
        return B2BCartResponseType(
            cart_id=cart.cart_id, 
            active_distributor_id=cart.active_distributor_id,
            total_estimated_price=cart.total_estimated_price,
            items_json=cart.items
        )

    @strawberry.mutation
    def checkout_b2b_cart(self, info: Info, payment_terms: str) -> B2BPurchaseOrderType:
        db: Session = info.context["db"]
        shop = info.context.get("shop")
        
        if not shop:
            raise Exception("Unauthorized: Retailer login required.")
            
        cart = db.query(B2BCart).filter(B2BCart.shop_id == shop.shop_id).first()
        if not cart or not cart.items:
            raise Exception("Cannot checkout an empty cart")
            
        subtotal = 0.0
        gst_total = 0.0
        
        from sqlalchemy.orm.attributes import flag_modified
        
        for item in cart.items:
            inventory = db.query(DistributorInventory).with_for_update().filter(
                DistributorInventory.inventory_id == item["inventory_id"]
            ).first()
            
            if not inventory or inventory.available_stock_boxes < item["qty_boxes"]:
                raise Exception(f"Insufficient stock for batch {item.get('batch_number', 'unknown')}")
                
            inventory.available_stock_boxes -= item["qty_boxes"]
            item["medicine_id"] = inventory.medicine_id
            item["batch_number"] = inventory.batch_number
            
            item_total = item["ptr"] * item["qty_boxes"]
            subtotal += item_total
            gst_total += item_total * (item["gst_percentage"] / 100)
            
        po = B2BPurchaseOrder(
            shop_id=shop.shop_id,
            distributor_id=cart.active_distributor_id,
            items=cart.items,
            subtotal=subtotal,
            cgst_amount=gst_total / 2,
            sgst_amount=gst_total / 2,
            total_invoice_amount=subtotal + gst_total,
            payment_terms=payment_terms
        )
        db.add(po)
        
        cart.items = []
        cart.active_distributor_id = None
        cart.total_estimated_price = 0.0
        flag_modified(cart, "items")
        
        db.commit()
        db.refresh(po)
        
        import asyncio
        from routes.websockets import redis_manager
        import json

        def notify_distributor():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(redis_manager.connect())
                    channel = f"distributor_channel_{po.distributor_id}"
                    msg = json.dumps({
                        "type": "NEW_PURCHASE_ORDER",
                        "po_id": po.po_id,
                        "total_amount": po.total_invoice_amount,
                        "items_count": len(po.items) if isinstance(po.items, list) else 0
                    })
                    # just a best effort
            except:
                pass
        
        notify_distributor()
        
        return B2BPurchaseOrderType(
            po_id=po.po_id,
            subtotal=po.subtotal,
            total_invoice_amount=po.total_invoice_amount,
            po_status=po.po_status,
            payment_terms=po.payment_terms,
            created_at=po.created_at.isoformat(),
            items_json=po.items,
            distributor_id=po.distributor_id
        )

    @strawberry.mutation
    def clear_b2b_cart(self, info: Info) -> B2BCartResponseType:
        from sqlalchemy.orm.attributes import flag_modified
        db: Session = info.context["db"]
        shop = info.context.get("shop")
        if not shop:
            raise Exception("Unauthorized")
            
        cart = db.query(B2BCart).filter(B2BCart.shop_id == shop.shop_id).first()
        if cart:
            cart.items = []
            cart.active_distributor_id = None
            cart.total_estimated_price = 0.0
            flag_modified(cart, "items")
            db.commit()
            
        return B2BCartResponseType(
            cart_id=cart.cart_id if cart else "empty",
            active_distributor_id=None,
            total_estimated_price=0.0,
            items_json=[]
        )
        

    @strawberry.mutation
    def update_b2b_cart_qty(self, info: Info, inventory_id: str, new_qty: int) -> B2BCartResponseType:
        from sqlalchemy.orm.attributes import flag_modified
        db: Session = info.context["db"]
        shop = info.context.get("shop")
        if not shop:
            raise Exception("Unauthorized")
            
        cart = db.query(B2BCart).filter(B2BCart.shop_id == shop.shop_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        if new_qty <= 0:
            return self.remove_from_b2b_cart(info, inventory_id)
            
        updated = False
        new_total = 0.0
        for item in cart.items:
            if item["inventory_id"] == inventory_id:
                item["qty_boxes"] = new_qty
                updated = True
            new_total += (item["ptr"] * item["qty_boxes"])
            
        if not updated:
            raise Exception("Item not in cart")
            
        cart.total_estimated_price = new_total
        flag_modified(cart, "items")
        db.commit()
        db.refresh(cart)
        return B2BCartResponseType(cart_id=cart.cart_id, active_distributor_id=cart.active_distributor_id, total_estimated_price=cart.total_estimated_price, items_json=cart.items)

    @strawberry.mutation
    def remove_from_b2b_cart(self, info: Info, inventory_id: str) -> B2BCartResponseType:
        from sqlalchemy.orm.attributes import flag_modified
        db: Session = info.context["db"]
        shop = info.context.get("shop")
        if not shop:
            raise Exception("Unauthorized")
            
        cart = db.query(B2BCart).filter(B2BCart.shop_id == shop.shop_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        filtered_items = []
        for item in cart.items:
            if item["inventory_id"] != inventory_id:
                filtered_items.append(item)
            else:
                cart.total_estimated_price -= (item["ptr"] * item["qty_boxes"])
                
        cart.items = filtered_items
        if not cart.items:
            cart.active_distributor_id = None
            
        flag_modified(cart, "items")
        db.commit()
        db.refresh(cart)
        
        return B2BCartResponseType(cart_id=cart.cart_id, active_distributor_id=cart.active_distributor_id, total_estimated_price=cart.total_estimated_price, items_json=cart.items)

    @strawberry.mutation
    def create_b2b_razorpay_order(self, info: Info, po_id: str) -> B2BRazorpayOrderType:
        db = info.context["db"]
        from models.b2b_purchase_order import B2BPurchaseOrder
        po = db.query(B2BPurchaseOrder).filter(B2BPurchaseOrder.po_id == po_id).first()
        if not po:
            raise Exception("PO not found")
            
        import os
        import razorpay
        RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_YourKeyId")
        RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "rzp_test_YourSecret")
        
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        amount_in_paise = int(po.total_invoice_amount * 100)
        
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": po.po_id,
        }
        try:
            razorpay_order = client.order.create(data=order_data)
            return B2BRazorpayOrderType(
                razorpay_order_id=razorpay_order["id"],
                amount_in_paise=amount_in_paise,
                currency="INR",
                key_id=RAZORPAY_KEY_ID
            )
        except Exception as e:
            raise Exception(f"Razorpay error: {str(e)}")
