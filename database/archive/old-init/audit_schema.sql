-- =====================================================
-- Audit & Security Logging Database Schema
-- =====================================================

-- Create audit_logs table for general request tracking
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    request_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    client_ip INET,
    user_agent TEXT,
    path VARCHAR(500),
    method VARCHAR(10),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status_code INTEGER,
    processing_time_ms NUMERIC(10,2),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_client_ip ON audit_logs(client_ip);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_path ON audit_logs(path);
CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs(request_id);

-- Create security_logs table for security-specific events
CREATE TABLE IF NOT EXISTS security_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- LOGIN_SUCCESS, LOGIN_FAILURE, INVALID_TOKEN, etc.
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    client_ip INET,
    user_agent TEXT,
    token_present BOOLEAN DEFAULT false,
    details TEXT,
    severity VARCHAR(20) DEFAULT 'INFO', -- INFO, WARNING, CRITICAL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for security_logs
CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_logs_client_ip ON security_logs(client_ip);
CREATE INDEX IF NOT EXISTS idx_security_logs_severity ON security_logs(severity);

-- Create token_validations table for detailed token tracking
CREATE TABLE IF NOT EXISTS token_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    result VARCHAR(50) NOT NULL, -- SUCCESS, JWT_ERROR, VALIDATION_ERROR, etc.
    validation_time_ms NUMERIC(10,2),
    client_ip INET,
    user_agent TEXT,
    error_details TEXT,
    token_age_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for token_validations
CREATE INDEX IF NOT EXISTS idx_token_validations_user_id ON token_validations(user_id);
CREATE INDEX IF NOT EXISTS idx_token_validations_result ON token_validations(result);
CREATE INDEX IF NOT EXISTS idx_token_validations_created_at ON token_validations(created_at);
CREATE INDEX IF NOT EXISTS idx_token_validations_client_ip ON token_validations(client_ip);

-- Create token_blacklist table for revoked tokens
CREATE TABLE IF NOT EXISTS token_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA256 hash of the token
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    reason VARCHAR(100), -- LOGOUT, SECURITY_BREACH, EXPIRED, etc.
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for token_blacklist
CREATE INDEX IF NOT EXISTS idx_token_blacklist_token_hash ON token_blacklist(token_hash);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires_at ON token_blacklist(expires_at);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_user_id ON token_blacklist(user_id);

-- Create suspicious_activities table for security monitoring
CREATE TABLE IF NOT EXISTS suspicious_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    activity_type VARCHAR(50) NOT NULL, -- RAPID_REQUESTS, MULTIPLE_IPS, UNUSUAL_PATTERN, etc.
    client_ip INET,
    user_agent TEXT,
    details TEXT,
    risk_score INTEGER DEFAULT 0, -- 0-100 risk score
    investigated BOOLEAN DEFAULT false,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for suspicious_activities
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_user_id ON suspicious_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_activity_type ON suspicious_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_created_at ON suspicious_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_risk_score ON suspicious_activities(risk_score);
CREATE INDEX IF NOT EXISTS idx_suspicious_activities_investigated ON suspicious_activities(investigated);

-- Create user_sessions table for session tracking
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL, -- Refresh token hash
    device_info JSONB,
    client_ip INET,
    user_agent TEXT,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);

-- Create login_attempts table for brute force protection
CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255),
    client_ip INET NOT NULL,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100),
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for login_attempts
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_client_ip ON login_attempts(client_ip);
CREATE INDEX IF NOT EXISTS idx_login_attempts_attempted_at ON login_attempts(attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_success ON login_attempts(success);
CREATE INDEX IF NOT EXISTS idx_login_attempts_user_id ON login_attempts(user_id);

-- Create rate_limit_violations table
CREATE TABLE IF NOT EXISTS rate_limit_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_ip INET NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    endpoint VARCHAR(500),
    request_count INTEGER NOT NULL,
    time_window_minutes INTEGER NOT NULL,
    blocked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for rate_limit_violations
CREATE INDEX IF NOT EXISTS idx_rate_limit_violations_client_ip ON rate_limit_violations(client_ip);
CREATE INDEX IF NOT EXISTS idx_rate_limit_violations_user_id ON rate_limit_violations(user_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_violations_created_at ON rate_limit_violations(created_at);
CREATE INDEX IF NOT EXISTS idx_rate_limit_violations_blocked_until ON rate_limit_violations(blocked_until);

-- Add audit columns to existing user table (if not already present)
DO $$ 
BEGIN
    -- Add last_login_ip if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'last_login_ip') THEN
        ALTER TABLE users ADD COLUMN last_login_ip INET;
    END IF;
    
    -- Add last_login_user_agent if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'last_login_user_agent') THEN
        ALTER TABLE users ADD COLUMN last_login_user_agent TEXT;
    END IF;
    
    -- Add password_changed_at if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'password_changed_at') THEN
        ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
    
    -- Add security_flags if not exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'users' AND column_name = 'security_flags') THEN
        ALTER TABLE users ADD COLUMN security_flags JSONB DEFAULT '{}';
    END IF;
END $;

-- Create materialized view for security dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS security_summary AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(CASE WHEN event_type = 'LOGIN_SUCCESS' THEN 1 END) as successful_logins,
    COUNT(CASE WHEN event_type = 'LOGIN_FAILURE' THEN 1 END) as failed_logins,
    COUNT(CASE WHEN event_type = 'INVALID_TOKEN' THEN 1 END) as invalid_tokens,
    COUNT(DISTINCT client_ip) as unique_ips,
    COUNT(DISTINCT user_id) as active_users
FROM security_logs 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_security_summary_date ON security_summary(date);

-- Create function to refresh security summary
CREATE OR REPLACE FUNCTION refresh_security_summary()
RETURNS void AS $
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY security_summary;
END;
$ LANGUAGE plpgsql;

-- Create function to clean old audit logs (for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old audit logs
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old token validations
    DELETE FROM token_validations 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Delete expired tokens from blacklist
    DELETE FROM token_blacklist 
    WHERE expires_at < NOW();
    
    -- Delete old login attempts
    DELETE FROM login_attempts 
    WHERE attempted_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;

-- Create function to detect suspicious patterns
CREATE OR REPLACE FUNCTION detect_suspicious_patterns()
RETURNS TABLE(user_id UUID, pattern_type TEXT, details TEXT, risk_score INTEGER) AS $
BEGIN
    -- Multiple failed logins from same IP
    RETURN QUERY
    SELECT 
        la.user_id,
        'MULTIPLE_FAILED_LOGINS' as pattern_type,
        'Multiple failed login attempts from IP: ' || la.client_ip::TEXT as details,
        30 as risk_score
    FROM login_attempts la
    WHERE la.attempted_at > NOW() - INTERVAL '1 hour'
    AND la.success = false
    GROUP BY la.user_id, la.client_ip
    HAVING COUNT(*) >= 5;
    
    -- Token used from multiple countries (simplified - multiple IPs)
    RETURN QUERY
    SELECT 
        al.user_id,
        'MULTIPLE_LOCATIONS' as pattern_type,
        'Token used from ' || COUNT(DISTINCT al.client_ip)::TEXT || ' different IPs' as details,
        50 as risk_score
    FROM audit_logs al
    WHERE al.created_at > NOW() - INTERVAL '1 hour'
    AND al.user_id IS NOT NULL
    GROUP BY al.user_id
    HAVING COUNT(DISTINCT al.client_ip) > 5;
    
    -- Rapid API requests
    RETURN QUERY
    SELECT 
        al.user_id,
        'RAPID_REQUESTS' as pattern_type,
        'Excessive API requests: ' || COUNT(*)::TEXT || ' requests in 1 minute' as details,
        25 as risk_score
    FROM audit_logs al
    WHERE al.created_at > NOW() - INTERVAL '1 minute'
    AND al.user_id IS NOT NULL
    GROUP BY al.user_id, al.client_ip
    HAVING COUNT(*) > 100;
END;
$ LANGUAGE plpgsql;

-- Create triggers for automatic security monitoring
CREATE OR REPLACE FUNCTION trigger_security_check()
RETURNS TRIGGER AS $
BEGIN
    -- Check for suspicious login patterns
    IF NEW.event_type IN ('LOGIN_FAILURE', 'INVALID_TOKEN') THEN
        -- Count recent failures from this IP
        IF (SELECT COUNT(*) FROM security_logs 
            WHERE client_ip = NEW.client_ip 
            AND event_type IN ('LOGIN_FAILURE', 'INVALID_TOKEN')
            AND created_at > NOW() - INTERVAL '15 minutes') >= 10 THEN
            
            -- Insert suspicious activity record
            INSERT INTO suspicious_activities (
                user_id, activity_type, client_ip, user_agent, details, risk_score
            ) VALUES (
                NEW.user_id, 'BRUTE_FORCE_ATTEMPT', NEW.client_ip, NEW.user_agent,
                'Multiple authentication failures detected', 75
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS security_check_trigger ON security_logs;
CREATE TRIGGER security_check_trigger
    AFTER INSERT ON security_logs
    FOR EACH ROW
    EXECUTE FUNCTION trigger_security_check();

-- Grant appropriate permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT ON audit_logs TO your_app_user;
-- GRANT SELECT, INSERT ON security_logs TO your_app_user;
-- GRANT SELECT, INSERT ON token_validations TO your_app_user;
-- GRANT SELECT, INSERT, DELETE ON token_blacklist TO your_app_user;
-- GRANT SELECT, INSERT ON suspicious_activities TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON user_sessions TO your_app_user;