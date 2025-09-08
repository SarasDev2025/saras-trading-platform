--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

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

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: trading_user
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO trading_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assets; Type: TABLE; Schema: public; Owner: trading_user
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
    CONSTRAINT assets_asset_type_check CHECK (((asset_type)::text = ANY ((ARRAY['stock'::character varying, 'crypto'::character varying, 'forex'::character varying, 'commodity'::character varying, 'bond'::character varying])::text[])))
);


ALTER TABLE public.assets OWNER TO trading_user;

--
-- Name: portfolio_holdings; Type: TABLE; Schema: public; Owner: trading_user
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
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.portfolio_holdings OWNER TO trading_user;

--
-- Name: portfolios; Type: TABLE; Schema: public; Owner: trading_user
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


ALTER TABLE public.portfolios OWNER TO trading_user;

--
-- Name: price_history; Type: TABLE; Schema: public; Owner: trading_user
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


ALTER TABLE public.price_history OWNER TO trading_user;

--
-- Name: smallcase_constituents; Type: TABLE; Schema: public; Owner: trading_user
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


ALTER TABLE public.smallcase_constituents OWNER TO trading_user;

--
-- Name: smallcase_performance; Type: TABLE; Schema: public; Owner: trading_user
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


ALTER TABLE public.smallcase_performance OWNER TO trading_user;

--
-- Name: smallcases; Type: TABLE; Schema: public; Owner: trading_user
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
    CONSTRAINT smallcases_risk_level_check CHECK (((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[])))
);


ALTER TABLE public.smallcases OWNER TO trading_user;

--
-- Name: trading_transactions; Type: TABLE; Schema: public; Owner: trading_user
--

CREATE TABLE public.trading_transactions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id uuid NOT NULL,
    portfolio_id uuid NOT NULL,
    asset_id uuid NOT NULL,
    transaction_type character varying(10) NOT NULL,
    quantity numeric(18,8) NOT NULL,
    price_per_unit numeric(15,8) NOT NULL,
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
    CONSTRAINT trading_transactions_order_type_check CHECK (((order_type)::text = ANY ((ARRAY['market'::character varying, 'limit'::character varying, 'stop'::character varying, 'stop_limit'::character varying])::text[]))),
    CONSTRAINT trading_transactions_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'executed'::character varying, 'cancelled'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT trading_transactions_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['buy'::character varying, 'sell'::character varying])::text[])))
);


ALTER TABLE public.trading_transactions OWNER TO trading_user;

--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: trading_user
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


ALTER TABLE public.user_sessions OWNER TO trading_user;

--
-- Name: user_smallcase_investments; Type: TABLE; Schema: public; Owner: trading_user
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
    CONSTRAINT user_smallcase_investments_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'sold'::character varying, 'partial'::character varying])::text[])))
);


ALTER TABLE public.user_smallcase_investments OWNER TO trading_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: trading_user
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
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp with time zone,
    CONSTRAINT users_account_status_check CHECK (((account_status)::text = ANY ((ARRAY['active'::character varying, 'suspended'::character varying, 'closed'::character varying])::text[]))),
    CONSTRAINT users_kyc_status_check CHECK (((kyc_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO trading_user;

--
-- Data for Name: assets; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.assets (id, symbol, name, asset_type, exchange, currency, current_price, price_updated_at, is_active, metadata, created_at, updated_at, pb_ratio, dividend_yield, beta, industry) FROM stdin;
e23922f7-94ce-4d18-a549-05a5790e25a7	TCS	Tata Consultancy Services	stock	NSE	INR	3650.50000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	12.40	1.80	0.850	IT Services
b76ecdf2-bb85-47c2-8f83-18366735edd1	INFY	Infosys Limited	stock	NSE	INR	1420.75000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	8.10	2.10	0.780	IT Services
267c1bef-3fea-4e08-8990-4224623ee0f2	WIPRO	Wipro Limited	stock	NSE	INR	385.20000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	3.20	1.50	0.820	IT Services
6d063bf2-ad7d-4ae2-b07f-b10281988d96	HCLTECH	HCL Technologies	stock	NSE	INR	1485.60000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	6.80	1.90	0.900	IT Services
7e4f8c1c-c668-4302-8e02-4df58e5cc125	HDFCBANK	HDFC Bank Limited	stock	NSE	INR	1545.60000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	2.80	1.20	0.950	Private Sector Bank
f6012ffb-c893-4fb2-907a-9d941cd97112	ICICIBANK	ICICI Bank Limited	stock	NSE	INR	1085.40000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	2.10	0.80	1.120	Private Sector Bank
b6cdd3bc-3824-4ab2-b202-0fb6c0bf7c87	KOTAKBANK	Kotak Mahindra Bank	stock	NSE	INR	1720.90000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	2.50	0.60	1.050	Private Sector Bank
5523a504-c0c2-405e-8688-95e00764abb0	BAJFINANCE	Bajaj Finance Limited	stock	NSE	INR	6850.75000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	4.80	0.40	1.250	NBFC
b714aad3-8b6d-4d89-af32-444f6bbb4307	HINDUNILVR	Hindustan Unilever Ltd	stock	NSE	INR	2385.45000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	12.50	1.40	0.450	Personal Care
891fac00-ba67-4315-ac23-c505623255ca	NESTLEIND	Nestle India Limited	stock	NSE	INR	2195.80000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	15.80	0.80	0.350	Food Products
0b450c70-7cf5-4593-88d1-2fe3afff9d7e	ITC	ITC Limited	stock	NSE	INR	405.65000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	4.20	4.50	0.650	Tobacco & Cigarettes
06d42b04-7e91-4ea9-8d06-9cd1cf324a0d	RELIANCE	Reliance Industries Ltd	stock	NSE	INR	2685.90000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	1.50	0.50	1.150	Refineries
871013ec-5772-46c2-8df1-d6c25274d3f1	ONGC	Oil & Natural Gas Corp	stock	NSE	INR	285.75000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	0.80	5.20	1.450	Oil Exploration
89487d06-a9c7-42f0-8377-8e8727b82dfc	NTPC	NTPC Limited	stock	NSE	INR	385.20000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	1.20	3.80	0.850	Power Generation
030fa051-02f1-40eb-8b07-ab0f8dd6faac	SUNPHARMA	Sun Pharmaceutical Inds	stock	NSE	INR	1650.75000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	6.20	0.60	0.750	Pharmaceuticals
903a5ef0-b620-414e-b322-255aa87b620d	DRREDDY	Dr Reddys Laboratories	stock	NSE	INR	1285.40000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	2.80	0.80	0.820	Pharmaceuticals
b8e3f4ce-ace5-4167-a038-07c0e694602d	CIPLA	Cipla Limited	stock	NSE	INR	1420.85000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	4.10	1.20	0.680	Pharmaceuticals
e7c70d9f-b60f-448f-82a0-c263129c4087	MARUTI	Maruti Suzuki India Ltd	stock	NSE	INR	10850.75000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	3.80	1.80	1.220	Passenger Cars
6b24bfbe-2644-420d-bf06-634aed67aa63	TATAMOTORS	Tata Motors Limited	stock	NSE	INR	785.60000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	2.10	0.00	1.850	Commercial Vehicles
1eeb5c5d-63a6-43d1-8d92-69e3f3ce46e1	M&M	Mahindra & Mahindra	stock	NSE	INR	1485.90000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	2.80	1.20	1.350	Passenger Cars
8f1b513f-cf5c-47a0-94d4-272d8e038882	LT	Larsen & Toubro Ltd	stock	NSE	INR	3485.75000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	4.20	0.80	1.150	Construction & Engineering
9d296262-8ece-4ff7-b391-1ae25f2e29c7	ULTRACEMCO	UltraTech Cement Ltd	stock	NSE	INR	10850.60000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	6.80	0.60	1.250	Cement
db00cf7e-a44c-4053-b76d-02a849bc3e7a	TATASTEEL	Tata Steel Limited	stock	NSE	INR	118.45000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	0.80	8.50	1.680	Steel
26a5c553-08fe-4409-bf39-ffef84e44ae8	BHARTIARTL	Bharti Airtel Limited	stock	NSE	INR	1485.20000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	8.20	0.40	0.950	Telecom Services
5cb4cd0d-fe47-4f25-82b3-850ee9386c42	HINDALCO	Hindalco Industries Ltd	stock	NSE	INR	485.70000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	1.80	2.50	1.450	Aluminium
6e7df10a-1c51-4be8-8745-b3d071847078	JSWSTEEL	JSW Steel Limited	stock	NSE	INR	785.30000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	1.50	3.20	1.550	Steel
38419b31-c982-4f69-be82-2e91d3aa81c0	VEDL	Vedanta Limited	stock	NSE	INR	485.25000000	\N	t	\N	2025-09-07 17:43:11.103797+00	2025-09-07 17:52:58.505674+00	1.20	18.50	1.850	Diversified Metals & Mining
\.


--
-- Data for Name: portfolio_holdings; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.portfolio_holdings (id, portfolio_id, asset_id, quantity, average_cost, total_cost, current_value, unrealized_pnl, realized_pnl, last_updated, created_at) FROM stdin;
\.


--
-- Data for Name: portfolios; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.portfolios (id, user_id, name, description, total_value, cash_balance, currency, is_default, created_at, updated_at) FROM stdin;
fe5891a9-a689-4e5e-b0c6-c47f903f118a	7188ff89-351b-41fe-8ac4-65c0a67ea5ac	Admin's Portfolio	Default portfolio for admin	100000.00	100000.00	USD	t	2025-09-06 18:47:37.526809+00	2025-09-06 18:47:37.526809+00
9c2ed553-1a87-43ff-bcb9-876c77ee82ec	b4d57aec-44ee-42c2-a823-739087343bd1	Johndoe's Portfolio	Default portfolio for johndoe	10000.00	10000.00	USD	t	2025-09-06 18:47:37.528854+00	2025-09-06 18:47:37.528854+00
11e07981-5a92-404f-8c96-62e44e35c48d	2a281d12-b9ed-413c-b3bf-f8b939b3cd9c	Janesmith's Portfolio	Default portfolio for janesmith	10000.00	10000.00	USD	t	2025-09-06 18:47:37.529487+00	2025-09-06 18:47:37.529487+00
8e9b49ea-a157-4409-87fb-a1fd33da408e	c0193a1a-2f52-409e-aac1-e795fe20ccae	Alicejohnson's Portfolio	Default portfolio for alicejohnson	10000.00	10000.00	USD	t	2025-09-06 18:47:37.529927+00	2025-09-06 18:47:37.529927+00
4f51c953-cf76-4f71-b70a-c3e74e8cc898	657b186b-551b-4ca5-b1d9-e79ae19875b8	Bobwilson's Portfolio	Default portfolio for bobwilson	10000.00	10000.00	USD	t	2025-09-06 18:47:37.530531+00	2025-09-06 18:47:37.530531+00
87654321-4321-4321-4321-210987654321	12345678-1234-1234-1234-123456789012	Demo Portfolio	\N	0.00	10000.00	USD	t	2025-09-06 18:49:28.152611+00	2025-09-06 18:49:28.152611+00
\.


--
-- Data for Name: price_history; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.price_history (id, asset_id, price, volume, market_cap, "timestamp", interval_type, created_at) FROM stdin;
\.


--
-- Data for Name: smallcase_constituents; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.smallcase_constituents (id, smallcase_id, asset_id, weight_percentage, is_active, created_at, updated_at, rationale) FROM stdin;
c555d908-09e6-4ddb-9695-9530f94296ea	4ab327eb-2773-490a-bc16-7116b79dbccf	8f1b513f-cf5c-47a0-94d4-272d8e038882	13.00	t	2025-09-07 17:52:58.508123+00	2025-09-07 17:52:58.508123+00	\N
c3908b78-8c0b-42c4-bc0f-7bf354cf31cc	4ab327eb-2773-490a-bc16-7116b79dbccf	89487d06-a9c7-42f0-8377-8e8727b82dfc	12.00	t	2025-09-07 17:52:58.508123+00	2025-09-07 17:52:58.508123+00	\N
a1004163-1a59-4c82-a97b-70b450b2ecd8	4ab327eb-2773-490a-bc16-7116b79dbccf	871013ec-5772-46c2-8df1-d6c25274d3f1	15.00	t	2025-09-07 17:52:58.508123+00	2025-09-07 17:52:58.508123+00	\N
37458073-2c2d-42c4-be8e-c7f27cc9ba49	4ab327eb-2773-490a-bc16-7116b79dbccf	06d42b04-7e91-4ea9-8d06-9cd1cf324a0d	25.00	t	2025-09-07 17:52:58.508123+00	2025-09-07 17:52:58.508123+00	\N
e750c3e2-8a24-4b58-8942-aad0be9f06bb	4ab327eb-2773-490a-bc16-7116b79dbccf	0b450c70-7cf5-4593-88d1-2fe3afff9d7e	15.00	t	2025-09-07 17:52:58.508123+00	2025-09-07 17:52:58.508123+00	\N
c7c7aa08-7a7f-4d79-8ff6-97e593214329	4ab327eb-2773-490a-bc16-7116b79dbccf	7e4f8c1c-c668-4302-8e02-4df58e5cc125	20.00	t	2025-09-07 17:52:58.508123+00	2025-09-07 17:52:58.508123+00	\N
ec8f8df5-85cf-4c04-9529-9fcc7b66d9a4	e18d2989-3572-4354-979e-1df926c06e09	5523a504-c0c2-405e-8688-95e00764abb0	25.00	t	2025-09-07 17:52:58.50967+00	2025-09-07 17:52:58.50967+00	\N
4dabf5fe-0f68-42b5-8d0c-b4859c75ade7	e18d2989-3572-4354-979e-1df926c06e09	b6cdd3bc-3824-4ab2-b202-0fb6c0bf7c87	20.00	t	2025-09-07 17:52:58.50967+00	2025-09-07 17:52:58.50967+00	\N
888ca7c1-1139-4ab7-99b0-e8e7e2eb30a8	e18d2989-3572-4354-979e-1df926c06e09	f6012ffb-c893-4fb2-907a-9d941cd97112	25.00	t	2025-09-07 17:52:58.50967+00	2025-09-07 17:52:58.50967+00	\N
6cdfaf67-4683-42c5-9202-415bff977e76	e18d2989-3572-4354-979e-1df926c06e09	7e4f8c1c-c668-4302-8e02-4df58e5cc125	30.00	t	2025-09-07 17:52:58.50967+00	2025-09-07 17:52:58.50967+00	\N
77d81fbe-a1e7-4343-b29e-8468529124e5	778a8a81-256f-4b01-8c5e-043a8d7bd399	6d063bf2-ad7d-4ae2-b07f-b10281988d96	15.00	t	2025-09-07 17:52:58.510147+00	2025-09-07 17:52:58.510147+00	\N
a3dbe3d2-6ef5-47e1-b80a-f58dc480bf28	778a8a81-256f-4b01-8c5e-043a8d7bd399	267c1bef-3fea-4e08-8990-4224623ee0f2	20.00	t	2025-09-07 17:52:58.510147+00	2025-09-07 17:52:58.510147+00	\N
e397a757-dd3d-4f74-b1f2-6384cbc5862f	778a8a81-256f-4b01-8c5e-043a8d7bd399	b76ecdf2-bb85-47c2-8f83-18366735edd1	30.00	t	2025-09-07 17:52:58.510147+00	2025-09-07 17:52:58.510147+00	\N
7490c00f-c7b4-46b9-b593-da5a0c0f9237	778a8a81-256f-4b01-8c5e-043a8d7bd399	e23922f7-94ce-4d18-a549-05a5790e25a7	35.00	t	2025-09-07 17:52:58.510147+00	2025-09-07 17:52:58.510147+00	\N
b42791b0-1c6c-4635-925b-5219b02b3d3e	f063cb17-8cd6-4bbf-b328-ef69b3c9c382	9d296262-8ece-4ff7-b391-1ae25f2e29c7	13.00	t	2025-09-07 17:52:58.510525+00	2025-09-07 17:52:58.510525+00	\N
752680fd-080d-4fe0-9789-5ce6681eb636	f063cb17-8cd6-4bbf-b328-ef69b3c9c382	e7c70d9f-b60f-448f-82a0-c263129c4087	12.00	t	2025-09-07 17:52:58.510525+00	2025-09-07 17:52:58.510525+00	\N
392c3e0b-6e84-40ab-bfbf-49f92221d155	f063cb17-8cd6-4bbf-b328-ef69b3c9c382	5523a504-c0c2-405e-8688-95e00764abb0	20.00	t	2025-09-07 17:52:58.510525+00	2025-09-07 17:52:58.510525+00	\N
5f222a66-d885-48c0-a516-641143a21f41	f063cb17-8cd6-4bbf-b328-ef69b3c9c382	6d063bf2-ad7d-4ae2-b07f-b10281988d96	15.00	t	2025-09-07 17:52:58.510525+00	2025-09-07 17:52:58.510525+00	\N
c8513932-a41d-4b9c-a9ec-0e005a3499d7	f063cb17-8cd6-4bbf-b328-ef69b3c9c382	b76ecdf2-bb85-47c2-8f83-18366735edd1	18.00	t	2025-09-07 17:52:58.510525+00	2025-09-07 17:52:58.510525+00	\N
a77ad75a-2ab2-42da-8a30-3969fba91aa9	f063cb17-8cd6-4bbf-b328-ef69b3c9c382	e23922f7-94ce-4d18-a549-05a5790e25a7	22.00	t	2025-09-07 17:52:58.510525+00	2025-09-07 17:52:58.510525+00	\N
826969a2-1784-44c5-ab6e-8d3c04ace301	c3dac2c7-9ee7-4874-8e39-c5bca3f9fc9c	6e7df10a-1c51-4be8-8745-b3d071847078	10.00	t	2025-09-07 17:52:58.511039+00	2025-09-07 17:52:58.511039+00	\N
a4739a81-ce2e-4293-9af8-a2f1851356b9	c3dac2c7-9ee7-4874-8e39-c5bca3f9fc9c	5cb4cd0d-fe47-4f25-82b3-850ee9386c42	15.00	t	2025-09-07 17:52:58.511039+00	2025-09-07 17:52:58.511039+00	\N
d012a856-5429-463a-8f13-f0e94828e5ba	c3dac2c7-9ee7-4874-8e39-c5bca3f9fc9c	db00cf7e-a44c-4053-b76d-02a849bc3e7a	20.00	t	2025-09-07 17:52:58.511039+00	2025-09-07 17:52:58.511039+00	\N
d02a98a8-9d3f-47d2-8f28-955d4450442f	c3dac2c7-9ee7-4874-8e39-c5bca3f9fc9c	9d296262-8ece-4ff7-b391-1ae25f2e29c7	25.00	t	2025-09-07 17:52:58.511039+00	2025-09-07 17:52:58.511039+00	\N
9cffb26b-f7f8-48c0-bc22-bb2ec6644af9	c3dac2c7-9ee7-4874-8e39-c5bca3f9fc9c	8f1b513f-cf5c-47a0-94d4-272d8e038882	30.00	t	2025-09-07 17:52:58.511039+00	2025-09-07 17:52:58.511039+00	\N
16aeb7bf-58ce-4d20-96b4-dac5883cb4c6	5c01b087-92bc-471c-aef1-abf49bc320c2	0b450c70-7cf5-4593-88d1-2fe3afff9d7e	30.00	t	2025-09-07 17:52:58.51165+00	2025-09-07 17:52:58.51165+00	\N
0d591e3e-4996-4333-85be-971d9934ddb8	5c01b087-92bc-471c-aef1-abf49bc320c2	891fac00-ba67-4315-ac23-c505623255ca	30.00	t	2025-09-07 17:52:58.51165+00	2025-09-07 17:52:58.51165+00	\N
b4ca00ad-2ed8-4dc4-a9d9-6bcb81d16a4c	5c01b087-92bc-471c-aef1-abf49bc320c2	b714aad3-8b6d-4d89-af32-444f6bbb4307	40.00	t	2025-09-07 17:52:58.51165+00	2025-09-07 17:52:58.51165+00	\N
3ff5febe-bb31-4336-85fe-32aa606b1472	fa41891a-b484-49ff-823e-58f1b958972f	89487d06-a9c7-42f0-8377-8e8727b82dfc	35.00	t	2025-09-07 17:52:58.512074+00	2025-09-07 17:52:58.512074+00	\N
63955a7c-c74d-4345-9df1-8e2aa7cb64c8	fa41891a-b484-49ff-823e-58f1b958972f	871013ec-5772-46c2-8df1-d6c25274d3f1	25.00	t	2025-09-07 17:52:58.512074+00	2025-09-07 17:52:58.512074+00	\N
0c401a77-28f0-44dd-baed-5b2a70f38b2a	fa41891a-b484-49ff-823e-58f1b958972f	06d42b04-7e91-4ea9-8d06-9cd1cf324a0d	40.00	t	2025-09-07 17:52:58.512074+00	2025-09-07 17:52:58.512074+00	\N
26539fa6-36e3-4dc5-b7d4-636b310e8f29	57131e70-8da0-4abe-8897-2689487acc2e	38419b31-c982-4f69-be82-2e91d3aa81c0	20.00	t	2025-09-07 17:52:58.512481+00	2025-09-07 17:52:58.512481+00	\N
69c260c6-4436-46a8-80fa-6f4db60a7553	57131e70-8da0-4abe-8897-2689487acc2e	6e7df10a-1c51-4be8-8745-b3d071847078	15.00	t	2025-09-07 17:52:58.512481+00	2025-09-07 17:52:58.512481+00	\N
a2ba14e0-ae2d-4f14-bdf7-969f927f7261	57131e70-8da0-4abe-8897-2689487acc2e	5cb4cd0d-fe47-4f25-82b3-850ee9386c42	10.00	t	2025-09-07 17:52:58.512481+00	2025-09-07 17:52:58.512481+00	\N
052849af-3e88-41a4-9e48-91374ef49a0a	57131e70-8da0-4abe-8897-2689487acc2e	1eeb5c5d-63a6-43d1-8d92-69e3f3ce46e1	10.00	t	2025-09-07 17:52:58.512481+00	2025-09-07 17:52:58.512481+00	\N
8dbf4dd5-33c5-4246-9fca-30559efa42b0	57131e70-8da0-4abe-8897-2689487acc2e	6b24bfbe-2644-420d-bf06-634aed67aa63	25.00	t	2025-09-07 17:52:58.512481+00	2025-09-07 17:52:58.512481+00	\N
b907a560-030e-4069-b99d-a72e402f6c5f	57131e70-8da0-4abe-8897-2689487acc2e	5523a504-c0c2-405e-8688-95e00764abb0	20.00	t	2025-09-07 17:52:58.512481+00	2025-09-07 17:52:58.512481+00	\N
e094bf3a-3721-48a0-885c-d47971a38527	87c41281-8ae1-4a4e-a361-e437e5a07f61	26a5c553-08fe-4409-bf39-ffef84e44ae8	6.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
d968be18-861c-40ad-b3cd-520c5727529b	87c41281-8ae1-4a4e-a361-e437e5a07f61	8f1b513f-cf5c-47a0-94d4-272d8e038882	8.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
285954ad-152e-4911-9b20-ea4c7b60d575	87c41281-8ae1-4a4e-a361-e437e5a07f61	e7c70d9f-b60f-448f-82a0-c263129c4087	7.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
d0e7d200-d098-49b8-a58f-87deb31dc612	87c41281-8ae1-4a4e-a361-e437e5a07f61	030fa051-02f1-40eb-8b07-ab0f8dd6faac	8.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
2d7f6cb9-47e8-4204-9b35-b47ac80eaf33	87c41281-8ae1-4a4e-a361-e437e5a07f61	89487d06-a9c7-42f0-8377-8e8727b82dfc	6.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
e962ea25-b886-4675-9d37-5c560c9fea67	87c41281-8ae1-4a4e-a361-e437e5a07f61	06d42b04-7e91-4ea9-8d06-9cd1cf324a0d	13.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
1ba5c665-17c7-4b42-8632-9f79c48a649a	87c41281-8ae1-4a4e-a361-e437e5a07f61	0b450c70-7cf5-4593-88d1-2fe3afff9d7e	7.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
e12c4519-4164-4b73-b4f1-b29b719657c8	87c41281-8ae1-4a4e-a361-e437e5a07f61	b714aad3-8b6d-4d89-af32-444f6bbb4307	10.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
556c1e5b-609d-4a0b-90fa-c7527c55767e	87c41281-8ae1-4a4e-a361-e437e5a07f61	f6012ffb-c893-4fb2-907a-9d941cd97112	8.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
35a05ad1-eb67-4ec4-aee8-e8d63ea203c6	87c41281-8ae1-4a4e-a361-e437e5a07f61	7e4f8c1c-c668-4302-8e02-4df58e5cc125	15.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
44534933-0c35-42d6-bf3a-f3348252fecc	87c41281-8ae1-4a4e-a361-e437e5a07f61	e23922f7-94ce-4d18-a549-05a5790e25a7	12.00	t	2025-09-07 17:52:58.512889+00	2025-09-07 17:52:58.512889+00	\N
00c5da2f-cb8d-4954-95c5-1c99b1b42382	33743cae-fe1e-4800-bde3-a8ee599e7b2c	38419b31-c982-4f69-be82-2e91d3aa81c0	12.00	t	2025-09-07 17:52:58.51343+00	2025-09-07 17:52:58.51343+00	\N
717fa432-e37b-4abf-a4db-e6ebd256416e	33743cae-fe1e-4800-bde3-a8ee599e7b2c	db00cf7e-a44c-4053-b76d-02a849bc3e7a	10.00	t	2025-09-07 17:52:58.51343+00	2025-09-07 17:52:58.51343+00	\N
b1a7e440-1b9d-4516-ba65-e27afa52bef2	33743cae-fe1e-4800-bde3-a8ee599e7b2c	89487d06-a9c7-42f0-8377-8e8727b82dfc	18.00	t	2025-09-07 17:52:58.51343+00	2025-09-07 17:52:58.51343+00	\N
f3f2ab0a-974e-4060-8142-a00dee1dc3f8	33743cae-fe1e-4800-bde3-a8ee599e7b2c	871013ec-5772-46c2-8df1-d6c25274d3f1	20.00	t	2025-09-07 17:52:58.51343+00	2025-09-07 17:52:58.51343+00	\N
97597819-251c-4ba0-b282-7e79f6480166	33743cae-fe1e-4800-bde3-a8ee599e7b2c	0b450c70-7cf5-4593-88d1-2fe3afff9d7e	25.00	t	2025-09-07 17:52:58.51343+00	2025-09-07 17:52:58.51343+00	\N
94067c89-d3f9-4938-bfbe-56865a3db2c3	33743cae-fe1e-4800-bde3-a8ee599e7b2c	b714aad3-8b6d-4d89-af32-444f6bbb4307	15.00	t	2025-09-07 17:52:58.51343+00	2025-09-07 17:52:58.51343+00	\N
\.


--
-- Data for Name: smallcase_performance; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.smallcase_performance (id, smallcase_id, date, nav, total_return_1d, total_return_1w, total_return_1m, total_return_3m, total_return_6m, total_return_1y, total_return_3y, benchmark_return_1d, benchmark_return_1y, alpha, created_at) FROM stdin;
\.


--
-- Data for Name: smallcases; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.smallcases (id, name, description, category, theme, risk_level, expected_return_min, expected_return_max, minimum_investment, is_active, created_by, created_at, updated_at, strategy_type, expected_return_1y, expected_return_3y, expected_return_5y, volatility, sharpe_ratio, max_drawdown, expense_ratio) FROM stdin;
4ab327eb-2773-490a-bc16-7116b79dbccf	Large Cap Value Fund	Fundamentally strong large-cap companies trading at attractive valuations with focus on dividend yield.	Equity	Value Investing	low	10.00	15.00	100000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	VALUE	12.00	14.00	15.00	15.50	0.850	-12.00	0.750
f063cb17-8cd6-4bbf-b328-ef69b3c9c382	Growth Momentum Portfolio	High-growth companies with strong earnings momentum in technology and financial services.	Equity	Growth & Momentum	high	15.00	25.00	250000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	GROWTH	18.00	22.00	20.00	22.50	0.920	-18.00	1.250
e18d2989-3572-4354-979e-1df926c06e09	Banking & NBFC Focus	Concentrated exposure to banking and financial services sector.	Financial Services	Banking Sector	medium	12.00	20.00	200000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	SECTORAL	15.00	18.00	16.00	20.00	0.880	-15.00	0.950
778a8a81-256f-4b01-8c5e-043a8d7bd399	IT Export Leaders	Technology services companies with strong global presence.	Information Technology	IT Services	medium	14.00	22.00	175000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	SECTORAL	16.00	19.00	18.00	18.50	0.950	-14.00	0.850
c3dac2c7-9ee7-4874-8e39-c5bca3f9fc9c	Infrastructure & Capex Theme	Companies benefiting from India infrastructure development.	Infrastructure	Nation Building	high	16.00	28.00	300000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	SECTORAL	20.00	25.00	22.00	25.00	0.850	-22.00	1.150
5c01b087-92bc-471c-aef1-abf49bc320c2	Consumer Staples Portfolio	Recession-proof FMCG companies with strong brand moats.	Consumer Staples	Daily Essentials	low	8.00	16.00	125000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	DEFENSIVE	11.00	13.00	14.00	14.00	0.820	-10.00	0.700
fa41891a-b484-49ff-823e-58f1b958972f	Energy & Power Utilities	Diversified exposure to energy value chain.	Energy	Energy Security	medium	12.00	18.00	180000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	SECTORAL	14.00	16.00	15.00	19.00	0.750	-16.00	0.900
57131e70-8da0-4abe-8897-2689487acc2e	High Beta Momentum Strategy	High beta stocks for aggressive investors.	High Beta	Volatility Play	high	18.00	35.00	500000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	MOMENTUM	25.00	30.00	28.00	35.00	0.780	-30.00	1.500
87c41281-8ae1-4a4e-a361-e437e5a07f61	All Weather Balanced	Diversified portfolio across sectors for all market conditions.	Balanced	All Weather	medium	10.00	18.00	100000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	VALUE	13.00	15.00	16.00	16.00	0.900	-12.00	0.800
33743cae-fe1e-4800-bde3-a8ee599e7b2c	Defensive Dividend Strategy	High dividend-yielding stocks from stable sectors.	Dividend	Income Generation	low	8.00	14.00	150000.00	t	\N	2025-09-07 17:52:58.507018+00	2025-09-07 17:52:58.507018+00	DEFENSIVE	10.00	12.00	13.00	12.00	0.780	-8.00	0.650
\.


--
-- Data for Name: trading_transactions; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.trading_transactions (id, user_id, portfolio_id, asset_id, transaction_type, quantity, price_per_unit, total_amount, fees, net_amount, transaction_date, settlement_date, status, order_type, notes, external_transaction_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.user_sessions (id, user_id, session_token, expires_at, created_at, ip_address, user_agent) FROM stdin;
\.


--
-- Data for Name: user_smallcase_investments; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.user_smallcase_investments (id, user_id, portfolio_id, smallcase_id, investment_amount, units_purchased, purchase_price, current_value, unrealized_pnl, status, invested_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: trading_user
--

COPY public.users (id, email, username, password_hash, first_name, last_name, phone, date_of_birth, profile_image_url, email_verified, phone_verified, kyc_status, account_status, created_at, updated_at, last_login) FROM stdin;
7188ff89-351b-41fe-8ac4-65c0a67ea5ac	admin@saras-trading.com	admin	$2b$12$esVSyQEVl/ZqbLcLlDF0Ke46RvmJaFJCR53ckRf68hoX8ySGad2Nm	Admin	User	\N	\N	\N	t	f	approved	active	2025-09-06 18:47:36.813612+00	2025-09-06 18:47:36.813612+00	\N
b4d57aec-44ee-42c2-a823-739087343bd1	john.doe@example.com	johndoe	$2b$12$MCVePuVdLuUPJtUt6c0wU.nLP0pkDkvc2qSO0TvqgyAH49vkYLHba	John	Doe	\N	\N	\N	t	f	approved	active	2025-09-06 18:47:36.995744+00	2025-09-06 18:47:36.995744+00	\N
2a281d12-b9ed-413c-b3bf-f8b939b3cd9c	jane.smith@example.com	janesmith	$2b$12$jOcUzfldl8TdNz.nUgSwQedZ.kI0tFHhHSab/P1rt5P/QZvCMaXVm	Jane	Smith	\N	\N	\N	t	f	approved	active	2025-09-06 18:47:37.170141+00	2025-09-06 18:47:37.170141+00	\N
c0193a1a-2f52-409e-aac1-e795fe20ccae	alice.johnson@example.com	alicejohnson	$2b$12$d3Ht0OUX2.zPP0dnSNOlCOmywFq84k6uidKzeuB2u6yZRQSZ3r13G	Alice	Johnson	\N	\N	\N	t	f	pending	active	2025-09-06 18:47:37.340474+00	2025-09-06 18:47:37.340474+00	\N
657b186b-551b-4ca5-b1d9-e79ae19875b8	bob.wilson@example.com	bobwilson	$2b$12$.GWycp0uRE6EjtB84KM7EeEhk3HlWBbRIW.L0IbF58l/DEanTFJOy	Bob	Wilson	\N	\N	\N	t	f	approved	active	2025-09-06 18:47:37.511704+00	2025-09-06 18:47:37.511704+00	\N
12345678-1234-1234-1234-123456789012	demo@saras.trading	demo_user	$2b$10$dummy.hash.for.demo	Demo	User	\N	\N	\N	f	f	pending	active	2025-09-06 18:49:28.152611+00	2025-09-06 18:49:28.152611+00	\N
\.


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: assets assets_symbol_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_symbol_key UNIQUE (symbol);


--
-- Name: portfolio_holdings portfolio_holdings_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_pkey PRIMARY KEY (id);


--
-- Name: portfolio_holdings portfolio_holdings_portfolio_id_asset_id_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_portfolio_id_asset_id_key UNIQUE (portfolio_id, asset_id);


--
-- Name: portfolios portfolios_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_pkey PRIMARY KEY (id);


--
-- Name: price_history price_history_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_pkey PRIMARY KEY (id);


--
-- Name: smallcase_constituents smallcase_constituents_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_pkey PRIMARY KEY (id);


--
-- Name: smallcase_constituents smallcase_constituents_smallcase_id_asset_id_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_smallcase_id_asset_id_key UNIQUE (smallcase_id, asset_id);


--
-- Name: smallcase_performance smallcase_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_performance
    ADD CONSTRAINT smallcase_performance_pkey PRIMARY KEY (id);


--
-- Name: smallcase_performance smallcase_performance_smallcase_id_date_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_performance
    ADD CONSTRAINT smallcase_performance_smallcase_id_date_key UNIQUE (smallcase_id, date);


--
-- Name: smallcases smallcases_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcases
    ADD CONSTRAINT smallcases_pkey PRIMARY KEY (id);


--
-- Name: trading_transactions trading_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_session_token_key UNIQUE (session_token);


--
-- Name: user_smallcase_investments user_smallcase_investments_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_assets_symbol; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_assets_symbol ON public.assets USING btree (symbol);


--
-- Name: idx_assets_type; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_assets_type ON public.assets USING btree (asset_type);


--
-- Name: idx_constituents_weight; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_constituents_weight ON public.smallcase_constituents USING btree (weight_percentage);


--
-- Name: idx_performance_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_performance_date ON public.smallcase_performance USING btree (date);


--
-- Name: idx_portfolio_holdings_asset_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_portfolio_holdings_asset_id ON public.portfolio_holdings USING btree (asset_id);


--
-- Name: idx_portfolio_holdings_portfolio_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_portfolio_holdings_portfolio_id ON public.portfolio_holdings USING btree (portfolio_id);


--
-- Name: idx_portfolios_user_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_portfolios_user_id ON public.portfolios USING btree (user_id);


--
-- Name: idx_price_history_asset_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_price_history_asset_id ON public.price_history USING btree (asset_id);


--
-- Name: idx_price_history_timestamp; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_price_history_timestamp ON public.price_history USING btree ("timestamp");


--
-- Name: idx_smallcases_risk_level; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_smallcases_risk_level ON public.smallcases USING btree (risk_level);


--
-- Name: idx_trading_transactions_asset_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trading_transactions_asset_id ON public.trading_transactions USING btree (asset_id);


--
-- Name: idx_trading_transactions_date; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trading_transactions_date ON public.trading_transactions USING btree (transaction_date);


--
-- Name: idx_trading_transactions_portfolio_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trading_transactions_portfolio_id ON public.trading_transactions USING btree (portfolio_id);


--
-- Name: idx_trading_transactions_status; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trading_transactions_status ON public.trading_transactions USING btree (status);


--
-- Name: idx_trading_transactions_user_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_trading_transactions_user_id ON public.trading_transactions USING btree (user_id);


--
-- Name: idx_user_sessions_token; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_user_sessions_token ON public.user_sessions USING btree (session_token);


--
-- Name: idx_user_sessions_user_id; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_user_sessions_user_id ON public.user_sessions USING btree (user_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: trading_user
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: assets update_assets_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON public.assets FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: portfolios update_portfolios_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON public.portfolios FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: smallcase_constituents update_smallcase_constituents_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_smallcase_constituents_updated_at BEFORE UPDATE ON public.smallcase_constituents FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: smallcases update_smallcases_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_smallcases_updated_at BEFORE UPDATE ON public.smallcases FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: trading_transactions update_trading_transactions_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_trading_transactions_updated_at BEFORE UPDATE ON public.trading_transactions FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_smallcase_investments update_user_smallcase_investments_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_user_smallcase_investments_updated_at BEFORE UPDATE ON public.user_smallcase_investments FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: trading_user
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: portfolio_holdings portfolio_holdings_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: portfolio_holdings portfolio_holdings_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.portfolio_holdings
    ADD CONSTRAINT portfolio_holdings_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


--
-- Name: portfolios portfolios_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.portfolios
    ADD CONSTRAINT portfolios_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: price_history price_history_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.price_history
    ADD CONSTRAINT price_history_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: smallcase_constituents smallcase_constituents_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: smallcase_constituents smallcase_constituents_smallcase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_constituents
    ADD CONSTRAINT smallcase_constituents_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id) ON DELETE CASCADE;


--
-- Name: smallcase_performance smallcase_performance_smallcase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcase_performance
    ADD CONSTRAINT smallcase_performance_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id);


--
-- Name: smallcases smallcases_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.smallcases
    ADD CONSTRAINT smallcases_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: trading_transactions trading_transactions_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_asset_id_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id);


--
-- Name: trading_transactions trading_transactions_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


--
-- Name: trading_transactions trading_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.trading_transactions
    ADD CONSTRAINT trading_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_smallcase_investments user_smallcase_investments_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolios(id) ON DELETE CASCADE;


--
-- Name: user_smallcase_investments user_smallcase_investments_smallcase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_smallcase_id_fkey FOREIGN KEY (smallcase_id) REFERENCES public.smallcases(id) ON DELETE CASCADE;


--
-- Name: user_smallcase_investments user_smallcase_investments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trading_user
--

ALTER TABLE ONLY public.user_smallcase_investments
    ADD CONSTRAINT user_smallcase_investments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

