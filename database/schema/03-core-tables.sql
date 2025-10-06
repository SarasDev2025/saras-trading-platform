--
-- Core Tables - Users, Portfolios, Assets, Price History, Virtual Money
--
-- This file is part of the organized schema structure
-- Generated from full_schema.sql
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';
SET default_table_access_method = heap;

--
-- Table: users
--

CREATE TABLE public.users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    phone character varying(20),
    date_of_birth date,
    profile_image_url text,
    email_verified boolean DEFAULT false,
    phone_verified boolean DEFAULT false,
    kyc_status character varying(20) DEFAULT 'pending'::character varying,
    account_status character varying(20) DEFAULT 'active'::character varying,
    region character varying(5) DEFAULT 'IN'::character varying NOT NULL,
    trading_mode character varying(10) DEFAULT 'paper'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp with time zone,
    failed_login_attempts integer DEFAULT 0,
    locked_until timestamp with time zone,
    email_verification_token character varying(255),
    email_verification_expires timestamp with time zone,
    password_reset_token character varying(255),
    password_reset_expires timestamp with time zone,
    CONSTRAINT users_account_status_check CHECK (((account_status)::text = ANY ((ARRAY['active'::character varying, 'suspended'::character varying, 'closed'::character varying])::text[]))),
    CONSTRAINT users_kyc_status_check CHECK (((kyc_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[]))),
    CONSTRAINT users_region_check CHECK (((region)::text = ANY ((ARRAY['IN'::character varying, 'US'::character varying, 'GB'::character varying])::text[]))),
    CONSTRAINT users_trading_mode_check CHECK (((trading_mode)::text = ANY ((ARRAY['paper'::character varying, 'live'::character varying])::text[])))
);


--
-- Constraints for users
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Table: assets
--

CREATE TABLE public.assets (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    symbol character varying(20) NOT NULL,
    name character varying(200) NOT NULL,
    asset_type character varying(20) NOT NULL,
    exchange character varying(50),
    currency character varying(3) DEFAULT 'USD'::character varying,
    current_price numeric(15,8),
    price_updated_at timestamp with time zone,
    is_active boolean DEFAULT true,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    pb_ratio numeric(8,2),
    dividend_yield numeric(5,2),
    beta numeric(6,3),
    industry character varying(150),
    region character varying(5) DEFAULT 'IN'::character varying,
    market_cap bigint,
    sector character varying(100),
    CONSTRAINT assets_asset_type_check CHECK (((asset_type)::text = ANY ((ARRAY['stock'::character varying, 'crypto'::character varying, 'forex'::character varying, 'commodity'::character varying, 'bond'::character varying])::text[]))),
    CONSTRAINT check_assets_currency CHECK (((currency)::text = ANY ((ARRAY['USD'::character varying, 'INR'::character varying])::text[]))),
    CONSTRAINT check_assets_region CHECK (((region)::text = ANY ((ARRAY['US'::character varying, 'IN'::character varying])::text[])))
);


--
-- Constraints for assets
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_symbol_key UNIQUE (symbol);


--
-- Table: portfolios
--

CREATE TABLE public.portfolios (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(100) DEFAULT 'Default Portfolio'::character varying NOT NULL,
    description text,
    total_value numeric(15,2) DEFAULT 0.00,
    cash_balance numeric(15,2) DEFAULT 0.00,
    currency character varying(3) DEFAULT 'USD'::character varying,
    is_default boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Constraints for portfolios
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: price_history
--

CREATE TABLE public.price_history (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    asset_id uuid NOT NULL,
    price numeric(15,8) NOT NULL,
    volume numeric(20,4),
    market_cap numeric(20,2),
    "timestamp" timestamp with time zone NOT NULL,
    interval_type character varying(10) DEFAULT '1d'::character varying,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT price_history_interval_type_check CHECK (((interval_type)::text = ANY ((ARRAY['1m'::character varying, '5m'::character varying, '15m'::character varying, '1h'::character varying, '4h'::character varying, '1d'::character varying, '1w'::character varying])::text[])))
);


--
-- Constraints for price_history
--

ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Table: virtual_money_config
--

CREATE TABLE public.virtual_money_config (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    initial_allocation numeric(15,2) DEFAULT 100000.00,
    max_top_up numeric(15,2) DEFAULT 1000000.00,
    total_added numeric(15,2) DEFAULT 0.00,
    allow_reset boolean DEFAULT true,
    last_reset_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Constraints for virtual_money_config
--

ALTER TABLE ONLY public.virtual_money_config
    ADD CONSTRAINT virtual_money_config_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.virtual_money_config
    ADD CONSTRAINT virtual_money_config_user_id_key UNIQUE (user_id);


ALTER TABLE ONLY public.virtual_money_config
    ADD CONSTRAINT virtual_money_config_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


