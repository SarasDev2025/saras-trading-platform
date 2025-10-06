--
-- Smallcase Tables - Smallcases, Constituents, Investments, Execution
--
-- This file is part of the organized schema structure
-- Generated from full_schema.sql
--

--
-- Table: smallcases (PARENT TABLE - no dependencies within this file)
--

CREATE TABLE public.smallcases (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    category character varying(50) NOT NULL,
    theme character varying(100),
    risk_level character varying(20) DEFAULT 'medium'::character varying,
    expected_return_min numeric(5,2),
    expected_return_max numeric(5,2),
    minimum_investment numeric(15,2) DEFAULT 1000.00,
    is_active boolean DEFAULT true,
    created_by uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    strategy_type character varying(100) DEFAULT 'VALUE'::character varying,
    expected_return_1y numeric(6,2),
    expected_return_3y numeric(6,2),
    expected_return_5y numeric(6,2),
    volatility numeric(6,2),
    sharpe_ratio numeric(6,3),
    max_drawdown numeric(6,2),
    expense_ratio numeric(5,3),
    region character varying(5) DEFAULT 'IN'::character varying,
    supported_brokers text[] DEFAULT ARRAY['zerodha'::text],
    currency character varying(3) DEFAULT 'INR'::character varying,
    CONSTRAINT check_smallcases_currency CHECK (((currency)::text = ANY ((ARRAY['USD'::character varying, 'INR'::character varying])::text[]))),
    CONSTRAINT check_smallcases_region CHECK (((region)::text = ANY ((ARRAY['US'::character varying, 'IN'::character varying])::text[]))),
    CONSTRAINT smallcases_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[])))
);


--
-- Constraints for smallcases
--

ALTER TABLE ONLY public.smallcases
    ADD CONSTRAINT smallcases_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.smallcases
    ADD CONSTRAINT smallcases_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Table: smallcase_constituents (depends on smallcases)
--

CREATE TABLE public.smallcase_constituents (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    smallcase_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    weight_percentage numeric(5,2) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    rationale text,
    CONSTRAINT smallcase_constituents_weight_percentage_check CHECK (((weight_percentage > (0)::numeric) AND (weight_percentage <= (100)::numeric)))
);


--
-- Constraints for smallcase_constituents
--

ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_smallcase_id_asset_id_key UNIQUE (smallcase_id, asset_id);


ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id) ON DELETE CASCADE;


--
-- Table: smallcase_performance (depends on smallcases)
--

CREATE TABLE public.smallcase_performance (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    smallcase_id uuid,
    date date NOT NULL,
    nav numeric(15,4) NOT NULL,
    total_return_1d numeric(8,4),
    total_return_1w numeric(8,4),
    total_return_1m numeric(8,4),
    total_return_3m numeric(8,4),
    total_return_6m numeric(8,4),
    total_return_1y numeric(8,4),
    total_return_3y numeric(8,4),
    benchmark_return_1d numeric(8,4),
    benchmark_return_1y numeric(8,4),
    alpha numeric(8,4),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Constraints for smallcase_performance
--

ALTER TABLE ONLY public.smallcase_performance
    ADD CONSTRAINT smallcase_performance_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.smallcase_performance
    ADD CONSTRAINT smallcase_performance_smallcase_id_date_key UNIQUE (smallcase_id, date);


ALTER TABLE ONLY public.smallcase_performance
    ADD CONSTRAINT smallcase_performance_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id);


--
-- Table: user_smallcase_investments (depends on smallcases)
--

CREATE TABLE public.user_smallcase_investments (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    smallcase_id uuid NOT NULL,
    investment_amount numeric(15,2) NOT NULL,
    units_purchased numeric(15,8) NOT NULL,
    purchase_price numeric(15,8) NOT NULL,
    current_value numeric(15,2),
    unrealized_pnl numeric(15,2),
    status character varying(20) DEFAULT 'active'::character varying,
    invested_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    execution_mode character varying(10) DEFAULT 'paper'::character varying,
    broker_connection_id uuid,
    auto_rebalance boolean DEFAULT false,
    last_rebalanced_at timestamp with time zone,
    closed_at timestamp with time zone,
    exit_price numeric(15,8),
    exit_value numeric(15,2),
    realized_pnl numeric(15,2),
    closure_reason character varying(50),
    CONSTRAINT user_smallcase_investments_closure_reason_check CHECK (((((status)::text = 'active'::text) AND (closure_reason IS NULL)) OR (((status)::text = ANY ((ARRAY['sold'::character varying, 'partial'::character varying])::text[])) AND (closure_reason IS NOT NULL)))),
    CONSTRAINT user_smallcase_investments_execution_mode_check CHECK (((execution_mode)::text = ANY ((ARRAY['paper'::character varying, 'live'::character varying])::text[]))),
    CONSTRAINT user_smallcase_investments_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'sold'::character varying, 'partial'::character varying])::text[])))
);


--
-- Constraints for user_smallcase_investments
--

ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE SET NULL;


ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: smallcase_execution_runs (depends on user_smallcase_investments)
--

CREATE TABLE public.smallcase_execution_runs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    investment_id uuid,
    broker_connection_id uuid,
    execution_mode character varying(10) DEFAULT 'paper'::character varying NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    total_orders integer DEFAULT 0,
    completed_orders integer DEFAULT 0,
    summary jsonb,
    error_message text,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT smallcase_execution_runs_execution_mode_check CHECK (((execution_mode)::text = ANY ((ARRAY['paper'::character varying, 'live'::character varying])::text[]))),
    CONSTRAINT smallcase_execution_runs_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'submitted'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);


--
-- Constraints for smallcase_execution_runs
--

ALTER TABLE ONLY public.smallcase_execution_runs
    ADD CONSTRAINT smallcase_execution_runs_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.smallcase_execution_runs
    ADD CONSTRAINT smallcase_execution_runs_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE SET NULL;


ALTER TABLE ONLY public.smallcase_execution_runs
    ADD CONSTRAINT smallcase_execution_runs_investment_id_fkey FOREIGN KEY (investment_id) REFERENCES public.user_smallcase_investments(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.smallcase_execution_runs
    ADD CONSTRAINT smallcase_execution_runs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: smallcase_execution_orders (depends on smallcase_execution_runs)
--

CREATE TABLE public.smallcase_execution_orders (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    execution_run_id uuid,
    asset_id uuid,
    symbol character varying(50),
    action character varying(20),
    current_weight numeric(7,3),
    suggested_weight numeric(7,3),
    weight_change numeric(7,3),
    status character varying(20) DEFAULT 'pending'::character varying,
    broker_order_id character varying(255),
    details jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT smallcase_execution_orders_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'submitted'::character varying, 'completed'::character varying, 'failed'::character varying, 'simulated'::character varying])::text[])))
);


--
-- Constraints for smallcase_execution_orders
--

ALTER TABLE ONLY public.smallcase_execution_orders
    ADD CONSTRAINT smallcase_execution_orders_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.smallcase_execution_orders
    ADD CONSTRAINT smallcase_execution_orders_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


ALTER TABLE ONLY public.smallcase_execution_orders
    ADD CONSTRAINT smallcase_execution_orders_execution_run_id_fkey FOREIGN KEY (execution_run_id) REFERENCES public.smallcase_execution_runs(id) ON DELETE CASCADE;


--
-- Table: user_smallcase_position_history (depends on smallcases)
--

CREATE TABLE public.user_smallcase_position_history (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    smallcase_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    investment_amount numeric(15,2) NOT NULL,
    units_purchased numeric(15,8) NOT NULL,
    purchase_price numeric(15,8) NOT NULL,
    exit_value numeric(15,2) NOT NULL,
    exit_price numeric(15,8) NOT NULL,
    realized_pnl numeric(15,2) NOT NULL,
    holding_period_days integer NOT NULL,
    roi_percentage numeric(8,4) NOT NULL,
    invested_at timestamp with time zone NOT NULL,
    closed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closure_reason character varying(50),
    execution_mode character varying(10) NOT NULL,
    broker_connection_id uuid,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_smallcase_position_history_execution_mode_check CHECK (((execution_mode)::text = ANY ((ARRAY['paper'::character varying, 'live'::character varying])::text[])))
);


--
-- Constraints for user_smallcase_position_history
--

ALTER TABLE ONLY public.user_smallcase_position_history
    ADD CONSTRAINT user_smallcase_position_history_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_smallcase_position_history
    ADD CONSTRAINT user_smallcase_position_history_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE SET NULL;


ALTER TABLE ONLY public.user_smallcase_position_history
    ADD CONSTRAINT user_smallcase_position_history_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id);


ALTER TABLE ONLY public.user_smallcase_position_history
    ADD CONSTRAINT user_smallcase_position_history_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id);


ALTER TABLE ONLY public.user_smallcase_position_history
    ADD CONSTRAINT user_smallcase_position_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


