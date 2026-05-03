"""
API Configuration Management
Handles storage and retrieval of API keys and configurations for all external services.
ALL DATA STORED IN DATABASE - NO JSON FILES.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import HTTPException
import logging
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)

class APIConfigManager:
    """Manages API configurations with encryption and DATABASE storage."""

    def __init__(self, config_dir: str = "app/storage"):
        self.config_dir = config_dir
        self.key_file = os.path.join(config_dir, "encryption.key")

        # Ensure storage directory exists for encryption key only
        os.makedirs(config_dir, exist_ok=True)

        # Initialize encryption
        self.cipher_suite = self._get_or_create_cipher()

        # Initialize database structure if needed
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure api_configs table exists in database."""
        with SessionLocal() as db:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS api_configs (
                    id SERIAL PRIMARY KEY,
                    workflow VARCHAR(50) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    service VARCHAR(50) NOT NULL,
                    config_key VARCHAR(100) NOT NULL,
                    config_value TEXT,
                    is_encrypted BOOLEAN DEFAULT FALSE,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(workflow, category, service, config_key)
                );
            """))
            db.commit()

    def _get_or_create_cipher(self) -> Fernet:
        """Get or create encryption cipher for sensitive data."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return Fernet(key)
    
    def _is_sensitive_field(self, key: str) -> bool:
        """Check if a field contains sensitive data."""
        sensitive_fields = [
            'apiKey', 'api_key', 'accessToken', 'access_token',
            'clientSecret', 'client_secret', 'authToken', 'auth_token',
            'apiSecret', 'api_secret', 'serviceAccount', 'botToken',
            'webhookUrl', 'secretAccessKey'
        ]
        return key in sensitive_fields

    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def load_config(self) -> Dict[str, Any]:
        """Load and decrypt configuration from DATABASE."""
        try:
            with SessionLocal() as db:
                result = db.execute(text("""
                    SELECT workflow, category, service, config_key, config_value, is_encrypted, is_enabled
                    FROM api_configs
                    ORDER BY workflow, category, service, config_key
                """))
                rows = result.fetchall()

            # Build nested config structure
            config = {"metadata": {"last_loaded": datetime.now().isoformat()}}

            for row in rows:
                workflow, category, service, key, value, is_encrypted, is_enabled = row

                # Initialize nested dict structure
                if workflow not in config:
                    config[workflow] = {}
                if category not in config[workflow]:
                    config[workflow][category] = {}
                if service not in config[workflow][category]:
                    config[workflow][category][service] = {}

                # Decrypt if needed
                if is_encrypted and value:
                    try:
                        value = self.cipher_suite.decrypt(value.encode()).decode()
                    except Exception as e:
                        logger.warning(f"Failed to decrypt {workflow}.{category}.{service}.{key}: {e}")

                # The 'enabled' state is stored as is_enabled on every row
                # for the service (set during save). Derive it from any row.
                if 'enabled' not in config[workflow][category][service]:
                    config[workflow][category][service]['enabled'] = bool(is_enabled)

                # Convert snake_case to camelCase for frontend compatibility
                camel_key = self._to_camel_case(key)

                # Store value (skip 'enabled' key rows — enabled is derived from is_enabled column)
                if key != 'enabled':
                    config[workflow][category][service][camel_key] = value or ""

            return config

        except Exception as e:
            logger.error(f"Error loading config from database: {e}")
            raise HTTPException(status_code=500, detail="Failed to load API configuration")
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Encrypt and save configuration to DATABASE."""
        try:
            with SessionLocal() as db:
                # Flatten nested config to database rows
                for workflow, workflow_data in config.items():
                    if workflow == "metadata":
                        continue

                    if not isinstance(workflow_data, dict):
                        continue

                    for category, category_data in workflow_data.items():
                        if not isinstance(category_data, dict):
                            continue

                        for service, service_data in category_data.items():
                            if not isinstance(service_data, dict):
                                continue

                            # Extract enabled flag
                            is_enabled = service_data.get('enabled', False)

                            # Save each config key
                            for key, value in service_data.items():
                                if key == 'enabled':
                                    continue

                                # Encrypt if sensitive
                                is_encrypted = self._is_sensitive_field(key)
                                stored_value = value

                                if is_encrypted and value:
                                    stored_value = self.cipher_suite.encrypt(str(value).encode()).decode()

                                # Upsert to database
                                db.execute(text("""
                                    INSERT INTO api_configs (workflow, category, service, config_key, config_value, is_encrypted, is_enabled, updated_at)
                                    VALUES (:workflow, :category, :service, :key, :value, :encrypted, :enabled, NOW())
                                    ON CONFLICT (workflow, category, service, config_key)
                                    DO UPDATE SET
                                        config_value = :value,
                                        is_encrypted = :encrypted,
                                        is_enabled = :enabled,
                                        updated_at = NOW()
                                """), {
                                    "workflow": workflow,
                                    "category": category,
                                    "service": service,
                                    "key": key,
                                    "value": stored_value,
                                    "encrypted": is_encrypted,
                                    "enabled": is_enabled
                                })

                db.commit()

            logger.info("API configuration saved successfully to database")
            return True

        except Exception as e:
            logger.error(f"Error saving config to database: {e}")
            raise HTTPException(status_code=500, detail="Failed to save API configuration")
    
    def get_service_config(self, workflow: str, category: str, service: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service."""
        config = self.load_config()
        return config.get(workflow, {}).get(category, {}).get(service)
    
    def update_service_config(self, workflow: str, category: str, service: str, service_config: Dict[str, Any]) -> bool:
        """Update configuration for a specific service."""
        config = self.load_config()
        
        if workflow not in config:
            config[workflow] = {}
        if category not in config[workflow]:
            config[workflow][category] = {}
        
        config[workflow][category][service] = service_config
        
        return self.save_config(config)
    
    def validate_service_credentials(self, workflow: str, category: str, service: str) -> bool:
        """Validate that required credentials are present for a service."""
        service_config = self.get_service_config(workflow, category, service)
        
        if not service_config or not service_config.get('enabled', False):
            return False
        
        # Define required fields per service
        required_fields = {
            'openai': ['apiKey'],
            'anthropic': ['apiKey'],
            'google': ['clientId'],
            'youtube': ['apiKey'],
            'slack': ['botToken'],
            'github': ['accessToken'],
            'xtts': ['host'],  # XTTS requires at least a host URL
            # Add more as needed
        }
        
        required = required_fields.get(service, [])
        return all(service_config.get(field) for field in required)

# Global instance
api_config_manager = APIConfigManager()
