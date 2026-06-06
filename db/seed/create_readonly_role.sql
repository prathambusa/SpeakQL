-- Run this as a superuser on your production PostgreSQL instance.
-- Creates a read-only role and grants it SELECT on all existing tables.

CREATE ROLE speakql_readonly WITH LOGIN PASSWORD 'changeme';

-- Grant connect on the database
GRANT CONNECT ON DATABASE northwind TO speakql_readonly;

-- Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO speakql_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO speakql_readonly;

-- Ensure future tables also get SELECT
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO speakql_readonly;

-- Then in .env set:
-- DB_PROD_URL=postgresql+asyncpg://speakql_readonly:changeme@host:5432/northwind
