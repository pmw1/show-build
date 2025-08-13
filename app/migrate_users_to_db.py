#!/usr/bin/env python3
"""
Migration script to move users from JSON storage to database tables
Run this after creating the user authentication tables
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

from database import DATABASE_URL
from models_user import User, APIKey

# Create database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def migrate_users_from_json():
    """Migrate users from JSON file to database"""
    
    # Path to existing JSON users file
    users_json_path = Path(__file__).parent / "storage" / "users.json"
    
    if not users_json_path.exists():
        print(f"Users JSON file not found at: {users_json_path}")
        return False
    
    try:
        # Load existing users from JSON
        with users_json_path.open('r') as f:
            users_data = json.load(f)
        
        print(f"Found {len(users_data)} users in JSON file")
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Check if users already exist in database
            existing_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            if existing_count > 0:
                print(f"Database already contains {existing_count} users. Skipping migration.")
                return True
            
            # Migrate each user
            migrated_count = 0
            for username, user_data in users_data.items():
                try:
                    # Create User object
                    db_user = User(
                        username=user_data.get('username', username),
                        hashed_password=user_data.get('hashed_password', ''),
                        access_level=user_data.get('access_level', 'user'),
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                        email=user_data.get('email', ''),
                        phone=user_data.get('phone', ''),
                        profile_picture=user_data.get('profile_picture', ''),
                        is_active=True,
                        is_verified=True,
                        settings={}
                    )
                    
                    db.add(db_user)
                    migrated_count += 1
                    print(f"✓ Migrated user: {username}")
                    
                except Exception as e:
                    print(f"✗ Failed to migrate user {username}: {e}")
            
            # Commit all users
            db.commit()
            print(f"\n✅ Successfully migrated {migrated_count} users to database")
            
            # Create backup of JSON file
            backup_path = users_json_path.with_suffix(f'.json.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            users_json_path.rename(backup_path)
            print(f"📁 Backed up original JSON file to: {backup_path}")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Database error during migration: {e}")
            return False
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False


def migrate_api_keys_from_json():
    """Migrate API keys from JSON file to database"""
    
    # Path to existing JSON API keys file
    api_keys_json_path = Path(__file__).parent / "storage" / "api_keys.json"
    
    if not api_keys_json_path.exists():
        print(f"API keys JSON file not found at: {api_keys_json_path}")
        return False
    
    try:
        # Load existing API keys from JSON
        with api_keys_json_path.open('r') as f:
            api_keys_data = json.load(f)
        
        print(f"Found {len(api_keys_data)} API keys in JSON file")
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Check if API keys already exist in database
            existing_count = db.execute(text("SELECT COUNT(*) FROM api_keys")).scalar()
            if existing_count > 0:
                print(f"Database already contains {existing_count} API keys. Skipping migration.")
                return True
            
            # Migrate each API key
            migrated_count = 0
            for key_value, key_data in api_keys_data.items():
                try:
                    # Create APIKey object
                    # Note: We store the actual key as key_hash (not ideal, but preserves functionality)
                    # In production, you'd want to hash the key and store the hash
                    db_api_key = APIKey(
                        key_hash=key_value,  # Store actual key for now
                        key_prefix=key_value[:8],
                        client_name=key_data.get('client_name', 'unknown'),
                        access_level=key_data.get('access_level', 'service'),
                        created_by_username=key_data.get('created_by', 'admin'),
                        is_active=True,
                        usage_count=0
                    )
                    
                    db.add(db_api_key)
                    migrated_count += 1
                    print(f"✓ Migrated API key: {key_value[:8]}...")
                    
                except Exception as e:
                    print(f"✗ Failed to migrate API key {key_value[:8]}...: {e}")
            
            # Commit all API keys
            db.commit()
            print(f"\n✅ Successfully migrated {migrated_count} API keys to database")
            
            # Create backup of JSON file
            backup_path = api_keys_json_path.with_suffix(f'.json.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            api_keys_json_path.rename(backup_path)
            print(f"📁 Backed up original JSON file to: {backup_path}")
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"❌ Database error during API key migration: {e}")
            return False
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error reading API keys JSON file: {e}")
        return False


def main():
    """Run the migration"""
    print("🚀 Starting user authentication data migration...")
    print("=" * 60)
    
    # Migrate users
    print("\n📋 Migrating users...")
    users_success = migrate_users_from_json()
    
    # Migrate API keys
    print("\n🔑 Migrating API keys...")
    api_keys_success = migrate_api_keys_from_json()
    
    print("\n" + "=" * 60)
    if users_success and api_keys_success:
        print("✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Update auth system to use database models")
        print("2. Test authentication with existing credentials")
        print("3. Remove JSON file dependencies from auth code")
    else:
        print("❌ Migration completed with errors")
        print("Please review the errors above and fix them before proceeding")
    
    return users_success and api_keys_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)