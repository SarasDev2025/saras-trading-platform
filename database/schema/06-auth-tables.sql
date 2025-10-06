--
-- Authentication & Security Tables - Sessions, Tokens, Logs, Security
--
-- This file is part of the organized schema structure
-- Generated from full_schema.sql
--

--
-- Table: audit_logs
--

CREATE TABLE public.audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_type character varying(50) NOT NULL,
    request_id uuid,
    "timestamp" timestamp with time zone NOT NULL,
    client_ip inet,
    user_agent text,
    path character varying(500),
    method character varying(10),
    user_id uuid,
    status_code integer,
    processing_time_ms numeric(10,2),
    success boolean DEFAULT true,
    error_message text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for audit_logs
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Table: login_attempts
--

CREATE TABLE public.login_attempts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255),
    client_ip inet NOT NULL,
    user_agent text,
    success boolean NOT NULL,
    failure_reason character varying(100),
    attempted_at timestamp with time zone DEFAULT now(),
    user_id uuid
);


--
-- Constraints for login_attempts
--

ALTER TABLE ONLY public.login_attempts
    ADD CONSTRAINT login_attempts_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.login_attempts
    ADD CONSTRAINT login_attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Table: rate_limit_violations
--

CREATE TABLE public.rate_limit_violations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_ip inet NOT NULL,
    user_id uuid,
    endpoint character varying(500),
    request_count integer NOT NULL,
    time_window_minutes integer NOT NULL,
    blocked_until timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for rate_limit_violations
--

ALTER TABLE ONLY public.rate_limit_violations
    ADD CONSTRAINT rate_limit_violations_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.rate_limit_violations
    ADD CONSTRAINT rate_limit_violations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Table: refresh_tokens
--

CREATE TABLE public.refresh_tokens (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    token_hash character varying(255) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    is_revoked boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_used timestamp with time zone,
    device_info jsonb
);


--
-- Constraints for refresh_tokens
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: security_logs
--

CREATE TABLE public.security_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_type character varying(50) NOT NULL,
    user_id uuid,
    "timestamp" timestamp with time zone NOT NULL,
    client_ip inet,
    user_agent text,
    token_present boolean DEFAULT false,
    details text,
    severity character varying(20) DEFAULT 'INFO'::character varying,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for security_logs
--

ALTER TABLE ONLY public.security_logs
    ADD CONSTRAINT security_logs_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.security_logs
    ADD CONSTRAINT security_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Table: suspicious_activities
--

CREATE TABLE public.suspicious_activities (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    activity_type character varying(50) NOT NULL,
    client_ip inet,
    user_agent text,
    details text,
    risk_score integer DEFAULT 0,
    investigated boolean DEFAULT false,
    resolved boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for suspicious_activities
--

ALTER TABLE ONLY public.suspicious_activities
    ADD CONSTRAINT suspicious_activities_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.suspicious_activities
    ADD CONSTRAINT suspicious_activities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Table: token_blacklist
--

CREATE TABLE public.token_blacklist (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    token_hash character varying(64) NOT NULL,
    user_id uuid,
    reason character varying(100),
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for token_blacklist
--

ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT token_blacklist_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT token_blacklist_token_hash_key UNIQUE (token_hash);


ALTER TABLE ONLY public.token_blacklist
    ADD CONSTRAINT token_blacklist_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: token_validations
--

CREATE TABLE public.token_validations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    result character varying(50) NOT NULL,
    validation_time_ms numeric(10,2),
    client_ip inet,
    user_agent text,
    error_details text,
    token_age_seconds integer,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for token_validations
--

ALTER TABLE ONLY public.token_validations
    ADD CONSTRAINT token_validations_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.token_validations
    ADD CONSTRAINT token_validations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Table: user_sessions
--

CREATE TABLE public.user_sessions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    session_token character varying(255) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address inet,
    user_agent text
);


--
-- Constraints for user_sessions
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_session_token_key UNIQUE (session_token);


ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


