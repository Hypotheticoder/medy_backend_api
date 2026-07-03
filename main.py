from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database Setup
from db import engine, Base

# REST Routers
from routes.medicine import router as medicine_router
from routes.order import router as order_router
from routes.websockets import router as websocket_router
from routes.auth import router as auth_router

# GraphQL Router
from graphql_api.router import graphql_app

# Create database tables automatically
# Import models to ensure they are registered with SQLAlchemy Base before create_all
import models
Base.metadata.create_all(bind=engine)

# Initialize FastAPI App
app = FastAPI(title="Medy Backend API")

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend's URL!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST Routes
app.include_router(auth_router)
app.include_router(medicine_router)
app.include_router(order_router)
app.include_router(websocket_router)

# Mount GraphQL Route
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Medy Backend API!"}
