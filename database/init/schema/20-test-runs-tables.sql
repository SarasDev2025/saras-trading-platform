-- Test Runs and Results Tables
-- Stores test execution history and results for tracking

-- Test runs tracking
CREATE TABLE IF NOT EXISTS test_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50),
    git_commit VARCHAR(40),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'running', -- running, passed, failed, error
    total_tests INT DEFAULT 0,
    passed_tests INT DEFAULT 0,
    failed_tests INT DEFAULT 0,
    skipped_tests INT DEFAULT 0,
    error_tests INT DEFAULT 0,
    coverage_pct NUMERIC(5,2),
    test_type VARCHAR(20) NOT NULL, -- api, ui, integration, all
    environment VARCHAR(20) DEFAULT 'development', -- development, staging, production
    duration_ms INT,
    triggered_by VARCHAR(100), -- user email or 'automated'

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Individual test results
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_run_id UUID NOT NULL REFERENCES test_runs(id) ON DELETE CASCADE,
    test_name VARCHAR(255) NOT NULL,
    test_file VARCHAR(500) NOT NULL,
    test_class VARCHAR(255),
    test_function VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL, -- passed, failed, skipped, error
    duration_ms INT,
    error_message TEXT,
    error_trace TEXT,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Markers/tags
    markers TEXT[], -- Array of pytest markers

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Database backups tracking
CREATE TABLE IF NOT EXISTS database_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    size_bytes BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    description TEXT,
    backup_type VARCHAR(20) DEFAULT 'full', -- full, incremental, pre-test
    restore_tested BOOLEAN DEFAULT FALSE,

    -- Metadata
    database_name VARCHAR(100),
    tables_count INT,
    rows_count BIGINT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_test_runs_status ON test_runs(status);
CREATE INDEX IF NOT EXISTS idx_test_runs_started_at ON test_runs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_test_runs_test_type ON test_runs(test_type);
CREATE INDEX IF NOT EXISTS idx_test_runs_environment ON test_runs(environment);

CREATE INDEX IF NOT EXISTS idx_test_results_test_run_id ON test_results(test_run_id);
CREATE INDEX IF NOT EXISTS idx_test_results_status ON test_results(status);
CREATE INDEX IF NOT EXISTS idx_test_results_test_name ON test_results(test_name);

CREATE INDEX IF NOT EXISTS idx_database_backups_created_at ON database_backups(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_database_backups_backup_type ON database_backups(backup_type);

-- Comments
COMMENT ON TABLE test_runs IS 'Tracks all test execution runs with summary statistics';
COMMENT ON TABLE test_results IS 'Stores individual test case results for each test run';
COMMENT ON TABLE database_backups IS 'Tracks database backup files for restore and testing';

COMMENT ON COLUMN test_runs.status IS 'Overall status: running, passed (all passed), failed (some failed), error (execution error)';
COMMENT ON COLUMN test_runs.test_type IS 'Type of tests run: api, ui, integration, or all';
COMMENT ON COLUMN test_results.markers IS 'Pytest markers like @pytest.mark.slow, @pytest.mark.auth';
