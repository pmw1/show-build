-- PostgreSQL Primary Server Initialization
-- Create replication user and configure for streaming replication

-- Create replication user
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'replicator_secure_2025';

-- Create publication for logical replication (if needed later)
CREATE PUBLICATION showbuild_pub FOR ALL TABLES;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE showbuild TO replicator;
GRANT USAGE ON SCHEMA public TO replicator;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO replicator;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO replicator;

-- Set default privileges for new objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO replicator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO replicator;

-- Create replication slot for each potential replica site
SELECT pg_create_physical_replication_slot('ravena_replica');
SELECT pg_create_physical_replication_slot('burlington_replica');
SELECT pg_create_physical_replication_slot('montpelier_replica');
SELECT pg_create_physical_replication_slot('nantucket_replica');
SELECT pg_create_physical_replication_slot('tucson_replica');

-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Log successful initialization
INSERT INTO public.system_log (level, message, timestamp) 
VALUES ('INFO', 'PostgreSQL primary server initialized with replication configuration', NOW())
ON CONFLICT DO NOTHING;