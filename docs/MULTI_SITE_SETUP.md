# Multi-Site Database Redundancy Setup

This document outlines the complete setup process for redundant database servers across multiple colocated sites for the Show-Build application.

## Architecture Overview

### Primary Site: Ravena, NY
- **Role**: Primary database server with read/write access
- **Configuration**: PostgreSQL 15 with streaming replication
- **Network**: WireGuard VPN (10.0.1.0/24)
- **Hardware**: Two servers for local redundancy

### Replica Sites
- **Burlington, VT**: 10.0.2.0/24
- **Montpelier, VT**: 10.0.3.0/24  
- **Nantucket, MA**: 10.0.4.0/24
- **Tucson, AZ**: 10.0.5.0/24

Each replica site provides:
- Read-only database access
- Automatic failover capability
- Local backup storage
- Application redundancy

## Prerequisites

### Hardware Requirements
- **Primary Site (Ravena)**: 2x Ubuntu servers
- **Replica Sites**: 1x Ubuntu server each (minimum)
- All servers: 4GB RAM, 50GB storage, Gigabit ethernet

### Software Requirements
- Ubuntu 22.04 LTS
- Docker & Docker Compose
- WireGuard VPN
- PostgreSQL 15
- Show-Build application

### Network Requirements
- Static IP addresses at each site
- WireGuard VPN mesh between all sites
- Port forwarding: 5432 (PostgreSQL), 51820 (WireGuard)

## Setup Process

### Phase 1: Primary Site Setup (Ravena, NY)

#### 1. Install Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install WireGuard
sudo apt install wireguard
```

#### 2. Configure WireGuard
```bash
# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Create WireGuard config
sudo nano /etc/wireguard/wg0.conf
```

**Primary Site WireGuard Config:**
```ini
[Interface]
PrivateKey = <PRIVATE_KEY_HERE>
Address = 10.0.1.1/24
ListenPort = 51820
SaveConfig = true

# Burlington, VT
[Peer]
PublicKey = <BURLINGTON_PUBLIC_KEY>
AllowedIPs = 10.0.2.0/24
Endpoint = <BURLINGTON_PUBLIC_IP>:51820

# Montpelier, VT
[Peer]
PublicKey = <MONTPELIER_PUBLIC_KEY>
AllowedIPs = 10.0.3.0/24
Endpoint = <MONTPELIER_PUBLIC_IP>:51820

# Nantucket, MA
[Peer]
PublicKey = <NANTUCKET_PUBLIC_KEY>
AllowedIPs = 10.0.4.0/24
Endpoint = <NANTUCKET_PUBLIC_IP>:51820

# Tucson, AZ
[Peer]
PublicKey = <TUCSON_PUBLIC_KEY>
AllowedIPs = 10.0.5.0/24
Endpoint = <TUCSON_PUBLIC_IP>:51820
```

#### 3. Start WireGuard
```bash
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0
```

#### 4. Deploy Primary Database
```bash
# Clone Show-Build repository
git clone <repository-url>
cd show-build

# Start primary database
docker compose -f docker-compose.postgres-primary.yml up -d

# Verify database is running
docker logs show-build-postgres-primary
```

#### 5. Initialize Database
```bash
# Connect and create initial schema
docker exec -it show-build-postgres-primary psql -U showbuild -d showbuild

-- Run initialization SQL from postgres-config/primary/init-replication.sql
```

### Phase 2: Replica Site Setup

#### 1. Burlington, VT Setup
```bash
# Install same prerequisites as primary
# Configure WireGuard with Burlington-specific settings

# WireGuard config for Burlington
sudo nano /etc/wireguard/wg0.conf
```

**Burlington WireGuard Config:**
```ini
[Interface]
PrivateKey = <BURLINGTON_PRIVATE_KEY>
Address = 10.0.2.1/24
ListenPort = 51820

[Peer]
PublicKey = <RAVENA_PUBLIC_KEY>
AllowedIPs = 10.0.1.0/24, 10.0.3.0/24, 10.0.4.0/24, 10.0.5.0/24
Endpoint = <RAVENA_PUBLIC_IP>:51820
PersistentKeepalive = 25
```

#### 2. Deploy Replica Database
```bash
# Clone repository
git clone <repository-url>
cd show-build

# Configure replica to connect to primary
export PRIMARY_HOST=10.0.1.1
export PRIMARY_PORT=5432

# Start replica database
docker compose -f docker-compose.postgres-replica.yml up -d

# Verify replication
docker logs show-build-postgres-replica-burlington
```

#### 3. Test Replication
```bash
# On primary (Ravena)
docker exec -it show-build-postgres-primary psql -U showbuild -d showbuild
INSERT INTO test_table VALUES ('replication test');

# On replica (Burlington)
docker exec -it show-build-postgres-replica-burlington psql -U showbuild -d showbuild
SELECT * FROM test_table; -- Should show the inserted data
```

### Phase 3: Application Deployment

#### 1. Frontend Configuration
Access the Show-Build setup interface at `http://<server-ip>:8080/setup`:

1. **Database Configuration**:
   - Host: Primary database IP (10.0.1.1)
   - Port: 5432
   - Database: showbuild
   - Username: showbuild
   - Password: [configured password]

2. **Site Configuration**:
   - Enable desired replica sites
   - Configure WireGuard IPs for each site
   - Set replication modes (async/sync)

3. **Network Setup**:
   - Enter WireGuard public/private keys
   - Configure peer connections
   - Test connectivity to all sites

4. **Verification**:
   - Run comprehensive system verification
   - Confirm database connectivity
   - Test replication lag
   - Verify failover capabilities

#### 2. Application Services
```bash
# Start Show-Build application stack
docker compose up -d

# Verify all services
docker compose ps
curl http://localhost:8888/health
```

### Phase 4: Monitoring and Maintenance

#### 1. Health Monitoring
Set up monitoring for:
- Database connection status
- Replication lag
- Disk space usage
- Network connectivity
- Backup completion

#### 2. Backup Strategy
```bash
# Automated daily backups
crontab -e
# Add: 0 2 * * * /opt/show-build/scripts/backup-database.sh
```

#### 3. Failover Procedures
In case of primary site failure:
1. Promote Burlington replica to primary
2. Update DNS/load balancer
3. Reconfigure other replicas
4. Notify all sites of topology change

## Configuration Files Reference

### Docker Compose Files
- `docker-compose.postgres-primary.yml`: Primary database server
- `docker-compose.postgres-replica.yml`: Replica database server
- `docker-compose.yml`: Main application stack

### PostgreSQL Configuration
- `postgres-config/primary/postgresql.conf`: Primary server config
- `postgres-config/primary/pg_hba.conf`: Primary authentication
- `postgres-config/replica/postgresql.conf`: Replica server config
- `postgres-config/replica/pg_hba.conf`: Replica authentication

### Application Configuration
Configuration is stored in `/app/config/`:
- `database.json`: Database connection settings
- `sites.json`: Multi-site configuration
- `network.json`: WireGuard network settings

## Troubleshooting

### Common Issues

1. **Replication Lag**
   ```bash
   # Check replication status
   SELECT * FROM pg_stat_replication;
   ```

2. **Network Connectivity**
   ```bash
   # Test WireGuard connectivity
   ping 10.0.2.1  # Burlington
   ping 10.0.3.1  # Montpelier
   ```

3. **Database Connection Issues**
   ```bash
   # Check PostgreSQL logs
   docker logs show-build-postgres-primary
   docker logs show-build-postgres-replica-burlington
   ```

4. **Configuration Problems**
   - Verify `/app/config/` files exist and are readable
   - Check Docker network connectivity
   - Confirm WireGuard keys are correct

### Monitoring Commands
```bash
# Check replication slots
SELECT slot_name, active, restart_lsn FROM pg_replication_slots;

# Monitor replication lag
SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;

# Check database sizes
SELECT pg_size_pretty(pg_database_size('showbuild')) AS size;

# View active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

## Security Considerations

1. **Network Security**
   - WireGuard provides end-to-end encryption
   - Database access limited to VPN network
   - Regular security updates on all servers

2. **Database Security**
   - Separate replication user with limited privileges
   - SSL/TLS encryption for all connections
   - Regular password rotation

3. **Access Control**
   - SSH key-based authentication
   - Firewall rules limiting port access
   - Application-level authentication required

## Expansion to Additional Sites

To add new sites:
1. Install hardware and software prerequisites
2. Generate WireGuard keys and configure VPN
3. Update all existing sites with new peer configuration
4. Deploy replica database using existing templates
5. Add site configuration via Show-Build setup interface
6. Test connectivity and replication

## Maintenance Schedule

### Daily
- Automated backups
- Health check monitoring
- Log rotation

### Weekly
- Replication lag analysis
- Disk space monitoring
- Network connectivity tests

### Monthly
- Security updates
- Performance tuning
- Backup restoration tests

### Quarterly
- Disaster recovery drills
- Configuration audits
- Hardware health checks

This multi-site setup provides robust redundancy for the Show-Build application while maintaining high availability and data consistency across all locations.