"""
API Configuration Management
Handles storage and retrieval of API keys and configurations for all external services.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class APIConfigManager:
    """Manages API configurations with encryption and file-based storage."""
    
    def __init__(self, config_dir: str = "app/storage"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "api_configs.json")
        self.backup_file = os.path.join(config_dir, "api_configs_backup.json")
        self.key_file = os.path.join(config_dir, "encryption.key")
        
        # Ensure storage directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize encryption
        self.cipher_suite = self._get_or_create_cipher()
        
        # Initialize empty config if none exists
        if not os.path.exists(self.config_file):
            self._create_default_config()
    
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
    
    def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in the configuration."""
        encrypted_data = data.copy()
        
        # Fields that should be encrypted
        sensitive_fields = [
            'apiKey', 'api_key', 'accessToken', 'access_token', 
            'clientSecret', 'client_secret', 'authToken', 'auth_token',
            'apiSecret', 'api_secret', 'serviceAccount', 'botToken',
            'webhookUrl', 'secretAccessKey'
        ]
        
        def encrypt_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in sensitive_fields and isinstance(value, str) and value:
                        obj[key] = self.cipher_suite.encrypt(value.encode()).decode()
                    elif isinstance(value, (dict, list)):
                        encrypt_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        encrypt_recursive(item)
        
        encrypt_recursive(encrypted_data)
        return encrypted_data
    
    def _decrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in the configuration."""
        decrypted_data = data.copy()
        
        sensitive_fields = [
            'apiKey', 'api_key', 'accessToken', 'access_token', 
            'clientSecret', 'client_secret', 'authToken', 'auth_token',
            'apiSecret', 'api_secret', 'serviceAccount', 'botToken',
            'webhookUrl', 'secretAccessKey'
        ]
        
        def decrypt_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in sensitive_fields and isinstance(value, str) and value:
                        try:
                            obj[key] = self.cipher_suite.decrypt(value.encode()).decode()
                        except Exception:
                            # If decryption fails, assume it's already decrypted
                            pass
                    elif isinstance(value, (dict, list)):
                        decrypt_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        decrypt_recursive(item)
        
        decrypt_recursive(decrypted_data)
        return decrypted_data
    
    def _create_default_config(self):
        """Create default configuration structure."""
        default_config = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "description": "API configurations for pre-production, production, and promotion workflows"
            },
            "preproduction": {
                "ai_services": {
                    "ollama": {"host": "", "apiKey": "", "enabled": False},
                    "whisper": {"host": "", "endpoint": "", "enabled": False},
                    "openai": {"apiKey": "", "organization": "", "enabled": False},
                    "anthropic": {"apiKey": "", "enabled": False},
                    "gemini": {"apiKey": "", "enabled": False},
                    "grok": {"apiKey": "", "enabled": False},
                    "stabilityAi": {"apiKey": "", "enabled": False},
                    "elevenLabs": {"apiKey": "", "enabled": False}
                },
                "storage": {
                    "google": {
                        "clientId": "",
                        "clientSecret": "",
                        "serviceAccount": "",
                        "driveEnabled": False,
                        "calendarEnabled": False
                    },
                    "aws": {
                        "accessKeyId": "",
                        "secretAccessKey": "",
                        "region": "",
                        "bucket": "",
                        "enabled": False
                    }
                },
                "communication": {
                    "slack": {"botToken": "", "webhookUrl": "", "enabled": False},
                    "discord": {"botToken": "", "webhookUrl": "", "enabled": False},
                    "twilio": {"accountSid": "", "authToken": "", "phoneNumber": "", "enabled": False},
                    "email": {"provider": "", "apiKey": "", "fromEmail": "", "enabled": False}
                }
            },
            "production": {
                "streaming": {},
                "recording": {},
                "live_control": {}
            },
            "promotion": {
                "social_media": {
                    "youtube": {"apiKey": "", "clientId": "", "enabled": False},
                    "vimeo": {"accessToken": "", "enabled": False},
                    "twitter": {"apiKey": "", "apiSecret": "", "accessToken": "", "enabled": False},
                    "facebook": {"accessToken": "", "pageId": "", "enabled": False},
                    "instagram": {"accessToken": "", "enabled": False},
                    "linkedin": {"accessToken": "", "enabled": False},
                    "tiktok": {"accessToken": "", "enabled": False},
                    "rumble": {"apiKey": "", "channelId": "", "enabled": False}
                },
                "analytics": {},
                "advertising": {}
            },
            "development": {
                "github": {"accessToken": "", "organization": "", "enabled": False},
                "gitlab": {"accessToken": "", "baseUrl": "https://gitlab.com", "enabled": False},
                "zapier": {"webhookUrl": "", "enabled": False},
                "webhooks": [],
                "customEndpoints": []
            }
        }
        
        self.save_config(default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """Load and decrypt configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                encrypted_config = json.load(f)
            
            # Decrypt sensitive data
            config = self._decrypt_sensitive_data(encrypted_config)
            
            # Add metadata
            config["metadata"]["last_loaded"] = datetime.now().isoformat()
            
            return config
            
        except FileNotFoundError:
            logger.warning("Config file not found, creating default")
            self._create_default_config()
            return self.load_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise HTTPException(status_code=500, detail="Failed to load API configuration")
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Encrypt and save configuration to file."""
        try:
            # Create backup of existing config
            if os.path.exists(self.config_file):
                import shutil
                shutil.copy2(self.config_file, self.backup_file)
            
            # Add metadata
            config["metadata"] = config.get("metadata", {})
            config["metadata"]["last_saved"] = datetime.now().isoformat()
            
            # Encrypt sensitive data
            encrypted_config = self._encrypt_sensitive_data(config)
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(encrypted_config, f, indent=2)
            
            logger.info("API configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
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
            # Add more as needed
        }
        
        required = required_fields.get(service, [])
        return all(service_config.get(field) for field in required)

# Global instance
api_config_manager = APIConfigManager()
