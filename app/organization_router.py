"""
Organization management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
# Import only what we need to avoid relationship errors
from sqlalchemy import text
from auth.utils import get_current_user_or_key
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["organizations"])

# Pydantic models for API
class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    organization_type: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    founded_date: Optional[date] = None
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[int] = None  # In cents
    status: Optional[str] = None
    notes: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: int
    asset_id: str
    name: Optional[str]
    legal_name: str
    trade_name: Optional[str]
    organization_type: Optional[str]
    industry: Optional[str]
    sector: Optional[str]
    registration_number: Optional[str]
    tax_id: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state_province: Optional[str]
    postal_code: Optional[str]
    country: str
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    founded_date: Optional[date]
    number_of_employees: Optional[int]
    annual_revenue: Optional[int]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[dict])
async def list_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get organizations - admins see all, users see only their own"""
    
    if current_user.get("access_level") == "admin":
        # Admins can see all organizations
        sql_query = """
            SELECT id, asset_id, name, legal_name, trade_name, organization_type, 
                   industry, sector, registration_number, tax_id,
                   address_line1, address_line2, city, state_province, postal_code, country,
                   phone, email, website, founded_date, number_of_employees, annual_revenue,
                   status, created_at, updated_at, created_by, notes
            FROM organizations
            ORDER BY created_at DESC
        """
        result = db.execute(text(sql_query))
    else:
        # Regular users can only see their own organization
        # First get the user's organization_id
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if not user_row or not user_row.organization_id:
            return []  # User has no organization assigned
            
        sql_query = """
            SELECT id, asset_id, name, legal_name, trade_name, organization_type, 
                   industry, sector, registration_number, tax_id,
                   address_line1, address_line2, city, state_province, postal_code, country,
                   phone, email, website, founded_date, number_of_employees, annual_revenue,
                   status, created_at, updated_at, created_by, notes
            FROM organizations
            WHERE id = :org_id
            ORDER BY created_at DESC
        """
        result = db.execute(text(sql_query), {"org_id": user_row.organization_id})
    
    organizations = []
    for row in result:
        org = dict(row._mapping)
        # Convert date objects to strings for JSON serialization
        if org.get('founded_date'):
            org['founded_date'] = org['founded_date'].isoformat()
        if org.get('created_at'):
            org['created_at'] = org['created_at'].isoformat()
        if org.get('updated_at'):
            org['updated_at'] = org['updated_at'].isoformat()
        organizations.append(org)
    
    return organizations

@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get a specific organization"""
    
    # Check if user has access to this organization
    if current_user.get("access_level") != "admin":
        # Regular users can only access their own organization
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if not user_row or user_row.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you can only view your own organization"
            )
    
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization

@router.put("/{organization_id}", response_model=dict)
async def update_organization(
    organization_id: int,
    organization_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Update an organization - admins can update any, users can update their own"""
    
    # Check if user has access to this organization
    if current_user.get("access_level") != "admin":
        # Regular users can only update their own organization
        user_result = db.execute(text("SELECT organization_id FROM users WHERE username = :username"), 
                                {"username": current_user.get("username")})
        user_row = user_result.first()
        
        if not user_row or user_row.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you can only update your own organization"
            )
    
    # Check if organization exists
    result = db.execute(text("SELECT id FROM organizations WHERE id = :org_id"), {"org_id": organization_id})
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields that were provided
    update_data = organization_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Build dynamic update query
    set_clauses = []
    params = {"org_id": organization_id, "updated_at": datetime.utcnow()}
    
    for field, value in update_data.items():
        set_clauses.append(f"{field} = :{field}")
        params[field] = value
    
    set_clauses.append("updated_at = :updated_at")
    
    update_sql = f"""
        UPDATE organizations 
        SET {', '.join(set_clauses)}
        WHERE id = :org_id
    """
    
    try:
        db.execute(text(update_sql), params)
        db.commit()
        
        # Return updated organization
        result = db.execute(text("""
            SELECT id, asset_id, name, legal_name, trade_name, organization_type, 
                   industry, sector, registration_number, tax_id,
                   address_line1, address_line2, city, state_province, postal_code, country,
                   phone, email, website, founded_date, number_of_employees, annual_revenue,
                   status, created_at, updated_at, created_by, notes
            FROM organizations WHERE id = :org_id
        """), {"org_id": organization_id})
        
        row = result.first()
        if row:
            org = dict(row._mapping)
            # Convert date objects to strings for JSON serialization
            if org.get('founded_date'):
                org['founded_date'] = org['founded_date'].isoformat()
            if org.get('created_at'):
                org['created_at'] = org['created_at'].isoformat()
            if org.get('updated_at'):
                org['updated_at'] = org['updated_at'].isoformat()
            
            logger.info(f"Organization {organization_id} updated by {current_user.get('username')}")
            return org
        else:
            raise HTTPException(status_code=404, detail="Organization not found after update")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating organization {organization_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )

@router.get("/by-asset-id/{asset_id}", response_model=OrganizationResponse)
async def get_organization_by_asset_id(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_or_key)
):
    """Get organization by AssetID"""
    organization = db.query(Organization).filter(Organization.asset_id == asset_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return organization