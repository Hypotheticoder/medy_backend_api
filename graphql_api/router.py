import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import Depends
from sqlalchemy.orm import Session

# 🚨 Notice the updated import here! 🚨
from graphql_api.queries import Query
from db import get_db

schema = strawberry.Schema(query=Query)

async def get_graphql_context(db: Session = Depends(get_db)):
    return {"db": db}

graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context
)
