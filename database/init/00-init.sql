-- =====================================================
-- Saras Trading Platform - Database Initialization
-- =====================================================
-- Main entry point for database setup
-- This file orchestrates the complete database initialization
-- by executing schema and seed files in the correct order
--
-- Run order: Execute this file first on a fresh database
-- Prerequisites: PostgreSQL 12+ with superuser privileges
-- =====================================================

\echo '=========================================='
\echo 'Saras Trading Platform - Database Setup'
\echo 'Starting initialization...'
\echo '=========================================='

-- =====================================================
-- PHASE 1: Extensions and Database Configuration
-- =====================================================
\echo ''
\echo 'Phase 1: Setting up extensions...'
\i /docker-entrypoint-initdb.d/schema/01-extensions.sql

-- =====================================================
-- PHASE 2: Functions and Stored Procedures
-- =====================================================
\echo ''
\echo 'Phase 2: Creating functions...'
\i /docker-entrypoint-initdb.d/schema/02-functions.sql

-- =====================================================
-- PHASE 3: Table Creation
-- =====================================================
\echo ''
\echo 'Phase 3: Creating core tables...'
\i /docker-entrypoint-initdb.d/schema/03-core-tables.sql

\echo ''
\echo 'Phase 3: Creating auth tables...'
\i /docker-entrypoint-initdb.d/schema/06-auth-tables.sql

\echo ''
\echo 'Phase 3: Creating broker tables...'
\i /docker-entrypoint-initdb.d/schema/07-broker-tables.sql

\echo ''
\echo 'Phase 3: Creating trading tables...'
\i /docker-entrypoint-initdb.d/schema/04-trading-tables.sql

\echo ''
\echo 'Phase 3: Creating smallcase tables...'
\i /docker-entrypoint-initdb.d/schema/05-smallcase-tables.sql

\echo ''
\echo 'Phase 3: Creating dividend tables...'
\i /docker-entrypoint-initdb.d/schema/08-dividend-tables.sql

-- =====================================================
-- PHASE 4: Triggers and Indexes
-- =====================================================
\echo ''
\echo 'Phase 4: Creating triggers and indexes...'
\i /docker-entrypoint-initdb.d/schema/09-triggers-indexes.sql

-- =====================================================
-- PHASE 5: Seed Data
-- =====================================================
\echo ''
\echo 'Phase 5: Loading initial configuration...'
\i /docker-entrypoint-initdb.d/seed/01-initial-config.sql

\echo ''
\echo 'Phase 5: Loading Indian stocks and ETFs...'
\i /docker-entrypoint-initdb.d/seed/02-indian-stocks.sql

\echo ''
\echo 'Phase 5: Loading US stocks and ETFs...'
\i /docker-entrypoint-initdb.d/seed/03-us-stocks.sql

\echo ''
\echo 'Phase 5: Loading Indian smallcases...'
\i /docker-entrypoint-initdb.d/seed/04-indian-smallcases.sql

\echo ''
\echo 'Phase 5: Loading US smallcases...'
\i /docker-entrypoint-initdb.d/seed/05-us-smallcases.sql

-- =====================================================
-- PHASE 6: Verification
-- =====================================================
\echo ''
\echo '=========================================='
\echo 'Database initialization complete!'
\echo '=========================================='
\echo ''
\echo 'Summary:'
SELECT
    'Tables created: ' || COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

SELECT
    'Indian stocks loaded: ' || COUNT(*)
FROM assets
WHERE region = 'India' AND asset_type = 'STOCK';

SELECT
    'US stocks loaded: ' || COUNT(*)
FROM assets
WHERE region = 'US' AND asset_type = 'STOCK';

SELECT
    'Indian smallcases loaded: ' || COUNT(*)
FROM smallcases
WHERE region = 'India';

SELECT
    'US smallcases loaded: ' || COUNT(*)
FROM smallcases
WHERE region = 'US';

SELECT
    'Total constituents configured: ' || COUNT(*)
FROM smallcase_constituents;

\echo ''
\echo '=========================================='
\echo 'Ready to start services!'
\echo '=========================================='
