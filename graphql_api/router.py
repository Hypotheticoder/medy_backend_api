import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from graphql_api.queries import Query
from graphql_api.mutations import Mutation
from db import get_db

# 1. Compile the Schema
# If you add Mutations later (e.g., update profile), you add them here: `mutation=Mutation`
schema = strawberry.Schema(query=Query, mutation=Mutation)

# 2. Context Dependency
# This injects the FastAPI PostgreSQL session into Strawberry's `info.context`
async def get_graphql_context(db: Session = Depends(get_db)):
    return {
        "db": db
    }

# 3. Create the Router
# You will import this `graphql_app` in your main.py and mount it!
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphiql=True # Enables the awesome GraphQL visual testing playground in your browser!
)

"""
In your main.py, you just need to do this:

from graphql_api.router import graphql_app
app.include_router(graphql_app, prefix="/graphql")
"""
