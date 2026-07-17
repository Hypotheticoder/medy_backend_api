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
            
        items = cart.items.copy() if cart.items else []
        
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
        
        db.commit()
        db.refresh(cart)
        return cart

    @strawberry.mutation
    def update_cart_quantity(self, info: Info, customer_id: str, medicine_id: str, quantity: int) -> CartType:
        """Updates the quantity of a specific item in the cart. If quantity is 0, removes the item."""
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        items = cart.items.copy() if cart.items else []
        
        if quantity <= 0:
            items = [item for item in items if item.get("medicine_id") != medicine_id]
        else:
            for item in items:
                if item.get("medicine_id") == medicine_id:
                    item["quantity"] = quantity
                    break
                    
        cart.items = items
        cart.total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.items)
        
        db.commit()
        db.refresh(cart)
        return cart

    @strawberry.mutation
    def remove_from_cart(self, info: Info, customer_id: str, medicine_id: str) -> CartType:
        """Removes a medicine completely from the customer's cart."""
        db = info.context["db"]
        cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
        if not cart:
            raise Exception("Cart not found")
            
        items = [item for item in cart.items if item.get("medicine_id") != medicine_id]
        cart.items = items
        cart.total_price = sum(float(item["price"]) * int(item["quantity"]) for item in cart.items)
        
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
