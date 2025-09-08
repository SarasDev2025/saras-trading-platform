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

