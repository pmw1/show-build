#!/usr/bin/env python3
"""
Update Polaris Broadcasting with comprehensive organization data
"""
import sys
import os
sys.path.append('/app')

from sqlalchemy.orm import sessionmaker
from database import engine
from models_v2 import Organization
from datetime import datetime, date

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_polaris_broadcasting():
    """Update Polaris Broadcasting with comprehensive data"""
    
    db = SessionLocal()
    try:
        print("🔄 Updating Polaris Broadcasting with comprehensive data...")
        
        # Find Polaris Broadcasting
        polaris = db.query(Organization).filter(
            Organization.legal_name == "Polaris Broadcasting"
        ).first()
        
        if not polaris:
            print("❌ Polaris Broadcasting not found!")
            return None
        
        print(f"📋 Found organization: {polaris.legal_name} (AssetID: {polaris.asset_id})")
        
        # Update with comprehensive data
        polaris.name = "Polaris Broadcasting"  # Display name
        polaris.legal_name = "Polaris Broadcasting LLC"  # Official legal name
        polaris.trade_name = "Polaris Media"  # Trade name/DBA
        
        # Organization classification
        polaris.organization_type = "LLC"
        polaris.industry = "Broadcasting"
        polaris.sector = "Media & Entertainment"
        
        # Contact information
        polaris.address_line1 = "190 Main St."
        polaris.city = "Ravena"
        polaris.state_province = "NY"
        polaris.postal_code = "12143"
        polaris.country = "United States"
        
        polaris.phone = "(518) 756-3300"
        polaris.email = "info@polarisbroadcasting.com"
        polaris.website = "https://polarisbroadcasting.com"
        
        # Operational data
        polaris.founded_date = date(2020, 1, 15)  # Founded January 15, 2020
        polaris.number_of_employees = 12
        polaris.annual_revenue = 2500000 * 100  # $2.5M in cents
        polaris.status = "active"
        
        # System data
        polaris.created_by = "kevin"
        polaris.notes = "Regional broadcasting company focused on local news and community content"
        
        # Clear the old settings field since we now have proper fields
        polaris.settings = {"migrated_from_settings": True}
        
        db.commit()
        
        print("✅ Successfully updated Polaris Broadcasting!")
        print("\n📊 Updated Organization Details:")
        print(f"   Legal Name: {polaris.legal_name}")
        print(f"   Display Name: {polaris.name}")
        print(f"   Trade Name: {polaris.trade_name}")
        print(f"   Type: {polaris.organization_type}")
        print(f"   Industry: {polaris.industry}")
        print(f"   Address: {polaris.address_line1}, {polaris.city}, {polaris.state_province} {polaris.postal_code}")
        print(f"   Phone: {polaris.phone}")
        print(f"   Website: {polaris.website}")
        print(f"   Founded: {polaris.founded_date}")
        print(f"   Employees: {polaris.number_of_employees}")
        print(f"   Annual Revenue: ${polaris.annual_revenue / 100:,.2f}")
        print(f"   Status: {polaris.status}")
        
        return polaris
        
    except Exception as e:
        print(f"❌ Error updating Polaris Broadcasting: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    update_polaris_broadcasting()