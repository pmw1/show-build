"""
Customer Router - API endpoints for customer/sponsor management.
Handles CRUD operations for advertisers, sponsors, and partners.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from database import get_db
from auth.utils import get_current_user_or_key
from services.asset_id import AssetIDService
from models_v2 import Customer, Organization


router = APIRouter(prefix="/api/customers", tags=["customers"])


# =====================
# Pydantic Models
# =====================

class CustomerCreate(BaseModel):
    """Schema for creating a new customer."""
    company_name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_title: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    customer_type: str = Field(default="advertiser")
    tier: str = Field(default="standard")
    notes: Optional[str] = None
    is_test_data: bool = False


class CustomerUpdate(BaseModel):
    """Schema for updating a customer."""
    company_name: Optional[str] = None
    display_name: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_title: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    customer_type: Optional[str] = None
    tier: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


# =====================
# CRUD Endpoints
# =====================

@router.get("/")
async def list_customers(
    is_active: bool = Query(True, description="Filter by active status"),
    customer_type: Optional[str] = Query(None, description="Filter by type (advertiser, sponsor, partner)"),
    search: Optional[str] = Query(None, description="Search in company name or contact name"),
    include_test_data: bool = Query(False, description="Include test data"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """List all customers with optional filtering."""
    query = db.query(Customer)

    # Apply filters
    if not include_test_data:
        query = query.filter(Customer.is_test_data == False)

    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)

    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.company_name.ilike(search_term),
                Customer.contact_name.ilike(search_term),
                Customer.display_name.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    customers = query.order_by(Customer.company_name).offset(offset).limit(limit).all()

    return {
        "customers": [c.to_dict() for c in customers],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/dropdown")
async def get_customer_dropdown(
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Get simplified customer list for dropdown selection."""
    customers = db.query(Customer).filter(
        Customer.is_active == True,
        Customer.is_test_data == False
    ).order_by(Customer.company_name).all()

    return {
        "customers": [
            {
                "asset_id": c.asset_id,
                "company_name": c.company_name,
                "display_name": c.display_name or c.company_name,
                "customer_type": c.customer_type,
                "tier": c.tier
            }
            for c in customers
        ]
    }


@router.get("/{asset_id}")
async def get_customer(
    asset_id: str,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Get a single customer by asset_id."""
    customer = db.query(Customer).filter(Customer.asset_id == asset_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {asset_id} not found")

    return customer.to_dict()


@router.post("/")
async def create_customer(
    customer_data: CustomerCreate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Create a new customer."""
    # Get default organization
    org = db.query(Organization).filter(Organization.status == "active").first()
    if not org:
        org = db.query(Organization).first()
    if not org:
        raise HTTPException(status_code=400, detail="No organization found")

    # Generate asset ID
    asset_id = AssetIDService.generate("CUS")  # CUS prefix for customers

    # Create customer
    customer = Customer(
        asset_id=asset_id,
        organization_id=org.id,
        company_name=customer_data.company_name,
        display_name=customer_data.display_name,
        industry=customer_data.industry,
        contact_name=customer_data.contact_name,
        contact_email=customer_data.contact_email,
        contact_phone=customer_data.contact_phone,
        contact_title=customer_data.contact_title,
        billing_email=customer_data.billing_email,
        billing_address=customer_data.billing_address,
        customer_type=customer_data.customer_type,
        tier=customer_data.tier,
        notes=customer_data.notes,
        is_test_data=customer_data.is_test_data,
        is_active=True
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer.to_dict()


@router.patch("/{asset_id}")
async def update_customer(
    asset_id: str,
    update_data: CustomerUpdate,
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Update an existing customer."""
    customer = db.query(Customer).filter(Customer.asset_id == asset_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {asset_id} not found")

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(customer, key, value)

    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)

    return customer.to_dict()


@router.delete("/{asset_id}")
async def delete_customer(
    asset_id: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    current_user: dict = Depends(get_current_user_or_key),
    db: Session = Depends(get_db)
):
    """Delete a customer (soft delete by default)."""
    customer = db.query(Customer).filter(Customer.asset_id == asset_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {asset_id} not found")

    if hard_delete:
        db.delete(customer)
        db.commit()
        return {"message": f"Customer {asset_id} permanently deleted"}
    else:
        customer.is_active = False
        customer.updated_at = datetime.utcnow()
        db.commit()
        return {"message": f"Customer {asset_id} deactivated"}
