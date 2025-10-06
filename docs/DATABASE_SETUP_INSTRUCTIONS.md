# Database Setup Instructions for Show-Build

This manual provides step-by-step instructions to set up a PostgreSQL database server in Docker exactly as needed for the Show-Build application.

## Quick Setup

### 1. Create Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: show-build-postgres
    environment:
      POSTGRES_DB: showbuild
      POSTGRES_USER: showbuild
      POSTGRES_PASSWORD: showbuild_password_2024
      POSTGRES_HOST_AUTH_METHOD: md5
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d/
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U showbuild -d showbuild"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 2. Create Initialization Script

Create `init-scripts/01-init-database.sql`:

```sql
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
ALTER DATABASE showbuild SET timezone TO 'UTC';

-- Create schemas if needed
-- (Show-Build uses default public schema)

-- Verify setup
SELECT version();
SELECT current_database();
SELECT current_user;
```

### 3. Start Database Server

```bash
# Start the database
docker compose up -d postgres

# Verify it's running
docker ps | grep postgres

# Check logs
docker logs show-build-postgres

# Test connection
docker exec show-build-postgres psql -U showbuild -d showbuild -c "SELECT 1;"
```

## Database Configuration Details

### Connection Parameters
- **Host**: `localhost` (from host) or `postgres` (from other containers)
- **Port**: `5432`
- **Database**: `showbuild`
- **Username**: `showbuild`
- **Password**: `showbuild_password_2024`
- **URL**: `postgresql://showbuild:showbuild_password_2024@localhost:5432/showbuild`

### Required Tables Schema

The Show-Build application expects these table structures (created automatically by Alembic migrations):

#### Core Tables
```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    access_level VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Settings table (critical for color configurations)
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSON NOT NULL,
    category VARCHAR(50),
    user_id INTEGER REFERENCES users(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Episodes (legacy support)
CREATE TABLE episodes_legacy (
    id SERIAL PRIMARY KEY,
    episode_number VARCHAR(4) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    airdate TIMESTAMP,
    status VARCHAR(20) DEFAULT 'draft',
    duration VARCHAR(10),
    guest VARCHAR(255),
    tags JSON DEFAULT '[]',
    slug VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    last_compiled TIMESTAMP,
    last_quote_extraction TIMESTAMP,
    episode_path VARCHAR(500) NOT NULL
);

-- Rundown items
CREATE TABLE rundown_items_legacy (
    id SERIAL PRIMARY KEY,
    episode_id INTEGER REFERENCES episodes_legacy(id) NOT NULL,
    asset_id VARCHAR(50) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL,
    "order" INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration VARCHAR(10),
    priority VARCHAR(20),
    status VARCHAR(20) DEFAULT 'draft',
    script_content TEXT,
    notes TEXT,
    resources TEXT,
    guests VARCHAR(255),
    tags JSON DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE,
    file_path VARCHAR(500) NOT NULL
);
```

#### RBAC Tables
```sql
-- Permissions
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Roles
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Groups  
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Relationship tables
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    assigned_by INTEGER REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

-- (Additional RBAC tables: user_groups, role_permissions, etc.)
```

## Setting Up Database Schema

### Option 1: Using Alembic (Recommended)

1. **Install Python dependencies** (in your application environment):
```bash
pip install alembic sqlalchemy psycopg2-binary
```

2. **Configure Alembic** - Create `alembic.ini`:
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://showbuild:showbuild_password_2024@localhost:5432/showbuild

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

3. **Run migrations**:
```bash
# Initialize Alembic (if needed)
alembic init alembic

# Run migrations to create all tables
alembic upgrade head
```

### Option 2: Manual SQL Import

If you have an existing schema dump:

```bash
# Import schema from SQL file
docker exec -i show-build-postgres psql -U showbuild -d showbuild < schema_dump.sql

# Or connect and run SQL manually
docker exec -it show-build-postgres psql -U showbuild -d showbuild
```

## Initial Data Setup

### 1. Create Default Settings

```sql
-- Insert default color settings
INSERT INTO settings (key, value, category, description) VALUES (
    'theme_colors_default',
    '{"segment": "info", "ad": "primary", "promo": "success", "cta": "accent", "trans": "secondary", "unknown": "grey", "Selection-interface": "warning", "Hover-interface": "blue-lighten-4", "Highlight-interface": "yellow-lighten-3", "Dropline-interface": "green-lighten-4", "DragLight-interface": "cyan-lighten-4", "Draft-script": "grey-darken-2", "Approved-script": "green-accent", "Production-script": "blue-accent", "Completed-script": "yellow-accent"}',
    'colors',
    'Default theme color configuration'
);

-- Insert default theme settings
INSERT INTO settings (key, value, category, description) VALUES (
    'theme_settings_default',
    '{"theme": "dark"}',
    'theme',
    'Default theme settings'
);
```

### 2. Create Default User (Optional)

```sql
-- Create admin user (password: 'admin123' - change this!)
INSERT INTO users (username, email, hashed_password, access_level) VALUES (
    'admin',
    'admin@showbuild.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXzgVU3hfmvu',
    'admin'
);
```

## Testing Database Connection

### From Host System

```bash
# Using psql (if installed)
psql postgresql://showbuild:showbuild_password_2024@localhost:5432/showbuild -c "SELECT version();"

# Using Docker
docker exec show-build-postgres psql -U showbuild -d showbuild -c "SELECT version();"

# Test specific tables
docker exec show-build-postgres psql -U showbuild -d showbuild -c "\dt"
```

### From Application

```python
# Test connection from Python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="showbuild",
    user="showbuild",
    password="showbuild_password_2024"
)

cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())
conn.close()
```

## Environment Variables

Set these environment variables for the application:

```bash
# Database connection
DATABASE_URL=postgresql://showbuild:showbuild_password_2024@localhost:5432/showbuild
DB_HOST=localhost
DB_PORT=5432
DB_NAME=showbuild
DB_USER=showbuild
DB_PASSWORD=showbuild_password_2024

# Application settings
JWT_SECRET_KEY=your_super_secret_key_change_this_in_production
MEDIA_ROOT=/path/to/media/files
```

## Backup and Maintenance

### Backup Database

```bash
# Full database backup
docker exec show-build-postgres pg_dump -U showbuild showbuild > backup_$(date +%Y%m%d_%H%M%S).sql

# Schema only
docker exec show-build-postgres pg_dump -U showbuild --schema-only showbuild > schema_$(date +%Y%m%d_%H%M%S).sql

# Data only
docker exec show-build-postgres pg_dump -U showbuild --data-only showbuild > data_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
docker exec -i show-build-postgres psql -U showbuild -d showbuild < backup_file.sql
```

### Database Maintenance

```sql
-- Connect to database
docker exec -it show-build-postgres psql -U showbuild -d showbuild

-- Check database size
SELECT pg_size_pretty(pg_database_size('showbuild'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum and analyze
VACUUM ANALYZE;
```

## Troubleshooting

### Connection Issues

```bash
# Check if container is running
docker ps | grep postgres

# Check container logs
docker logs show-build-postgres

# Check if port is available
netstat -tlnp | grep 5432

# Test connection from container
docker exec show-build-postgres pg_isready -U showbuild -d showbuild
```

### Permission Issues

```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE showbuild TO showbuild;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO showbuild;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO showbuild;
```

### Performance Tuning

Add to `docker-compose.yml` postgres service:

```yaml
command: [
  "postgres",
  "-c", "max_connections=100",
  "-c", "shared_buffers=256MB",
  "-c", "effective_cache_size=1GB",
  "-c", "work_mem=4MB",
  "-c", "maintenance_work_mem=64MB"
]
```

## Complete Docker Compose Example

Here's a complete `docker-compose.yml` with database and application:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: show-build-postgres
    environment:
      POSTGRES_DB: showbuild
      POSTGRES_USER: showbuild
      POSTGRES_PASSWORD: showbuild_password_2024
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U showbuild -d showbuild"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: show-build-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  app:
    build: .
    container_name: show-build-app
    environment:
      DATABASE_URL: postgresql://showbuild:showbuild_password_2024@postgres:5432/showbuild
      REDIS_URL: redis://redis:6379
    ports:
      - "8888:8888"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./episodes:/home/episodes
      - ./shared_media:/shared_media
    restart: unless-stopped

volumes:
  postgres_data:
```

## Summary

1. **Create the Docker Compose file** with PostgreSQL configuration
2. **Start the database**: `docker compose up -d postgres`  
3. **Run migrations** to create schema: `alembic upgrade head`
4. **Insert default data** (colors, settings, admin user)
5. **Test connection** and verify tables exist
6. **Set environment variables** for the application
7. **Start the application** and verify database connectivity

The database will be ready for the Show-Build application with all required tables, indexes, and initial data.