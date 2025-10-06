--
-- Trading Tables - Transactions, Holdings, Paper Trading
--
-- This file is part of the organized schema structure
-- Generated from full_schema.sql
--

--
-- Table: basket_orders
--

CREATE TABLE public.basket_orders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    broker_connection_id uuid NOT NULL,
    basket_id character varying(100) NOT NULL,
    orders_placed integer NOT NULL,
    success_count integer DEFAULT 0,
    failure_count integer DEFAULT 0,
    status character varying(20) DEFAULT 'pending'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    basket_details jsonb,
    is_active boolean DEFAULT true,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT basket_orders_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'completed'::character varying, 'partial'::character varying, 'failed'::character varying])::text[])))
);


--
-- Constraints for basket_orders
--

ALTER TABLE ONLY public.basket_orders
    ADD CONSTRAINT basket_orders_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.basket_orders
    ADD CONSTRAINT basket_orders_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE CASCADE;


--
-- Table: oco_orders
--

CREATE TABLE public.oco_orders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    broker_connection_id uuid NOT NULL,
    trigger_id character varying(100) NOT NULL,
    symbol character varying(20) NOT NULL,
    exchange character varying(10) NOT NULL,
    side character varying(4) NOT NULL,
    quantity numeric(15,4) NOT NULL,
    target_price numeric(15,4) NOT NULL,
    stop_loss_price numeric(15,4) NOT NULL,
    product character varying(10) DEFAULT 'CNC'::character varying,
    status character varying(20) DEFAULT 'active'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    triggered_at timestamp with time zone,
    expires_at timestamp with time zone,
    executed_price numeric(15,4),
    executed_side character varying(20),
    order_id character varying(100),
    execution_details jsonb,
    is_active boolean DEFAULT true,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT oco_orders_side_check CHECK (((side)::text = ANY ((ARRAY['BUY'::character varying, 'SELL'::character varying])::text[]))),
    CONSTRAINT oco_orders_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'target_hit'::character varying, 'stop_hit'::character varying, 'cancelled'::character varying, 'expired'::character varying])::text[])))
);


--
-- Constraints for oco_orders
--

ALTER TABLE ONLY public.oco_orders
    ADD CONSTRAINT oco_orders_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.oco_orders
    ADD CONSTRAINT oco_orders_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE CASCADE;


--
-- Table: paper_orders
--

CREATE TABLE public.paper_orders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    broker_connection_id uuid NOT NULL,
    order_id character varying(100) NOT NULL,
    symbol character varying(20) NOT NULL,
    side character varying(10) NOT NULL,
    order_type character varying(20) NOT NULL,
    quantity numeric(15,4) NOT NULL,
    price numeric(15,2),
    status character varying(20) DEFAULT 'pending'::character varying,
    filled_quantity numeric(15,4) DEFAULT 0,
    average_fill_price numeric(15,2),
    broker_type character varying(50) NOT NULL,
    is_paper_trading boolean DEFAULT true,
    order_response jsonb,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    filled_at timestamp without time zone,
    CONSTRAINT paper_orders_quantity_check CHECK ((quantity > (0)::numeric)),
    CONSTRAINT paper_orders_side_check CHECK (((side)::text = ANY ((ARRAY['BUY'::character varying, 'SELL'::character varying])::text[]))),
    CONSTRAINT paper_orders_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'filled'::character varying, 'partial'::character varying, 'cancelled'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Constraints for paper_orders
--

ALTER TABLE ONLY public.paper_orders
    ADD CONSTRAINT paper_orders_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.paper_orders
    ADD CONSTRAINT paper_orders_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.paper_orders
    ADD CONSTRAINT paper_orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: paper_trading_stats
--

CREATE TABLE public.paper_trading_stats (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    total_trades integer DEFAULT 0,
    winning_trades integer DEFAULT 0,
    losing_trades integer DEFAULT 0,
    total_pnl numeric(15,2) DEFAULT 0.00,
    best_trade numeric(15,2) DEFAULT 0.00,
    worst_trade numeric(15,2) DEFAULT 0.00,
    current_streak integer DEFAULT 0,
    max_drawdown numeric(15,2) DEFAULT 0.00,
    total_fees numeric(15,2) DEFAULT 0.00,
    updated_at timestamp without time zone DEFAULT now()
);


--
-- Constraints for paper_trading_stats
--

ALTER TABLE ONLY public.paper_trading_stats
    ADD CONSTRAINT paper_trading_stats_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.paper_trading_stats
    ADD CONSTRAINT paper_trading_stats_user_id_key UNIQUE (user_id);


ALTER TABLE ONLY public.paper_trading_stats
    ADD CONSTRAINT paper_trading_stats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: portfolio_holdings
--

CREATE TABLE public.portfolio_holdings (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    portfolio_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    quantity numeric(18,8) DEFAULT 0 NOT NULL,
    average_cost numeric(15,8) DEFAULT 0 NOT NULL,
    total_cost numeric(15,2) DEFAULT 0 NOT NULL,
    current_value numeric(15,2) DEFAULT 0,
    unrealized_pnl numeric(15,2) DEFAULT 0,
    realized_pnl numeric(15,2) DEFAULT 0,
    last_updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Constraints for portfolio_holdings
--

ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_portfolio_id_asset_id_key UNIQUE (portfolio_id, asset_id);


ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


--
-- Table: trading_transactions
--

CREATE TABLE public.trading_transactions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    asset_id uuid,
    transaction_type character varying(10) NOT NULL,
    quantity numeric(18,8),
    price_per_unit numeric(15,8),
    total_amount numeric(15,2) NOT NULL,
    fees numeric(10,2) DEFAULT 0.00,
    net_amount numeric(15,2) NOT NULL,
    transaction_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    settlement_date timestamp with time zone,
    status character varying(20) DEFAULT 'pending'::character varying,
    order_type character varying(20) DEFAULT 'market'::character varying,
    notes text,
    external_transaction_id character varying(255),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    cash_impact numeric(15,2) DEFAULT 0.00,
    cash_balance_after numeric(15,2),
    CONSTRAINT trading_transactions_order_type_check CHECK (((order_type)::text = ANY ((ARRAY['market'::character varying, 'limit'::character varying, 'stop'::character varying, 'stop_limit'::character varying])::text[]))),
    CONSTRAINT trading_transactions_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'executed'::character varying, 'cancelled'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT trading_transactions_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['buy'::character varying, 'sell'::character varying, 'close_position'::character varying, 'partial_close'::character varying, 'deposit'::character varying, 'withdrawal'::character varying])::text[])))
);


--
-- Constraints for trading_transactions
--

ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


