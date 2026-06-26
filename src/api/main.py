import os

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from src.database import get_db
from src.models import Product, PriceHistory
from src.tracker import add_product

# In production we hide the interactive API docs and the OpenAPI schema.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
_IS_PROD = ENVIRONMENT == "production"

# Initialize api
app = FastAPI(
    title="Price Tracker API",
    description="Backend API for Mobile App connection",
    version="1.0.0",
    docs_url=None if _IS_PROD else "/docs",
    redoc_url=None if _IS_PROD else "/redoc",
    openapi_url=None if _IS_PROD else "/openapi.json",
)

# Data format
class ProductSchema(BaseModel):
    id: int
    name: str
    url: str
    target_price: Optional[float] = None
    current_price: Optional[float] = None

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    url: str
    target_price: Optional[float] = None

@app.get("/")
def read_root():
    return {"status": "online", "message": "Price Tracker API is running"}

# Returns list of products and their actual price
@app.get("/products", response_model=List[ProductSchema])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    
    results = []
    for p in products:
        latest_price = p.prices[-1].price if p.prices else 0.0
        
        p_data = ProductSchema(
            id=p.id,
            name=p.name,
            url=p.url,
            target_price=p.target_price,
            current_price=latest_price
        )
        results.append(p_data)
        
    return results

# Add product from the mobile via URL
@app.post("/products", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        new_product = add_product(product.url, product.target_price)
        
        # Search initial price
        initial_price = 0.0
        if new_product.prices:
            initial_price = new_product.prices[0].price
            
        return ProductSchema(
            id=new_product.id,
            name=new_product.name,
            url=new_product.url,
            target_price=new_product.target_price,
            current_price=initial_price
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))