"""
Setup management router for Show-Build application
Handles initial system configuration, database setup, and multi-site configuration
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import json
import asyncpg
import asyncio
import subprocess
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/setup", tags=["setup"])

# Configuration storage paths
CONFIG_DIR = Path("/app/config") if Path("/app").exists() else Path("app/config")
DB_CONFIG_FILE = CONFIG_DIR / "database.json"
SITE_CONFIG_FILE = CONFIG_DIR / "sites.json"
NETWORK_CONFIG_FILE = CONFIG_DIR / "network.json"

class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str = Field(..., description="Database hostname or IP")
    port: int = Field(5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    ssl: bool = Field(False, description="Enable SSL connection")

class SiteConfig(BaseModel):
    """Individual site configuration"""
    ip: str = Field(..., description="Server IP address")
    wireguardIp: str = Field(..., description="WireGuard VPN IP")
    enabled: bool = Field(False, description="Site enabled status")
    replicationMode: Optional[str] = Field("async", description="Replication mode")
    role: str = Field("replica", description="Site role (primary/replica)")

class NetworkConfig(BaseModel):
    """WireGuard network configuration"""
    publicKey: str = Field(..., description="WireGuard public key")
    privateKey: str = Field(..., description="WireGuard private key")
    listenPort: int = Field(51820, description="WireGuard listen port")
    endpoint: Optional[str] = Field(None, description="Public endpoint")

class SetupRequest(BaseModel):
    """Complete setup configuration"""
    database: DatabaseConfig
    sites: Dict[str, SiteConfig]
    network: NetworkConfig

class VerificationCheck(BaseModel):
    """Individual verification check result"""
    name: str
    status: str  # 'success', 'warning', 'error', 'pending'
    message: str

def ensure_config_directory():
    """Ensure configuration directory exists"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/test-database")
async def test_database_connection(config: DatabaseConfig) -> Dict[str, Any]:
    """Test database connection with provided configuration"""
    try:
        # Build connection string
        connection_params = {
            "host": config.host,
            "port": config.port,
            "database": config.database,
            "user": config.username,
            "password": config.password
        }
        
        if config.ssl:
            connection_params["ssl"] = "require"
        
        # Test connection
        conn = await asyncpg.connect(**connection_params)
        
        # Test basic query
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        
        return {
            "success": True,
            "message": f"Connected successfully to PostgreSQL",
            "version": version[:50] + "..." if len(version) > 50 else version
        }
        
    except asyncpg.InvalidAuthorizationSpecificationError:
        return {
            "success": False,
            "message": "Invalid username or password"
        }
    except asyncpg.InvalidCatalogNameError:
        return {
            "success": False,
            "message": f"Database '{config.database}' does not exist"
        }
    except OSError as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }

@router.post("/test-peer")
async def test_peer_connection(peer_config: Dict[str, Any]) -> Dict[str, Any]:
    """Test connectivity to a peer site"""
    ip = peer_config.get("ip")
    site = peer_config.get("site")
    
    if not ip:
        return {"success": False, "message": "IP address required"}
    
    try:
        # Test ping connectivity
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "2", ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Extract latency from ping output
            latency = "Unknown"
            for line in result.stdout.split('\n'):
                if "time=" in line:
                    latency = line.split("time=")[1].split()[0] + "ms"
                    break
            
            return {
                "success": True,
                "message": f"Peer {site} reachable",
                "latency": latency
            }
        else:
            return {
                "success": False,
                "message": f"Peer {site} unreachable",
                "latency": None
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": f"Peer {site} timeout",
            "latency": None
        }
    except Exception as e:
        logger.error(f"Peer connectivity test failed: {e}")
        return {
            "success": False,
            "message": f"Test failed: {str(e)}",
            "latency": None
        }

@router.post("/verify")
async def verify_configuration(setup: SetupRequest) -> Dict[str, Any]:
    """Run comprehensive verification of the setup configuration"""
    checks = []
    overall_success = True
    
    # Check 1: Database Connection
    try:
        db_test = await test_database_connection(setup.database)
        if db_test["success"]:
            checks.append(VerificationCheck(
                name="Database Connection",
                status="success",
                message=f"Connected to {setup.database.host}:{setup.database.port}"
            ))
        else:
            checks.append(VerificationCheck(
                name="Database Connection",
                status="error",
                message=db_test["message"]
            ))
            overall_success = False
    except Exception as e:
        checks.append(VerificationCheck(
            name="Database Connection",
            status="error",
            message=f"Test failed: {str(e)}"
        ))
        overall_success = False
    
    # Check 2: WireGuard Network Configuration
    if setup.network.publicKey and setup.network.privateKey:
        checks.append(VerificationCheck(
            name="WireGuard Network",
            status="success",
            message="WireGuard keys configured"
        ))
    else:
        checks.append(VerificationCheck(
            name="WireGuard Network",
            status="warning",
            message="WireGuard keys missing - peer connectivity may fail"
        ))
    
    # Check 3: Site Connectivity
    enabled_sites = [site for site, config in setup.sites.items() if config.enabled]
    if len(enabled_sites) > 1:  # More than just primary
        reachable_sites = 0
        for site_name, site_config in setup.sites.items():
            if site_config.enabled and site_name != 'ravena':
                try:
                    peer_test = await test_peer_connection({
                        "ip": site_config.wireguardIp,
                        "site": site_name
                    })
                    if peer_test["success"]:
                        reachable_sites += 1
                except Exception:
                    pass
        
        if reachable_sites > 0:
            checks.append(VerificationCheck(
                name="Site Connectivity",
                status="success" if reachable_sites == len(enabled_sites) - 1 else "warning",
                message=f"{reachable_sites}/{len(enabled_sites)-1} replica sites reachable"
            ))
        else:
            checks.append(VerificationCheck(
                name="Site Connectivity",
                status="error",
                message="No replica sites reachable"
            ))
            overall_success = False
    else:
        checks.append(VerificationCheck(
            name="Site Connectivity",
            status="success",
            message="Single-site configuration (primary only)"
        ))
    
    # Check 4: Replication Setup
    replica_count = sum(1 for config in setup.sites.values() if config.enabled and config.role == "replica")
    if replica_count > 0:
        checks.append(VerificationCheck(
            name="Replication Setup",
            status="success",
            message=f"{replica_count} replica sites configured"
        ))
    else:
        checks.append(VerificationCheck(
            name="Replication Setup",
            status="warning",
            message="No replica sites configured - no redundancy"
        ))
    
    # Check 5: Configuration Storage
    try:
        ensure_config_directory()
        checks.append(VerificationCheck(
            name="Configuration Storage",
            status="success",
            message=f"Configuration directory ready: {CONFIG_DIR}"
        ))
    except Exception as e:
        checks.append(VerificationCheck(
            name="Configuration Storage",
            status="error",
            message=f"Cannot create config directory: {str(e)}"
        ))
        overall_success = False
    
    return {
        "success": overall_success,
        "checks": [check.dict() for check in checks],
        "summary": {
            "total_sites": len([s for s in setup.sites.values() if s.enabled]),
            "replica_sites": replica_count,
            "replication_modes": list(set(s.replicationMode for s in setup.sites.values() if s.enabled and hasattr(s, 'replicationMode')))
        }
    }

@router.post("/save-config")
async def save_configuration(setup: SetupRequest) -> Dict[str, Any]:
    """Save configuration to local filesystem"""
    try:
        ensure_config_directory()
        
        # Save database configuration
        with open(DB_CONFIG_FILE, 'w') as f:
            json.dump(setup.database.dict(), f, indent=2)
        
        # Save site configurations
        with open(SITE_CONFIG_FILE, 'w') as f:
            json.dump({k: v.dict() for k, v in setup.sites.items()}, f, indent=2)
        
        # Save network configuration (without private key for security)
        network_config = setup.network.dict()
        network_config["privateKey"] = "***STORED_SECURELY***"  # Don't save plain text
        with open(NETWORK_CONFIG_FILE, 'w') as f:
            json.dump(network_config, f, indent=2)
        
        # Save private key separately with restricted permissions
        private_key_file = CONFIG_DIR / ".wireguard_private"
        with open(private_key_file, 'w') as f:
            f.write(setup.network.privateKey)
        os.chmod(private_key_file, 0o600)  # Owner read/write only
        
        logger.info("Configuration saved successfully")
        return {
            "success": True,
            "message": "Configuration saved to filesystem",
            "files": [
                str(DB_CONFIG_FILE),
                str(SITE_CONFIG_FILE), 
                str(NETWORK_CONFIG_FILE),
                str(private_key_file)
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@router.get("/load-config")
async def load_configuration() -> Dict[str, Any]:
    """Load existing configuration from filesystem"""
    config = {}
    
    try:
        # Load database config
        if DB_CONFIG_FILE.exists():
            with open(DB_CONFIG_FILE, 'r') as f:
                config["database"] = json.load(f)
        
        # Load site configs
        if SITE_CONFIG_FILE.exists():
            with open(SITE_CONFIG_FILE, 'r') as f:
                config["sites"] = json.load(f)
        
        # Load network config
        if NETWORK_CONFIG_FILE.exists():
            with open(NETWORK_CONFIG_FILE, 'r') as f:
                network_config = json.load(f)
                
            # Load private key separately
            private_key_file = CONFIG_DIR / ".wireguard_private"
            if private_key_file.exists():
                with open(private_key_file, 'r') as f:
                    network_config["privateKey"] = f.read().strip()
            
            config["network"] = network_config
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return {}

@router.get("/status")
async def get_setup_status() -> Dict[str, Any]:
    """Get current setup status"""
    status = {
        "configured": False,
        "database_configured": False,
        "sites_configured": False,
        "network_configured": False,
        "files_exist": {
            "database": DB_CONFIG_FILE.exists(),
            "sites": SITE_CONFIG_FILE.exists(), 
            "network": NETWORK_CONFIG_FILE.exists(),
            "private_key": (CONFIG_DIR / ".wireguard_private").exists()
        }
    }
    
    # Check if all required files exist
    status["configured"] = all([
        status["files_exist"]["database"],
        status["files_exist"]["sites"],
        status["files_exist"]["network"]
    ])
    
    status["database_configured"] = status["files_exist"]["database"]
    status["sites_configured"] = status["files_exist"]["sites"]
    status["network_configured"] = status["files_exist"]["network"] and status["files_exist"]["private_key"]
    
    return status

@router.delete("/reset")
async def reset_configuration() -> Dict[str, Any]:
    """Reset/clear all configuration"""
    try:
        files_removed = []
        
        # Remove configuration files
        for file_path in [DB_CONFIG_FILE, SITE_CONFIG_FILE, NETWORK_CONFIG_FILE, CONFIG_DIR / ".wireguard_private"]:
            if file_path.exists():
                file_path.unlink()
                files_removed.append(str(file_path))
        
        # Remove config directory if empty
        if CONFIG_DIR.exists() and not any(CONFIG_DIR.iterdir()):
            CONFIG_DIR.rmdir()
            files_removed.append(str(CONFIG_DIR))
        
        logger.info("Configuration reset successfully")
        return {
            "success": True,
            "message": "Configuration reset successfully",
            "files_removed": files_removed
        }
        
    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset configuration: {str(e)}")

@router.get("/docker-compose")
async def generate_docker_compose() -> Dict[str, Any]:
    """Generate Docker Compose configurations for multi-site deployment"""
    try:
        config = await load_configuration()
        
        if not config.get("sites"):
            raise HTTPException(status_code=404, detail="No site configuration found")
        
        # Generate primary server compose
        primary_compose = generate_primary_compose(config)
        
        # Generate replica server compose for each enabled site
        replica_composes = {}
        for site_name, site_config in config["sites"].items():
            if site_config.get("enabled") and site_config.get("role") == "replica":
                replica_composes[site_name] = generate_replica_compose(site_name, site_config, config)
        
        return {
            "success": True,
            "primary": primary_compose,
            "replicas": replica_composes
        }
        
    except Exception as e:
        logger.error(f"Failed to generate Docker Compose: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Docker Compose: {str(e)}")

def generate_primary_compose(config: Dict[str, Any]) -> str:
    """Generate Docker Compose configuration for primary server"""
    db_config = config.get("database", {})
    
    return f"""version: '3.8'

services:
  postgres-primary:
    image: postgres:15-alpine
    container_name: show-build-postgres-primary
    restart: unless-stopped
    environment:
      POSTGRES_DB: {db_config.get('database', 'showbuild')}
      POSTGRES_USER: {db_config.get('username', 'showbuild')}
      POSTGRES_PASSWORD: {db_config.get('password', 'showbuild_primary_2025')}
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: replicator_secure_2025
    ports:
      - "{db_config.get('port', 5432)}:5432"
    volumes:
      - postgres_primary_data:/var/lib/postgresql/data
      - ./postgres-config/primary:/docker-entrypoint-initdb.d
    networks:
      - postgres-replication
      - video-post

volumes:
  postgres_primary_data:
    driver: local

networks:
  postgres-replication:
    driver: bridge
  video-post:
    external: true
"""

def generate_replica_compose(site_name: str, site_config: Dict[str, Any], full_config: Dict[str, Any]) -> str:
    """Generate Docker Compose configuration for replica server"""
    db_config = full_config.get("database", {})
    primary_ip = full_config.get("sites", {}).get("ravena", {}).get("wireguardIp", "10.0.1.1")
    
    return f"""version: '3.8'

services:
  postgres-replica-{site_name}:
    image: postgres:15-alpine
    container_name: show-build-postgres-replica-{site_name}
    restart: unless-stopped
    environment:
      POSTGRES_DB: {db_config.get('database', 'showbuild')}
      POSTGRES_USER: {db_config.get('username', 'showbuild')}
      POSTGRES_PASSWORD: {db_config.get('password', 'showbuild_primary_2025')}
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: replicator_secure_2025
      POSTGRES_PRIMARY_HOST: {primary_ip}
      POSTGRES_PRIMARY_PORT: {db_config.get('port', 5432)}
    ports:
      - "5432:5432"
    volumes:
      - postgres_replica_{site_name}_data:/var/lib/postgresql/data
      - ./postgres-config/replica:/docker-entrypoint-initdb.d
    networks:
      - postgres-replication

volumes:
  postgres_replica_{site_name}_data:
    driver: local

networks:
  postgres-replication:
    driver: bridge
"""