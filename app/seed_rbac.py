#!/usr/bin/env python3
"""
Seed RBAC system with default permissions and roles
"""
import sys
import os
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from rbac_service import seed_default_permissions

def main():
    """Seed the RBAC system with default data"""
    print("Seeding RBAC system with default permissions and roles...")
    
    db = SessionLocal()
    try:
        seed_default_permissions(db)
        print("✅ Successfully seeded RBAC system with default data")
        
        # Print some statistics
        from models_rbac import Permission, Role
        perm_count = db.query(Permission).count()
        role_count = db.query(Role).count()
        print(f"📊 Created {perm_count} permissions and {role_count} roles")
        
    except Exception as e:
        print(f"❌ Error seeding RBAC data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()