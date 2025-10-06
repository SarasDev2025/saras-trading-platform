--
-- Broker Integration Tables - Connections, GTT Orders
--
-- This file is part of the organized schema structure
-- Generated from full_schema.sql
--

--
-- Table: user_broker_connections
--

CREATE TABLE public.user_broker_connections (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid,
    broker_type character varying(50) NOT NULL,
    alias character varying(50) NOT NULL,
    api_key text,
    api_secret text,
    credentials jsonb,
    paper_trading boolean DEFAULT true,
    status character varying(20) DEFAULT 'active'::character varying,
    connection_metadata jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Constraints for user_broker_connections
--

ALTER TABLE ONLY public.user_broker_connections
    ADD CONSTRAINT user_broker_connections_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.user_broker_connections
    ADD CONSTRAINT user_broker_connections_user_id_alias_key UNIQUE (user_id, alias);


ALTER TABLE ONLY public.user_broker_connections
    ADD CONSTRAINT user_broker_connections_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Table: gtt_orders
--

CREATE TABLE public.gtt_orders (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    broker_connection_id uuid NOT NULL,
    trigger_id character varying(100) NOT NULL,
    symbol character varying(20) NOT NULL,
    exchange character varying(10) NOT NULL,
    side character varying(4) NOT NULL,
    quantity numeric(15,4) NOT NULL,
    trigger_price numeric(15,4) NOT NULL,
    limit_price numeric(15,4),
    trigger_type character varying(20) DEFAULT 'single'::character varying,
    product character varying(10) DEFAULT 'CNC'::character varying,
    status character varying(20) DEFAULT 'active'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    triggered_at timestamp with time zone,
    expires_at timestamp with time zone,
    order_id character varying(100),
    execution_details jsonb,
    is_active boolean DEFAULT true,
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT gtt_orders_product_check CHECK (((product)::text = ANY ((ARRAY['CNC'::character varying, 'MIS'::character varying, 'NRML'::character varying, 'CO'::character varying, 'BO'::character varying])::text[]))),
    CONSTRAINT gtt_orders_side_check CHECK (((side)::text = ANY ((ARRAY['BUY'::character varying, 'SELL'::character varying])::text[]))),
    CONSTRAINT gtt_orders_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'triggered'::character varying, 'cancelled'::character varying, 'expired'::character varying])::text[]))),
    CONSTRAINT gtt_orders_trigger_type_check CHECK (((trigger_type)::text = ANY ((ARRAY['single'::character varying, 'two-leg'::character varying])::text[])))
);


--
-- Constraints for gtt_orders
--

ALTER TABLE ONLY public.gtt_orders
    ADD CONSTRAINT gtt_orders_pkey PRIMARY KEY (id);


ALTER TABLE ONLY public.gtt_orders
    ADD CONSTRAINT gtt_orders_broker_connection_id_fkey FOREIGN KEY (broker_connection_id) REFERENCES public.user_broker_connections(id) ON DELETE CASCADE;


