from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Database Setup
from db import engine, Base

# REST Routers
from routes.medicine import router as medicine_router
from routes.order import router as order_router
from routes.websockets import router as websocket_router
from routes.auth import router as auth_router
from routes.customer import router as customer_router
from routes.pharma_shop import router as pharma_shop_router

# GraphQL Router
from graphql_api.router import graphql_app

# Create database tables automatically
# Import models to ensure they are registered with SQLAlchemy Base before create_all
import models
Base.metadata.create_all(bind=engine)

# Initialize FastAPI App
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/medicines", exist_ok=True)
app = FastAPI(title="Medy Backend API")

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
app.include_router(customer_router)
app.include_router(pharma_shop_router)
app.include_router(medicine_router)
app.include_router(order_router)
app.include_router(websocket_router)
from routes.lab_booking import router as lab_booking_router
from routes.lab_test import router as lab_test_router
from routes.payment import router as payment_router

app.include_router(lab_booking_router)
app.include_router(lab_test_router)
app.include_router(payment_router)

from routes.about_us import router as about_us_router
from routes.earnings import router as earnings_router
from routes.dashboard_analytics import router as dashboard_analytics_router
from routes.pharmacy_dashboard import router as pharmacy_dashboard_router
from routes.advertisement import router as advertisement_router

app.include_router(advertisement_router)
app.include_router(about_us_router)
app.include_router(earnings_router)
app.include_router(dashboard_analytics_router)
app.include_router(pharmacy_dashboard_router)

from routes.distributor_admin import router as distributor_admin_router
app.include_router(distributor_admin_router)

from routes.distributor_auth import router as distributor_auth_router
app.include_router(distributor_auth_router)

from routes.super_admin_b2b import router as super_admin_b2b_router
app.include_router(super_admin_b2b_router)

from routes.invoice import router as b2b_invoice_router
app.include_router(b2b_invoice_router)

# Mount GraphQL Route
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Medy Backend API!"}
