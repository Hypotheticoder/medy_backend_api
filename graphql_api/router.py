import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os

from graphql_api.queries import Query
from graphql_api.mutations import Mutation
from db import get_db
from models.pharma_shop import PharmaShopUser

# 1. Compile the Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey_change_in_production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# 2. Context Dependency with Auth Injection
async def get_graphql_context(request: Request, db: Session = Depends(get_db)):
    context = {"db": db, "shop": None}
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print("JWT Payload:", payload)
            shop_id = payload.get("sub")
            if shop_id:
                # Bypass verification for development
                class MockShop:
                    def __init__(self, sid):
                        self.shop_id = sid
                        self.is_verified = True
                context["shop"] = MockShop(shop_id)
        except JWTError as e:
            print("JWT Verification Error:", str(e))
            pass 
    else:
        print("No valid Authorization header found. Header was:", auth_header)
            
    return context

# 3. Create the Router
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context
)
