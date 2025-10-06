--
-- Dividend Management Tables - Declarations, Payments, DRIP
--
-- This file is part of the organized schema structure
-- Generated from full_schema.sql
--

--
-- Table: dividend_bulk_orders
--

CREATE TABLE public.dividend_bulk_orders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    asset_id uuid NOT NULL,
    execution_date date NOT NULL,
    total_amount numeric(15,4) NOT NULL,
    total_shares_to_purchase numeric(15,4) NOT NULL,
    target_price numeric(15,4),
    actual_price numeric(15,4),
    broker_name character varying(50) NOT NULL,
    broker_order_id character varying(100),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    execution_window_start timestamp with time zone,
    execution_window_end timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    error_message text
);


--
-- Constraints for dividend_bulk_orders
--

ALTER TABLE ONLY public.dividend_bulk_orders
    ADD CONSTRAINT dividend_bulk_orders_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.dividend_bulk_orders
    ADD CONSTRAINT dividend_bulk_orders_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Table: dividend_declarations
--

CREATE TABLE public.dividend_declarations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    asset_id uuid NOT NULL,
    ex_dividend_date date NOT NULL,
    record_date date NOT NULL,
    payment_date date NOT NULL,
    dividend_amount numeric(15,4) NOT NULL,
    dividend_type character varying(20) DEFAULT 'cash'::character varying NOT NULL,
    currency character varying(3) DEFAULT 'USD'::character varying NOT NULL,
    announcement_date date,
    status character varying(20) DEFAULT 'announced'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for dividend_declarations
--

ALTER TABLE ONLY public.dividend_declarations
    ADD CONSTRAINT dividend_declarations_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.dividend_declarations
    ADD CONSTRAINT unique_dividend_per_asset_ex_date UNIQUE (asset_id, ex_dividend_date);


ALTER TABLE ONLY public.dividend_declarations
    ADD CONSTRAINT dividend_declarations_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Table: drip_bulk_order_allocations
--

CREATE TABLE public.drip_bulk_order_allocations (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    drip_transaction_id uuid NOT NULL,
    dividend_bulk_order_id uuid NOT NULL,
    allocated_amount numeric(15,4) NOT NULL,
    allocated_shares numeric(15,4) NOT NULL,
    allocation_percentage numeric(8,4) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for drip_bulk_order_allocations
--

ALTER TABLE ONLY public.drip_bulk_order_allocations
    ADD CONSTRAINT drip_bulk_order_allocations_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.drip_bulk_order_allocations
    ADD CONSTRAINT unique_drip_bulk_allocation UNIQUE (drip_transaction_id, dividend_bulk_order_id);


ALTER TABLE ONLY public.drip_bulk_order_allocations
    ADD CONSTRAINT drip_bulk_order_allocations_dividend_bulk_order_id_fkey FOREIGN KEY (dividend_bulk_order_id) REFERENCES public.dividend_bulk_orders(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.drip_bulk_order_allocations
    ADD CONSTRAINT drip_bulk_order_allocations_drip_transaction_id_fkey FOREIGN KEY (drip_transaction_id) REFERENCES public.drip_transactions(id) ON DELETE CASCADE;


--
-- Table: drip_transactions
--

CREATE TABLE public.drip_transactions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_dividend_payment_id uuid NOT NULL,
    user_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    reinvestment_amount numeric(15,4) NOT NULL,
    shares_purchased numeric(15,4) NOT NULL,
    purchase_price numeric(15,4) NOT NULL,
    transaction_date date NOT NULL,
    broker_name character varying(50) NOT NULL,
    broker_transaction_id character varying(100),
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    error_message text
);


--
-- Constraints for drip_transactions
--

ALTER TABLE ONLY public.drip_transactions
    ADD CONSTRAINT drip_transactions_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.drip_transactions
    ADD CONSTRAINT drip_transactions_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.drip_transactions
    ADD CONSTRAINT drip_transactions_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.drip_transactions
    ADD CONSTRAINT drip_transactions_user_dividend_payment_id_fkey FOREIGN KEY (user_dividend_payment_id) REFERENCES public.user_dividend_payments(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.drip_transactions
    ADD CONSTRAINT drip_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: user_dividend_payments
--

CREATE TABLE public.user_dividend_payments (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    dividend_declaration_id uuid NOT NULL,
    position_snapshot_id uuid,
    eligible_shares numeric(15,4) NOT NULL,
    dividend_per_share numeric(15,4) NOT NULL,
    gross_amount numeric(15,4) NOT NULL,
    tax_withheld numeric(15,4) DEFAULT 0,
    net_amount numeric(15,4) NOT NULL,
    payment_date date NOT NULL,
    broker_name character varying(50) NOT NULL,
    reinvestment_preference character varying(20) DEFAULT 'cash'::character varying,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for user_dividend_payments
--

ALTER TABLE ONLY public.user_dividend_payments
    ADD CONSTRAINT user_dividend_payments_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_dividend_payments
    ADD CONSTRAINT user_dividend_payments_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_dividend_payments
    ADD CONSTRAINT user_dividend_payments_dividend_declaration_id_fkey FOREIGN KEY (dividend_declaration_id) REFERENCES public.dividend_declarations(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_dividend_payments
    ADD CONSTRAINT user_dividend_payments_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_dividend_payments
    ADD CONSTRAINT user_dividend_payments_position_snapshot_id_fkey FOREIGN KEY (position_snapshot_id) REFERENCES public.user_position_snapshots(id) ON DELETE SET NULL;


ALTER TABLE ONLY public.user_dividend_payments
    ADD CONSTRAINT user_dividend_payments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: user_drip_preferences
--

CREATE TABLE public.user_drip_preferences (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    asset_id uuid,
    is_enabled boolean DEFAULT false NOT NULL,
    minimum_amount numeric(15,4) DEFAULT 0,
    maximum_percentage numeric(5,2) DEFAULT 100.00,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for user_drip_preferences
--

ALTER TABLE ONLY public.user_drip_preferences
    ADD CONSTRAINT unique_user_drip_pref UNIQUE (user_id, asset_id);


ALTER TABLE ONLY public.user_drip_preferences
    ADD CONSTRAINT user_drip_preferences_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_drip_preferences
    ADD CONSTRAINT user_drip_preferences_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_drip_preferences
    ADD CONSTRAINT user_drip_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: user_position_snapshots
--

CREATE TABLE public.user_position_snapshots (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    snapshot_date date NOT NULL,
    quantity numeric(15,4) NOT NULL,
    average_cost numeric(15,4) NOT NULL,
    market_value numeric(15,4) NOT NULL,
    broker_name character varying(50) NOT NULL,
    dividend_declaration_id uuid,
    is_eligible boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Constraints for user_position_snapshots
--

ALTER TABLE ONLY public.user_position_snapshots
    ADD CONSTRAINT unique_position_snapshot UNIQUE (user_id, asset_id, snapshot_date, dividend_declaration_id);


ALTER TABLE ONLY public.user_position_snapshots
    ADD CONSTRAINT user_position_snapshots_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_position_snapshots
    ADD CONSTRAINT user_position_snapshots_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_position_snapshots
    ADD CONSTRAINT user_position_snapshots_dividend_declaration_id_fkey FOREIGN KEY (dividend_declaration_id) REFERENCES public.dividend_declarations(id) ON DELETE SET NULL;


ALTER TABLE ONLY public.user_position_snapshots
    ADD CONSTRAINT user_position_snapshots_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.user_position_snapshots
    ADD CONSTRAINT user_position_snapshots_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


