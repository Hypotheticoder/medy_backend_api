import strawberry
from strawberry.types import Info
from typing import Optional

from graphql_api.types.cart import CartType
from models.cart import Cart
from models.medicine import Medicine

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
