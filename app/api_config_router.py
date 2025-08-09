"""
API Configuration Router
FastAPI endpoints for managing API configurations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from api_config import api_config_manager
from auth.utils import get_current_user_or_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["API Configuration"])

class APIConfigUpdate(BaseModel):
    """Model for API configuration updates"""
    config: Dict[str, Any]

class ServiceConfigUpdate(BaseModel):
    """Model for individual service configuration updates"""
    workflow: str
    category: str
    service: str
    config: Dict[str, Any]

@router.get("/api-configs")
async def get_api_configs(token_data=Depends(get_current_user_or_key)):
    """
    Get all API configurations.
    Requires authentication.
    """
    try:
        config = api_config_manager.load_config()
        
        # Remove sensitive metadata for frontend
        if "metadata" in config:
            config["metadata"] = {
                "version": config["metadata"].get("version", "1.0"),
                "last_loaded": config["metadata"].get("last_loaded")
            }
        
        return {
            "success": True,
            "data": config,
            "message": "API configurations loaded successfully"
        }
    except Exception as e:
        logger.error(f"Error getting API configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to load API configurations")

@router.post("/api-configs")
async def save_api_configs(config_update: APIConfigUpdate, token_data=Depends(get_current_user_or_key)):
    """
    Save API configurations.
    Requires authentication.
    """
    try:
        success = api_config_manager.save_config(config_update.config)
        
        if success:
            return {
                "success": True,
                "message": "API configurations saved successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save configurations")
    
    except Exception as e:
        logger.error(f"Error saving API configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to save API configurations")

@router.get("/api-configs/{workflow}")
async def get_workflow_configs(workflow: str, token_data=Depends(get_current_user_or_key)):
    """
    Get API configurations for a specific workflow (preproduction, production, promotion).
    """
    try:
        config = api_config_manager.load_config()
        workflow_config = config.get(workflow)
        
        if not workflow_config:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow}' not found")
        
        return {
            "success": True,
            "data": workflow_config,
            "message": f"Configuration for {workflow} loaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {workflow} configs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load {workflow} configurations")

@router.post("/api-configs/service")
async def update_service_config(service_update: ServiceConfigUpdate, token_data=Depends(get_current_user_or_key)):
    """
    Update configuration for a specific service.
    """
    try:
        success = api_config_manager.update_service_config(
            service_update.workflow,
            service_update.category,
            service_update.service,
            service_update.config
        )
        
        if success:
            return {
                "success": True,
                "message": f"Configuration for {service_update.service} updated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update service configuration")
    
    except Exception as e:
        logger.error(f"Error updating service config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update service configuration")

@router.post("/test/{service}")
async def test_api_connection(service: str, token_data=Depends(get_current_user_or_key)):
    """
    Test API connection for a specific service.
    This is a placeholder - actual implementation would test real API connections.
    """
    try:
        # Get service configuration
        config = api_config_manager.load_config()
        
        # Find service in all workflows and categories
        service_config = None
        workflow_found = None
        category_found = None
        
        for workflow_name, workflow_data in config.items():
            if workflow_name == "metadata":
                continue
            for category_name, category_data in workflow_data.items():
                if service in category_data:
                    service_config = category_data[service]
                    workflow_found = workflow_name
                    category_found = category_name
                    break
            if service_config:
                break
        
        if not service_config:
            raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
        
        if not service_config.get('enabled', False):
            raise HTTPException(status_code=400, detail=f"Service '{service}' is not enabled")
        
        # Validate credentials
        has_credentials = api_config_manager.validate_service_credentials(
            workflow_found, category_found, service
        )
        
        if not has_credentials:
            raise HTTPException(status_code=400, detail=f"Missing required credentials for '{service}'")
        
        # TODO: Implement actual API testing logic for each service
        # For now, simulate testing
        import asyncio
        await asyncio.sleep(1)  # Simulate network delay
        
        # Random success/failure for demonstration
        import random
        if random.random() > 0.2:  # 80% success rate
            return {
                "success": True,
                "message": f"Connection to {service} successful",
                "service": service,
                "status": "connected"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Connection to {service} failed")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing {service} connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test {service} connection")

@router.delete("/api-configs")
async def reset_api_configs(token_data=Depends(get_current_user_or_key)):
    """
    Reset API configurations to defaults.
    This will remove all saved configurations!
    """
    try:
        # Create backup before reset
        import shutil
        import os
        from datetime import datetime
        
        backup_name = f"api_configs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join("app/storage", backup_name)
        
        if os.path.exists(api_config_manager.config_file):
            shutil.copy2(api_config_manager.config_file, backup_path)
        
        # Remove current config file to trigger default creation
        if os.path.exists(api_config_manager.config_file):
            os.remove(api_config_manager.config_file)
        
        # Load (which will create defaults)
        api_config_manager.load_config()
        
        return {
            "success": True,
            "message": "API configurations reset to defaults",
            "backup_created": backup_name
        }
    
    except Exception as e:
        logger.error(f"Error resetting API configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset API configurations")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for API configuration service.
    No authentication required.
    """
    try:
        # Check if config file exists and is readable
        config = api_config_manager.load_config()
        
        return {
            "success": True,
            "status": "healthy",
            "config_version": config.get("metadata", {}).get("version", "unknown"),
            "timestamp": config.get("metadata", {}).get("last_loaded")
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
